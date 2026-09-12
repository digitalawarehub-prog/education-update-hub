from __future__ import annotations
import json, logging, os, re, sys, inspect
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from sources_manager import SourceManager
from scraper import scrape_all_sources
from parser import parse_jobs
from database import load_jobs, save_jobs
from html_generator import generate_all, clean_output_directory
import homepage, category_generator
from sitemap_generator import update_sitemap

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
log = logging.getLogger('EUH_FINAL')

MAX_AI = int(os.getenv('MAX_AI_POSTS_PER_RUN', '5'))
CANDIDATES = max(40, MAX_AI * 10)
ROOT = Path(__file__).resolve().parent.parent
ARCH = ROOT / 'database' / 'archive.json'

# Pages which are useful government updates but are NOT recruitment articles.
NON_RECRUITMENT_PATTERNS = (
    'selected candidates', 'selected candidate', 'qualified candidates', 'qualified candidate',
    'shortlisted candidates', 'shortlisted candidate', 'merit list', 'selection list',
    'final result', 'result of', 'answer key', 'admit card', 'hall ticket', 'call letter',
    'exam schedule', 'examination schedule', 'exam programme', 'exam program', 'exam calendar',
    'time table', 'timetable', 'date sheet', 'previous year question', 'question paper',
    'question papers', 'recruitment exams', 'recruitment examination', 'interview schedule',
    'corrigendum', 'tender', 'press release', 'press-release', 'score card', 'scorecard',
    'individual score', 'api score', 'marks obtained', 'document verification',
    'counselling schedule', 'counselling', 'old recruitment', 'old result',
    'recruitment rules', 'recruitment calendar', 'recruitment cell', 'vacancy position',
    'recruitment notices', 'recruitment notice board', 'application link', 'apply link',
)
RECRUITMENT_SIGNALS = (
    'recruitment', 'vacancy', 'vacancies', 'applications are invited', 'application invited',
    'apply online', 'online application', 'engagement of', 'appointment of', 'direct recruitment',
    'advertisement for', 'advertisement no', 'apprentice', 'apprenticeship', 'hiring', 'career',
    'भर्ती', 'रिक्ति', 'आवेदन आमंत्रित', 'ऑनलाइन आवेदन', 'नियुक्ति', 'अप्रेंटिस', 'विज्ञापन',
)
ROLE_SIGNALS = (
    'assistant', 'teacher', 'officer', 'engineer', 'technician', 'constable', 'inspector', 'clerk',
    'stenographer', 'patwari', 'lekhpal', 'fellow', 'research', 'scientist', 'staff', 'faculty',
    'professor', 'lecturer', 'driver', 'manager', 'analyst', 'nurse', 'pharmacist', 'attendant',
    'peon', 'junior', 'senior', 'शिक्षक', 'अधिकारी', 'प्रोफेसर', 'व्याख्याता', 'कर्मचारी', 'पद',
)

def norm(x):
    return (x[0] or [], x[1] or []) if isinstance(x, tuple) else (x or [], [])

def scrape_compat(sources):
    params = inspect.signature(scrape_all_sources).parameters
    if 'workers' in params:
        return scrape_all_sources(sources, workers=10)
    if 'max_workers' in params:
        return scrape_all_sources(sources, max_workers=10)
    return scrape_all_sources(sources)

def clean_url(url):
    u = str(url or '').strip()
    if not u:
        return ''
    try:
        p = urlsplit(u)
        return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip('/'), '', ''))
    except Exception:
        return u.split('#', 1)[0].split('?', 1)[0].rstrip('/').casefold()

def source_key(job):
    u = clean_url(job.get('url'))
    if u:
        return 'url:' + u
    jid = str(job.get('job_id') or '').strip().casefold()
    if jid:
        return 'id:' + jid
    return 'title:' + re.sub(r'\s+', ' ', str(job.get('title') or '').strip()).casefold()

def unique(jobs):
    out, seen = [], set()
    for job in jobs or []:
        k = source_key(job)
        if k and k not in seen:
            seen.add(k); out.append(job)
    return out

def parse_date(value):
    s = re.sub(r'\s+', ' ', str(value or '').strip())
    if not s:
        return None
    for pat, order in (
        (r'^(\d{2})-(\d{2})-(20\d{2})$', 'dmy'),
        (r'^(20\d{2})-(\d{2})-(\d{2})$', 'ymd'),
        (r'^(\d{1,2})[/.-](\d{1,2})[/.-](20\d{2})$', 'dmy'),
    ):
        m = re.search(pat, s)
        if m:
            try:
                a, b, c = map(int, m.groups())
                return date(c, b, a) if order == 'dmy' else date(a, b, c)
            except ValueError:
                return None
    months = {'jan':1,'january':1,'feb':2,'february':2,'mar':3,'march':3,'apr':4,'april':4,
              'may':5,'jun':6,'june':6,'jul':7,'july':7,'aug':8,'august':8,'sep':9,'sept':9,
              'september':9,'oct':10,'october':10,'nov':11,'november':11,'dec':12,'december':12}
    m = re.search(r'^(\d{1,2})\s+([A-Za-z]+)\s+(20\d{2})$', s)
    if m and m.group(2).lower() in months:
        try: return date(int(m.group(3)), months[m.group(2).lower()], int(m.group(1)))
        except ValueError: return None
    return None

