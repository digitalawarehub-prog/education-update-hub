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
MAX_AI=int(os.getenv('MAX_AI_POSTS_PER_RUN','5')); CANDIDATES=max(120,MAX_AI*24); ROOT=Path(__file__).resolve().parent.parent; ARCH=ROOT/'database'/'archive.json'
def norm(x): return (x[0] or [],x[1] or []) if isinstance(x,tuple) else (x or [],[])
def scrape_compat(s):
 p=inspect.signature(scrape_all_sources).parameters
 if 'workers' in p:return scrape_all_sources(s,workers=24)
 if 'max_workers' in p:return scrape_all_sources(s,max_workers=24)
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
 # Accept common date formats, but never let malformed calendar values crash the publisher.
 patterns=(
  (r'^(\d{2})-(\d{2})-(20\d{2})$', lambda m:(int(m.group(3)),int(m.group(2)),int(m.group(1)))),
  (r'^(\d{2})/(\d{2})/(20\d{2})$', lambda m:(int(m.group(3)),int(m.group(2)),int(m.group(1)))),
  (r'^(20\d{2})-(\d{2})-(\d{2})', lambda m:(int(m.group(1)),int(m.group(2)),int(m.group(3)))),
 )
 for pat,parts in patterns:
  m=re.search(pat,s)
  if m:
   try:
    y,mo,d=parts(m)
    return date(y,mo,d)
   except (ValueError,TypeError):
    log.warning('Ignoring invalid date value: %r',v)
    return None
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
 if not t or len(t)<12: return False
 blocked=(
  'result','results','answer key','answer-key','admit card','admit-card','hall ticket','score card','scorecard',
  'merit list','selected candidates','selected candidate','qualified candidates','qualified candidate',
  'previous year','previous years','question paper','question papers','exam schedule','examination schedule',
  'exam date','examination date','interview schedule','corrigendum','extension of last date','extension of date',
  'revised schedule','date extended','provisional answer','syllabus','shortlisted candidates','shortlisted candidate',
  'final answer key','waiting list','cut off','cut-off','score list','individual score','call letter','main examination call letter','preliminary examination call letter',
  'provisionally selected','provisionally shortlisted','no candidate shortlisted','list of candidates','candidate shortlisted',
  'selected in second wait list','second wait list','backlog vacancies (preliminary examination',
  'vice chancellor','vice-chancellor','kulapati','re-appointed','reappointed','second term','कार्यकाल','कुलपति','पुनः नियुक्त','नियुक्त किया गया','appointment announced'
 )
 if any(x in t for x in blocked): return False
 if any(x in t for x in ('press release','press-release','gazette','act,','act ','rti officer','rti officers','faq','previous years','notice to the candidates','marks of the candidates','eligible and ineligible candidates','refund of fee','refund of fees','stands cancelled','cancellation of','preference selection')): return False
 # Appointment/reappointment news is not recruitment unless the title also
 # clearly contains an application/vacancy signal.
 if any(x in t for x in ('appointment of','re-appointed','reappointed','vice chancellor','vice-chancellor','second term','कुलपति','पुनः नियुक्त','नियुक्त किया गया')) and not any(x in t for x in ('recruitment','vacancy','apply online','applications are invited','application invited','भर्ती','रिक्ति','आवेदन आमंत्रित')):
  return False
 years=[int(y) for y in re.findall(r'\b(20\d{2})\b',t)]
 if years and max(years) < date.today().year: return False
 # Genuine application/engagement language is required for recruitment-style posts.
 good=(
  'recruitment','vacancy','vacancies','applications are invited','application invited','apply online',
  'online application','engagement of','appointment of','walk-in','walk in','भर्ती','रिक्ति','आवेदन आमंत्रित',
  'ऑनलाइन आवेदन','नियुक्ति','संविदा','guest lecturer','contractual'
 )
 if not any(x in t for x in good): return False
 return True

# -------------------- AdSense / Public Quality Gate --------------------
# Keep low-value notification shells out of public pages. These records may
# remain in archive.json for traceability, but they are never rendered.
PUBLIC_BLOCKED = (
    'selection list','selection-list','result of','re-examination result',
    're-examination results','answer key','answer-key','admit card','admit-card',
    'hall ticket','call letter','preference selection','waiting list',
    'qualified candidates','selected candidates','shortlisted candidates',
    'extension of last date','extension of date','date extended','last date extended',
    'stands cancelled','cancelled','cancellation of','refund of fees','refund of fee',
    're-examination','exam schedule','examination schedule','exam date',
    'interview schedule','corrigendum','press release','press-release',
    'appointment of','re-appointed','reappointed','second term','vice chancellor',
    'vice-chancellor','kulapati','कार्यकाल','कुलपति','पुनः नियुक्त',
    'नियुक्त किया गया','चयन सूची','चयनित उम्मीदवार','उत्तर कुंजी','प्रवेश पत्र',
    'परिणाम','अंतिम तिथि बढ़ी','तिथि बढ़ी','रद्द','शुल्क वापसी'
)
RECRUITMENT_SIGNALS = (
    'recruitment','vacancy','vacancies','applications are invited',
    'application invited','apply online','online application','registration',
    'engagement of','walk-in','walk in','apprentice','apprenticeship',
    'भर्ती','रिक्ति','आवेदन आमंत्रित','ऑनलाइन आवेदन','पंजीकरण','अप्रेंटिस',
    'सीधी भर्ती'
)

