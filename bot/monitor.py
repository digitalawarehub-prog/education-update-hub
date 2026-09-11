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
MAX_AI=int(os.getenv('MAX_AI_POSTS_PER_RUN','5')); CANDIDATES=max(20,MAX_AI*4); ROOT=Path(__file__).resolve().parent.parent; ARCH=ROOT/'database'/'archive.json'
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
 s=str(v or '').strip()
 if not s:return None
 s=re.sub(r"\s+", " ", s).strip()
 months={"jan":1,"january":1,"feb":2,"february":2,"mar":3,"march":3,"apr":4,"april":4,"may":5,"jun":6,"june":6,"jul":7,"july":7,"aug":8,"august":8,"sep":9,"sept":9,"september":9,"oct":10,"october":10,"nov":11,"november":11,"dec":12,"december":12}
 patterns=[
  r"\b(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})\b",
  r"\b(\d{1,2})[-/.](\d{1,2})[-/.](20\d{2})\b",
  r"\b(\d{1,2})\s+(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(20\d{2})\b"
 ]
 m=re.search(patterns[0],s,re.I)
 if m:
  try:return date(int(m.group(1)),int(m.group(2)),int(m.group(3)))
  except ValueError:return None
 m=re.search(patterns[1],s,re.I)
 if m:
  try:return date(int(m.group(3)),int(m.group(2)),int(m.group(1)))
  except ValueError:return None
 m=re.search(patterns[2],s,re.I)
 if m:
  try:return date(int(m.group(3)),months[m.group(2).lower()],int(m.group(1)))
  except (ValueError,KeyError):return None
 return None
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
  # Keep every existing live post. Only archived posts are removed from the live pool.
  old=unique(load_jobs())
  archived_existing=unique(load_arch())
  archived_keys={key(j) for j in archived_existing}
  old=[j for j in old if key(j) not in archived_keys]
  result=run_optimizer(old,parsed)
  optimizer_new=unique(result.get('new_jobs',[]) if isinstance(result,dict) else [])
  existing_keys={key(j) for j in old}|archived_keys
  # A 'new' post means a never-published source item, not a changed existing item.
  new=[j for j in optimizer_new if key(j) not in existing_keys][:CANDIDATES]
  log.info('NEW POST SELECTION | ExistingLive=%d | Archived=%d | Candidates=%d | Target=%d',len(old),len(archived_existing),len(new),MAX_AI)
  from ai_editor import enrich_many
  made=[]
  # Generate all five posts in ONE OpenRouter request. This reduces free-tier
  # request consumption and prevents a 429 on post #1 from producing fake fallback posts.
  batch=new[:MAX_AI]
  if len(batch) < MAX_AI:
   raise RuntimeError(f'TARGET_NOT_ENOUGH_NEW_CANDIDATES:{len(batch)}/{MAX_AI}')
  try:
   made=enrich_many([dict(x) for x in batch])
   for idx,j in enumerate(made,1):
    j['ai_generated']=True; j['site_published_at']=datetime.now().strftime('%Y-%m-%d'); j['status'],j['is_expired']=status(j)
    log.info('AI OK | %d/%d | %s | %s',idx,MAX_AI,j.get('title'),j.get('category'))
  except RuntimeError as e:
   if str(e)=='OPENROUTER_RATE_LIMIT':
    log.error('OPENROUTER 429 | No local fallback used. 5 real AI posts cannot be claimed until the API quota/rate limit is available.')
   raise
  if not made and not old:return
  # Accumulate all existing live posts + this run's five new AI posts.
  live=unique(old+made); archive=archived_existing; still=[]
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
  if len(made) < MAX_AI:
   log.warning('TARGET NOT MET | NewAI=%d Target=%d',len(made),MAX_AI)
  log.info('DONE | Live=%d Archived=%d NewAI=%d Target=%d',len(still),len(archive),len(made),MAX_AI)
 except Exception:log.exception('Fatal Error');sys.exit(1)
if __name__=='__main__':main()
