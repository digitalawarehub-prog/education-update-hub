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
MAX_AI=int(os.getenv('MAX_AI_POSTS_PER_RUN','5')); CANDIDATES=max(40,MAX_AI*10); ROOT=Path(__file__).resolve().parent.parent; ARCH=ROOT/'database'/'archive.json'
def norm(x): return (x[0] or [],x[1] or []) if isinstance(x,tuple) else (x or [],[])
def scrape_compat(s):
 p=inspect.signature(scrape_all_sources).parameters
 if 'workers' in p:return scrape_all_sources(s,workers=10)
 if 'max_workers' in p:return scrape_all_sources(s,max_workers=10)
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

# Only genuine fresh opportunities should be sent to the AI editor.
def ai_candidate(j):
 t=str(j.get('title') or '').strip().casefold()
 body=str(j.get('content') or j.get('description') or '').strip().casefold()
 # Reject clearly obsolete advertisements/forms/notices before spending AI quota.
 years=[int(x) for x in re.findall(r'\b(20\d{2})\b', t)]
 if years and max(years) < date.today().year-1: return False
 if any(x in t for x in ('scribe declaration','certificate of disability','application form','press release','caveat','financial results','how do you apply','click here','advertisements')): return False
 if not t or len(t)<12: return False
 blocked=(
  'result','results','answer key','answer-key','admit card','admit-card','hall ticket','score card','scorecard',
  'merit list','selected candidates','selected candidate','qualified candidates','qualified candidate',
  'previous year','previous years','question paper','question papers','exam schedule','examination schedule',
  'exam date','examination date','interview schedule','corrigendum','extension of last date','extension of date',
  'revised schedule','date extended','provisional answer','syllabus','shortlisted candidates','shortlisted candidate',
  'final answer key','waiting list','cut off','cut-off','score list','individual score'
 )
 if any(x in t for x in blocked): return False
 # Genuine application/engagement language is required for recruitment-style posts.
 good=(
  'recruitment','vacancy','vacancies','applications are invited','application invited','apply online',
  'online application','engagement of','appointment of','walk-in','walk in','भर्ती','रिक्ति','आवेदन आमंत्रित',
  'ऑनलाइन आवेदन','नियुक्ति','संविदा','guest lecturer','contractual'
 )
 if not any(x in t for x in good): return False
 # For English titles, require application/recruitment evidence in the record itself.
 evidence=t+' '+body
 if not any(x in evidence for x in ('applications are invited','application invited','apply online','online application','engagement of','appointment of','walk-in','walk in','recruitment','vacancy','भर्ती','रिक्ति','आवेदन आमंत्रित','ऑनलाइन आवेदन','नियुक्ति','संविदा')): return False
 return True
def load_arch():
 try:return json.loads(ARCH.read_text(encoding='utf8')) if ARCH.exists() else []
 except:return []
def save_arch(a):
 ARCH.parent.mkdir(parents=True,exist_ok=True); ARCH.write_text(json.dumps(unique(a),ensure_ascii=False,indent=2),encoding='utf8')
def main():
 try:
  log.info('Education Update Hub | FINAL AI PUBLISHER')
  sources=SourceManager().get_html_sources(); raw,failed=norm(scrape_compat(sources)); parsed=parse_jobs(raw)
  log.info('Links=%d FailedSources=%d Parsed=%d',len(raw),len(failed),len(parsed))
  if not parsed:return
  old=unique(load_jobs())
  archive=load_arch()
  # Use ALL existing live + archived records for deduplication. This prevents
  # previously published manual/AI items from being treated as fresh again.
  known=unique(old+archive)
  result=run_optimizer(known,parsed)
  fresh=unique(result.get('new_jobs',[]) if isinstance(result,dict) else [])
  known_keys={key(j) for j in known if key(j)}
  new=[]; seen=set()
  for j in fresh:
   if not ai_candidate(j): continue
   k=key(j)
   if k and k not in known_keys and k not in seen:
    seen.add(k); new.append(j)
   if len(new)>=CANDIDATES: break
  log.info('NEW POST SELECTION | Existing=%d | Archived=%d | FreshValid=%d | AIEligible=%d | Target=%d',len(old),len(archive),len(fresh),len(new),MAX_AI)
  from ai_editor import enrich
  made=[]
  for raw_job in new:
   if len(made)>=MAX_AI:break
   try:
    j=enrich(dict(raw_job)); j['ai_generated']=True; j['site_published_at']=datetime.now().strftime('%Y-%m-%d'); j['status'],j['is_expired']=status(j); made.append(j); log.info('AI OK | %s | %s',j.get('title'),j.get('category'))
   except RuntimeError as e:
    if str(e)=='OPENROUTER_RATE_LIMIT':log.error('OpenRouter 429 -> STOP AI');break
    log.warning('AI skipped: %s | %s',raw_job.get('title'),e)
   except Exception:log.exception('AI failed: %s',raw_job.get('title'))
  if not made and not old:return
  live=unique(old+made); archive=unique(archive); still=[]
  for j in live:
   j['status'],j['is_expired']=status(j)
   if j['is_expired']:archive.append(j)
   else:still.append(j)
  archive=unique(archive)
  for j in archive:j['status']='Application Closed';j['is_expired']=True
  save_arch(archive); save_jobs(still)
  clean_output_directory(); all_public=unique(still+archive); generate_all(all_public,category_jobs=still)
  category_generator.build_categories(still); homepage.run(still)
  from archive_generator import build_archive; build_archive(archive)
  try:update_sitemap(all_public)
  except TypeError:update_sitemap()
  log.info('DONE | Live=%d Archived=%d NewAI=%d Target=%d',len(still),len(archive),len(made),MAX_AI)
 except Exception:log.exception('Fatal Error');sys.exit(1)
if __name__=='__main__':main()