def deadline(job):
    for k in ('last_date','deadline','application_last_date','last_date_to_apply','closing_date','application_deadline'):
        d = parse_date(job.get(k))
        if d: return d
    return None

def status(job):
    d = deadline(job)
    return ('Application Closed', True) if d and d < date.today() else ('Active', False)

def load_arch():
    try:
        return json.loads(ARCH.read_text(encoding='utf-8')) if ARCH.exists() else []
    except Exception:
        return []

def save_arch(items):
    ARCH.parent.mkdir(parents=True, exist_ok=True)
    ARCH.write_text(json.dumps(unique(items), ensure_ascii=False, indent=2), encoding='utf-8')

def candidate_ok(job):
    title = re.sub(r'\s+', ' ', str(job.get('title') or '').strip()).casefold()
    desc = re.sub(r'\s+', ' ', str(job.get('description') or job.get('content') or '').strip()).casefold()
    if len(title) < 12:
        return False
    if any(p in title for p in NON_RECRUITMENT_PATTERNS):
        return False
    has_recruitment = any(p in title for p in RECRUITMENT_SIGNALS)
    has_role = any(p in title for p in ROLE_SIGNALS)
    # A recruitment article must have an application/vacancy signal in the title.
    if not (has_recruitment and (has_role or any(x in title for x in ('post', 'posts', 'vacancy', 'vacancies', 'recruitment of', 'applications are invited', 'apply online', 'engagement of', 'appointment of')))):
        return False
    # Never use a result/exam/selected-candidate page merely because its body mentions recruitment.
    if any(p in title for p in NON_RECRUITMENT_PATTERNS):
        return False
    if any(p in desc[:2500] for p in ('selected candidates list', 'qualified candidates list', 'previous years question papers')) and not any(p in title for p in ('applications are invited', 'apply online', 'vacancy', 'recruitment')):
        return False
    if not str(job.get('url') or '').lower().startswith(('http://','https://')):
        return False
    return True

def main():
    try:
        log.info('Education Update Hub | QUALITY + REAL AI PUBLISHER')
        sources = SourceManager().get_html_sources()
        raw, failed = norm(scrape_compat(sources))
        parsed = unique(parse_jobs(raw))
        log.info('Links=%d FailedSources=%d ParsedUnique=%d', len(raw), len(failed), len(parsed))
        if not parsed:
            log.warning('No parsed jobs; nothing to publish.')
            return

        old = unique(load_jobs())
        archive = unique(load_arch())
        archived_keys = {source_key(j) for j in archive}
        live = [j for j in old if source_key(j) not in archived_keys]
        existing_keys = {source_key(j) for j in live} | archived_keys

        # Select ONLY never-published genuine recruitment items.
        candidates = []
        for job in parsed:
            k = source_key(job)
            if k in existing_keys or not candidate_ok(job):
                continue
            candidates.append(job)
            if len(candidates) >= CANDIDATES:
                break
        log.info('NEW POST SELECTION | ExistingLive=%d | Archived=%d | Candidates=%d | Target=%d', len(live), len(archive), len(candidates), MAX_AI)
        if len(candidates) < MAX_AI:
            raise RuntimeError(f'TARGET_NOT_ENOUGH_QUALITY_CANDIDATES:{len(candidates)}/{MAX_AI}')

        from ai_editor import enrich_many
        made = enrich_many([dict(x) for x in candidates[:CANDIDATES]], target=MAX_AI)
        if len(made) != MAX_AI:
            raise RuntimeError(f'AI_TARGET_NOT_REACHED:{len(made)}/{MAX_AI}')

        for i, j in enumerate(made, 1):
            j['ai_generated'] = True
            j['site_published_at'] = datetime.now().strftime('%Y-%m-%d')
            j['status'], j['is_expired'] = status(j)
            log.info('AI OK | %d/%d | %s | %s', i, MAX_AI, j.get('title'), j.get('category'))

        live = unique(live + made)
        still = []
        for j in live:
            j['status'], j['is_expired'] = status(j)
            if j['is_expired']:
                archive.append(j)
            else:
                still.append(j)
        archive = unique(archive)
        for j in archive:
            j['status'] = 'Application Closed'; j['is_expired'] = True

        save_arch(archive)
        save_jobs(still)
        clean_output_directory()
        all_public = unique(still + archive)
        generate_all(all_public, category_jobs=still)
        category_generator.build_categories(still)
        homepage.run(still)
        from archive_generator import build_archive
        build_archive(archive)
        try:
            update_sitemap(all_public)
        except TypeError:
            update_sitemap()
        log.info('DONE | Live=%d Archived=%d NewAI=%d Target=%d ArchivedThisRun=%d', len(still), len(archive), len(made), MAX_AI, sum(1 for j in archive if j.get('site_published_at') == datetime.now().strftime('%Y-%m-%d') and j.get('is_expired')))
    except Exception:
        log.exception('Fatal Error')
        sys.exit(1)

if __name__ == '__main__':
    main()
