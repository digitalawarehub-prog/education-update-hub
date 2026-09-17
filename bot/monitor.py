import logging,os,sys,inspect,json,re
from datetime import datetime,date
from pathlib import Path
from sources_manager import SourceManager
from scraper import scrape_all_sources
from parser import parse_jobs
from optimizer import run_optimizer
from database import load_jobs,save_jobs
from html_generator import generate_all,clean_output_directory
import homepage,category_generator
from sitemap_generator import update_sitemap
logging.basicConfig(level=logging.INFO,format='%(asctime)s | %(levelname)s | %(message)s'); log=logging.getLogger('EUH_FINAL')
MAX_AI=int(os.getenv('MAX_AI_POSTS_PER_RUN','5')); MAX_ATTEMPTS=int(os.getenv('MAX_AI_ATTEMPTS','18')); ROOT=Path(__file__).resolve().parent.parent; ARCH=ROOT/'database'/'archive.json'
def norm(x): return (x[0] or [],x[1] or []) if isinstance(x,tuple) else (x or [],[])
def scrape_compat(s):
 p=inspect.signature(scrape_all_sources).parameters
 # More concurrency shortens the long pre-AI scrape stage.
 if 'workers' in p:return scrape_all_sources(s,workers=20)
 if 'max_workers' in p:return scrape_all_sources(s,max_workers=20)
 return scrape_all_sources(s)
def key(j):return str(j.get('job_id') or j.get('url') or j.get('title') or '').strip().casefold()
def unique(a):
 o=[];seen=set()
 for j in a or []:
  k=key(j)
  if k and k not in seen:seen.add(k);o.append(j)
 return o
def pdate(v):
 s=str(v or '').strip(); m=re.search(r'^(\d{2})-(\d{2})-(20\d{2})$',s)
 if m:return date(int(m.group(3)),int(m.group(2)),int(m.group(1)))
 m=re.search(r'^(20\d{2})-(\d{2})-(\d{2})',s)
 if m:return date(int(m.group(1)),int(m.group(2)),int(m.group(3)))
 return None
def deadline(j):
 for k in ('last_date','deadline','application_last_date','last_date_to_apply','closing_date','application_deadline'):
  d=pdate(j.get(k))
  if d:return d
 return None
def status(j):
 d=deadline(j); return ('Application Closed',True) if d and d<date.today() else ('Active',False)

def ai_candidate(j):
 t=str(j.get('title') or '').strip().casefold(); body=str(j.get('content') or j.get('description') or '').strip().casefold()
 if len(t)<12:return False
 years=[int(x) for x in re.findall(r'\b20\d{2}\b',t)]
 if years and max(years)<date.today().year-1:return False
 blocked=(
  'selected','qualified','wait list','waiting list','merit list','shortlisted','previous year','question paper',
  'answer key','admit card','hall ticket','result','score card','individual score','exam schedule','examination schedule',
  'interview schedule','corrigendum','extension','date extended','revised schedule','syllabus','cut off','cut-off',
  'caveat','certificate','declaration','press release','cancelled','stands cancelled','promotion','seniority list'
 )
 if any(x in t for x in blocked):return False
 # Notices that merely report an update are not fresh recruitment opportunities.
 if re.search(r'\b(notification|notice|update|updated|advertisement)\b',t) and not re.search(r'\b(recruitment|vacanc|application|engagement|appointment|walk[- ]?in)\b',t):
  return False
 good=('recruitment','vacancy','vacancies','applications are invited','application invited','apply online','online application','engagement of','appointment of','walk-in','walk in','भर्ती','रिक्ति','आवेदन आमंत्रित','ऑनलाइन आवेदन','नियुक्ति','संविदा','guest lecturer','contractual')
 evidence=t+' '+body
 return any(x in evidence for x in good)
def candidate_score(j):
 t=str(j.get('title') or '').casefold(); body=str(j.get('content') or j.get('description') or '')
 score=0
 for x in ('recruitment','applications are invited','apply online','online application','vacancy','engagement of','appointment of','भर्ती','रिक्ति','आवेदन'): score += 4 if x in t else 2 if x in body.casefold() else 0
 if j.get('notification_pdf'):score+=3
 if j.get('apply_link'):score+=3
 if len(body)>=500:score+=3
 if deadline(j):score+=4
 return score
def load_arch():
 try:return json.loads(ARCH.read_text(encoding='utf8')) if ARCH.exists() else []
 except:return []
def save_arch(a):
 ARCH.parent.mkdir(parents=True,exist_ok=True); ARCH.write_text(json.dumps(unique(a),ensure_ascii=False,indent=2),encoding='utf8')
def main():
 try:
  log.info('Education Update Hub | STABLE AI PUBLISHER')
  sources=SourceManager().get_html_sources(); raw,failed=norm(scrape_compat(sources)); parsed=parse_jobs(raw)
  log.info('Links=%d FailedSources=%d Parsed=%d',len(raw),len(failed),len(parsed))
  if not parsed:return
  old=unique(load_jobs()); archive=load_arch(); known=unique(old+archive)
  result=run_optimizer(known,parsed); fresh=unique(result.get('new_jobs',[]) if isinstance(result,dict) else [])
  known_keys={key(j) for j in known if key(j)}
  eligible=[j for j in fresh if ai_candidate(j) and key(j) not in known_keys]
  eligible=sorted(eligible,key=candidate_score,reverse=True)
  log.info('NEW POST SELECTION | Existing=%d | Archived=%d | FreshValid=%d | AIEligible=%d | Target=%d',len(old),len(archive),len(fresh),len(eligible),MAX_AI)
  from ai_editor import enrich
  made=[]; attempts=0
  for raw_job in eligible:
   if len(made)>=MAX_AI or attempts>=MAX_ATTEMPTS:break
   attempts+=1
   try:
    j=enrich(dict(raw_job)); j['ai_generated']=True; j['site_published_at']=datetime.now().strftime('%Y-%m-%d'); j['status'],j['is_expired']=status(j); made.append(j); log.info('AI OK %d/%d | %s | %s',len(made),MAX_AI,j.get('title'),j.get('category'))
   except RuntimeError as e:
    if str(e)=='OPENROUTER_RATE_LIMIT':log.error('OpenRouter 429 -> STOP AI');break
    log.warning('AI skipped: %s | %s',raw_job.get('title'),e)
   except Exception as e:log.warning('AI skipped: %s | %s',raw_job.get('title'),e)
  if not made and not old:return
  live=unique(old+made); archive=unique(archive); still=[]
  for j in live:
   j['status'],j['is_expired']=status(j)
   if j['is_expired']:archive.append(j)
   else:still.append(j)
  archive=unique(archive)
  for j in archive:j['status']='Application Closed';j['is_expired']=True
  save_arch(archive); save_jobs(still)
  clean_output_directory(); all_public=unique(still+archive); generate_all(all_public,category_jobs=still); category_generator.build_categories(still); homepage.run(still)
  from archive_generator import build_archive; build_archive(archive)
  try:update_sitemap(all_public)
  except TypeError:update_sitemap()
  log.info('DONE | Live=%d Archived=%d NewAI=%d Attempts=%d Target=%d',len(still),len(archive),len(made),attempts,MAX_AI)
 except Exception:log.exception('Fatal Error');sys.exit(1)
if __name__=='__main__':main()
