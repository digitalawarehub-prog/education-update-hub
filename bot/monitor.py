import logging, os, sys, inspect, json, re
from datetime import datetime, date
from pathlib import Path
from sources_manager import SourceManager
from scraper import scrape_all_sources
from parser import parse_jobs
from optimizer import run_optimizer
from database import load_jobs, save_jobs
from html_generator import generate_all, clean_output_directory
import homepage, category_generator
from sitemap_generator import update_sitemap
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
log=logging.getLogger('EUH_FINAL')
MAX_AI=max(1,int(os.getenv('MAX_AI_POSTS_PER_RUN','5')))
ROOT=Path(__file__).resolve().parent.parent; ARCH=ROOT/'database'/'archive.json'
def norm(x): return (x[0] or [],x[1] or []) if isinstance(x,tuple) else (x or [],[])
def scrape_compat(s):
 p=inspect.signature(scrape_all_sources).parameters
 if 'workers' in p:return scrape_all_sources(s,workers=10)
 if 'max_workers' in p:return scrape_all_sources(s,max_workers=10)
 return scrape_all_sources(s)
def key(j):return str(j.get('job_id') or j.get('url') or j.get('title') or '').strip().casefold()
def unique(a):
 out=[]; seen=set()
 for j in a or []:
  k=key(j)
  if k and k not in seen:seen.add(k);out.append(j)
 return out
def pdate(v):
 s=str(v or '').strip()
 for f in ('%d-%m-%Y','%Y-%m-%d','%d/%m/%Y','%d.%m.%Y'):
  try:return datetime.strptime(s[:10],f).date()
  except:pass
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
def score(j):
 t=str(j.get('title','')).casefold(); s=0
 if any(x in t for x in ('recruitment','vacancy','applications are invited','apply online','engagement of','appointment of','भर्ती','रिक्ति')):s+=100
 if any(x in t for x in ('admit card','result','answer key','syllabus','scholarship')):s+=40
 if any(x in t for x in ('notice','circular','order','information','सूचना','आदेश')):s-=80
 if any(j.get(k) for k in ('vacancy','qualification','salary','last_date','application_fee')):s+=25
 d=deadline(j)
 if d and d>=date.today():s+=20
 return s
def main():
 try:
  log.info('Education Update Hub | AI Publisher | Target=%d',MAX_AI)
  raw,failed=norm(scrape_compat(SourceManager().get_html_sources())); parsed=parse_jobs(raw)
  log.info('Links=%d FailedSources=%d Parsed=%d',len(raw),len(failed),len(parsed))
  if not parsed: raise RuntimeError('NO_PARSED_JOBS')
  old=unique(load_jobs()); ai_old=[j for j in old if j.get('ai_generated')]
  result=run_optimizer(ai_old,parsed); fresh=unique(result.get('new_jobs',[]) if isinstance(result,dict) else [])
  candidates=sorted(fresh,key=score,reverse=True)[:max(40,MAX_AI*10)]
  log.info('AI CANDIDATES=%d | Target=%d',len(candidates),MAX_AI)
  from ai_editor import enrich
  made=[]
  for raw_job in candidates:
   if len(made)>=MAX_AI:break
   try:
    j=enrich(dict(raw_job)); j['ai_generated']=True; j['site_published_at']=datetime.now().strftime('%Y-%m-%d'); j['status'],j['is_expired']=status(j); made.append(j)
    log.info('AI OK | %d/%d | %s | %s',len(made),MAX_AI,j.get('title'),j.get('category'))
   except Exception as e:log.warning('Candidate failed: %s | %s',raw_job.get('title'),e)
  if len(made)<MAX_AI: raise RuntimeError(f'AI_TARGET_NOT_REACHED: {len(made)}/{MAX_AI}')
  live=unique(ai_old+made); archive=load_arch(); still=[]
  for j in live:
   j['status'],j['is_expired']=status(j)
   (archive if j['is_expired'] else still).append(j)
  archive=unique(archive)
  for j in archive:j['status'],j['is_expired']='Application Closed',True
  save_arch(archive);save_jobs(still);clean_output_directory();all_public=unique(still+archive)
  generate_all(all_public,category_jobs=still);category_generator.build_categories(still);homepage.run(still)
  from archive_generator import build_archive;build_archive(archive)
  try:update_sitemap(all_public)
  except TypeError:update_sitemap()
  log.info('DONE | Live=%d Archived=%d NewAI=%d Target=%d',len(still),len(archive),len(made),MAX_AI)
 except Exception:
  log.exception('Fatal Error');sys.exit(1)
if __name__=='__main__':main()
