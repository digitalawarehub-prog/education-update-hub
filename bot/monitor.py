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
MAX_AI=int(os.getenv('MAX_AI_POSTS_PER_RUN','5')); CANDIDATES=max(8,MAX_AI*2); ROOT=Path(__file__).resolve().parent.parent; ARCH=ROOT/'database'/'archive.json'
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
  # Remove all pre-AI legacy records; retain only posts made by this publisher.
  ai_old=[j for j in old if j.get('ai_generated')]
  result=run_optimizer(ai_old,parsed); new=unique(result.get('new_jobs',[]) if isinstance(result,dict) else [])[:CANDIDATES]
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
  if not made and not ai_old:return
  live=unique(ai_old+made); archive=load_arch(); still=[]
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
  log.info('DONE | Live=%d Archived=%d NewAI=%d LegacyRemoved=%d',len(still),len(archive),len(made),len(old)-len(ai_old))
 except Exception:log.exception('Fatal Error');sys.exit(1)
if __name__=='__main__':main()