def public_quality_ok(j):
    """Return True only for useful, article-level public content."""
    title=str(j.get('title') or '').strip()
    t=title.casefold()
    if not title or len(title)<20:
        return False
    if any(x in t for x in PUBLIC_BLOCKED):
        return False

    typ=str(j.get('post_type') or '').casefold()
    cat=str(j.get('category') or '').casefold()

    # Recruitment pages must actually be about applying/engagement, not an
    # Act, policy, exam notice, person appointment, or generic landing page.
    is_recruit = typ=='recruitment' or cat=='recruitment' or any(x in t for x in RECRUITMENT_SIGNALS)
    if is_recruit:
        if not any(x in t for x in RECRUITMENT_SIGNALS):
            return False
        # Do not publish an empty/shell AI article as a recruitment post.
        # Older records can legitimately have one missing field, so the gate
        # targets generic placeholder/OCR content rather than deleting every
        # recruitment record with incomplete metadata.
        fields=('vacancy','qualification','age_limit','application_fee',
                'selection_process','last_date','application_start_date','salary')
        populated=sum(1 for k in fields if str(j.get(k) or '').strip() and
                      str(j.get(k)).strip().casefold() not in {'not specified','not mentioned','not available'})
        summary=str(j.get('summary') or j.get('description') or '').strip()
        intro=str(j.get('intro') or '').strip()
        generic = (
            'से संबंधित आधिकारिक अपडेट को सरल भाषा में संकलित किया गया है' in summary or
            'के संबंध में उपलब्ध महत्वपूर्ण जानकारी नीचे दी गई है' in intro or
            summary.casefold().startswith('official recruitment notification for')
        )
        if (j.get('ai_generated') or j.get('ai_model')) and generic and populated < 2:
            return False
        sal=str(j.get('salary') or '')
        if re.search(r'(?:ment done|freq:|qv\^|f41q)',sal,re.I) or len(re.findall(r'[\^~`]',sal))>=2:
            return False
    return True

def split_public_records(live, archived):
    """Move clearly low-value live records to archive and hide them from HTML."""
    clean_live=[]; moved=[]
    for j in live or []:
        if public_quality_ok(j):
            clean_live.append(j)
        else:
            j=dict(j)
            j['status']='Archived - Low Value'
            j['is_expired']=True
            moved.append(j)
    clean_archive=[j for j in (archived or []) if public_quality_ok(j)]
    hidden_archive=[j for j in (archived or []) if not public_quality_ok(j)]
    hidden_archive.extend(moved)
    return unique(clean_live), unique(hidden_archive), unique(clean_archive)

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
  # Always initialize fresh before optimizer output is inspected.
  # This keeps the publisher safe even if optimizer returns None/list/dict.
  fresh=[]
  try:
   result=run_optimizer(known,parsed)
   if isinstance(result,dict):
    fresh=unique(result.get('new_jobs') or [])
   elif isinstance(result,list):
    fresh=unique(result)
  except Exception:
   log.exception('Optimizer failed; continuing with an empty fresh list')
   fresh=[]
  known_keys={key(j) for j in known if key(j)}
  new=[]; seen=set()
  for j in fresh:
   if not ai_candidate(j): continue
   k=key(j)
   if k and k not in known_keys and k not in seen:
    seen.add(k); new.append(j)
   if len(new)>=CANDIDATES: break
  # Prefer explicit application/registration/recruitment titles. This keeps
  # low-value notices out of the first AI attempts and reduces quota usage.
  def rank_candidate(j):
   t=str(j.get('title') or '').casefold()
   score=0
   for x in ('applications are invited','apply online','online application','registration from','recruitment of','recruitment –','recruitment -','भर्ती','आवेदन आमंत्रित'):
    if x in t: score+=4
   if j.get('notification_pdf'): score+=2
   if j.get('last_date'): score+=2
   if j.get('vacancy'): score+=1
   return -score
  new=sorted(new,key=rank_candidate)[:max(12,MAX_AI*3)]
  log.info('NEW POST SELECTION | Existing=%d | Archived=%d | FreshValid=%d | AIEligible=%d | Target=%d',len(old),len(archive),len(fresh),len(new),MAX_AI)
  if len(new)<MAX_AI:
   log.warning('AI_TARGET_LIMITED | Only %d genuinely new eligible source(s) found; will not recycle old posts',len(new))
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
  # Final public-quality pass: keep weak/notification-only records out of
  # homepage, categories and generated post HTML. They remain in archive.json
  # only for internal traceability.
  still, hidden_archive, visible_archive = split_public_records(still, archive)
  archive = unique(hidden_archive + visible_archive)
  save_arch(archive); save_jobs(still)
  clean_output_directory()
  all_public=unique(still + visible_archive)
  generate_all(all_public,category_jobs=still)
  category_generator.build_categories(still); homepage.run(still)
  from archive_generator import build_archive; build_archive(visible_archive)
  try:update_sitemap(all_public)
  except TypeError:update_sitemap()
  log.info('DONE | Live=%d Archived=%d NewAI=%d Target=%d',len(still),len(archive),len(made),MAX_AI)
 except Exception:log.exception('Fatal Error');sys.exit(1)
if __name__=='__main__':main()
