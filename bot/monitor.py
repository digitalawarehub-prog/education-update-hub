import logging, os, sys, inspect, json, re
from datetime import datetime, date
from pathlib import Path

from sources_manager import SourceManager
from scraper import scrape_all_sources
from parser import parse_jobs
from database import load_jobs, save_jobs
from html_generator import generate_all, clean_output_directory
import homepage, category_generator
from sitemap_generator import update_sitemap

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
log = logging.getLogger('EUH_FINAL')

MAX_AI = max(1, int(os.getenv('MAX_AI_POSTS_PER_RUN', '5')))
CANDIDATE_POOL = max(40, MAX_AI * 12)
ROOT = Path(__file__).resolve().parent.parent
ARCH = ROOT / 'database' / 'archive.json'


def norm(x):
    return (x[0] or [], x[1] or []) if isinstance(x, tuple) else (x or [], [])


def scrape_compat(sources):
    p = inspect.signature(scrape_all_sources).parameters
    if 'workers' in p:
        return scrape_all_sources(sources, workers=24)
    if 'max_workers' in p:
        return scrape_all_sources(sources, max_workers=24)
    return scrape_all_sources(sources)


def stable_key(j):
    url = str(j.get('url') or '').strip().split('#', 1)[0].rstrip('/').casefold()
    jid = str(j.get('job_id') or '').strip().casefold()
    title = re.sub(r'\s+', ' ', str(j.get('title') or '')).strip().casefold()
    # URL is the strongest identity; fall back to job_id/title when needed.
    return ('url:' + url) if url else (('id:' + jid) if jid else ('title:' + title))


def unique(items):
    out, seen = [], set()
    for j in items or []:
        k = stable_key(j)
        if k and k not in seen:
            seen.add(k)
            out.append(j)
    return out


def pdate(value):
    s = str(value or '').strip()
    patterns = (
        (r'^(\d{2})-(\d{2})-(20\d{2})$', lambda m: (int(m.group(3)), int(m.group(2)), int(m.group(1)))),
        (r'^(\d{2})/(\d{2})/(20\d{2})$', lambda m: (int(m.group(3)), int(m.group(2)), int(m.group(1)))),
        (r'^(20\d{2})-(\d{2})-(\d{2})', lambda m: (int(m.group(1)), int(m.group(2)), int(m.group(3)))),
    )
    for pat, parts in patterns:
        m = re.search(pat, s)
        if m:
            try:
                y, mo, d = parts(m)
                return date(y, mo, d)
            except (ValueError, TypeError):
                log.warning('Ignoring invalid date value: %r', value)
                return None
    return None


def deadline(j):
    for k in ('last_date', 'deadline', 'application_last_date', 'last_date_to_apply', 'closing_date', 'application_deadline'):
        d = pdate(j.get(k))
        if d:
            return d
    return None


def status(j):
    d = deadline(j)
    return ('Application Closed', True) if d and d < date.today() else ('Active', False)


# These are NOT recruitment opportunities. Keeping them out here prevents
# appointment/news/extension notices from ever reaching the AI editor.
BLOCKED = (
    'result', 'results', 'answer key', 'answer-key', 'admit card', 'admit-card',
    'hall ticket', 'score card', 'scorecard', 'merit list', 'selected candidates',
    'selected candidate', 'provisionally selected', 'qualified candidates',
    'qualified candidate', 'previous year', 'previous years', 'question paper',
    'question papers', 'exam schedule', 'examination schedule', 'exam programme',
    'exam calendar', 'interview schedule', 'final result', 'waiting list',
    'cut off', 'cut-off', 'score list', 'individual score', 'corrigendum',
    'extension of last date', 'extension of date', 'date extended', 'revised schedule',
    'revised result', 'proceedings', 'notification regarding', 'press release',
    'press-release', 'gazette', 'vice chancellor', 'vice-chancellor', 'kulapati',
    're-appointed', 'reappointed', 'second term', 'कार्यकाल', 'कुलपति',
    'पुनः नियुक्त', 'पुनर्नियुक्त', 'नियुक्त किया गया', 'पदस्थापना', 'स्थानांतरण',
    'transfer order', 'promotion order', 'award', 'award ceremony', 'retirement',
    'farewell', 'obituary', 'notice regarding', 'important notice regarding',
    'advertisement cancellation', 'stands cancelled', 'cancelled as per',
)

RECRUITMENT_SIGNALS = (
    'recruitment', 'vacancy', 'vacancies', 'applications are invited',
    'application invited', 'apply online', 'online application',
    'online applications', 'engagement of', 'walk-in', 'walk in',
    'apprentice', 'apprenticeship', 'for the post', 'for the posts',
    'advertisement for', 'recruitment of', 'career opportunity',
    'call for applications', 'applications invited', 'भर्ती', 'रिक्ति',
    'आवेदन आमंत्रित', 'ऑनलाइन आवेदन', 'अप्रेंटिस', 'पद हेतु आवेदन',
    'संविदा', 'contract basis', 'contractual basis', 'contract basis',
)

ROLE_SIGNALS = (
    'assistant', 'teacher', 'officer', 'engineer', 'technician', 'constable',
    'inspector', 'clerk', 'stenographer', 'patwari', 'lekhpal', 'fellow',
    'research', 'professional', 'scientist', 'staff', 'faculty', 'professor',
    'lecturer', 'driver', 'junior', 'senior', 'manager', 'analyst', 'doctor',
    'nurse', 'pharmacist', 'attendant', 'peon', 'consultant', 'surgeon',
    'शिक्षक', 'अधिकारी', 'प्रोफेसर', 'व्याख्याता', 'अनुसंधान', 'पद',
    'कर्मचारी', 'निदेशक',
)


def ai_candidate(job):
    title = re.sub(r'\s+', ' ', str(job.get('title') or '')).strip()
    t = title.casefold()
    desc = re.sub(r'\s+', ' ', str(job.get('description') or '')).strip().casefold()
    pdf = str(job.get('notification_pdf') or '').casefold()
    url = str(job.get('url') or '').casefold()

    if len(title) < 12:
        return False
    if any(x in t for x in BLOCKED):
        return False

    # A future/usable application date is strong evidence, but a missing date
    # is allowed when the notification itself is available for the AI to read.
    evidence = ' '.join((t, desc, pdf, url))
    has_application = any(x in evidence for x in RECRUITMENT_SIGNALS)
    has_role = any(x in t for x in ROLE_SIGNALS)
    has_document = bool(job.get('notification_pdf')) or pdf.endswith('.pdf') or '/document' in pdf or 'viewpdf' in pdf

    if not (has_application or (has_role and has_document)):
        return False

    # Do not revive clearly old advertisements unless the record has a future
    # application deadline. This blocks old 2024/2025 pages that are merely
    # still present on government sites.
    years = [int(y) for y in re.findall(r'\b(20\d{2})\b', title)]
    if years and max(years) < date.today().year:
        d = deadline(job)
        if not d or d < date.today():
            return False

    # Reject obvious page/navigation fragments.
    if any(x in t for x in (
        'download notification', 'download guidelines', 'apply links',
        'vacancy position', 'recruitment/admission', 'application link',
        'search in notices', 'login', 'register'
    )):
        return False

    return True


def candidate_score(job):
    t = str(job.get('title') or '').casefold()
    d = str(job.get('description') or '').casefold()
    pdf = str(job.get('notification_pdf') or '').casefold()
    score = 0
    for x in ('applications are invited', 'apply online', 'online application', 'call for applications', 'आवेदन आमंत्रित'):
        if x in t or x in d:
            score += 20
    for x in ('recruitment', 'vacancy', 'advertisement', 'engagement of', 'apprentice', 'recruitment of'):
        if x in t:
            score += 10
    if any(x in t for x in ROLE_SIGNALS):
        score += 8
    if pdf or pdf.endswith('.pdf'):
        score += 8
    dline = deadline(job)
    if dline:
        if dline >= date.today():
            score += 18
        else:
            score -= 50
    return score


def load_arch():
    try:
        return json.loads(ARCH.read_text(encoding='utf8')) if ARCH.exists() else []
    except Exception:
        return []


def save_arch(items):
    ARCH.parent.mkdir(parents=True, exist_ok=True)
    ARCH.write_text(json.dumps(unique(items), ensure_ascii=False, indent=2), encoding='utf8')


def main():
    try:
        log.info('Education Update Hub | FINAL AI PUBLISHER | QUALITY MODE')
        sources = SourceManager().get_html_sources()
        raw, failed = norm(scrape_compat(sources))
        parsed = parse_jobs(raw)
        log.info('Links=%d FailedSources=%d Parsed=%d', len(raw), len(failed), len(parsed))
        if not parsed:
            return

        old = unique(load_jobs())
        archive = load_arch()
        known = unique(old + archive)
        known_keys = {stable_key(j) for j in known}

        # IMPORTANT: use the current parsed feed for AI candidate discovery.
        # The optimizer treats changed/updated old records as "fresh", which
        # previously flooded the AI pool with old notices.
        pool = []
        for j in parsed:
            k = stable_key(j)
            if not k or k in known_keys or not ai_candidate(j):
                continue
            pool.append(j)

        pool = unique(sorted(pool, key=candidate_score, reverse=True))[:CANDIDATE_POOL]
        log.info(
            'NEW POST SELECTION | Existing=%d | Archived=%d | Parsed=%d | AIEligible=%d | Target=%d',
            len(old), len(archive), len(parsed), len(pool), MAX_AI
        )

        from ai_editor import enrich
        made = []
        for raw_job in pool:
            if len(made) >= MAX_AI:
                break
            try:
                j = enrich(dict(raw_job))
                j['ai_generated'] = True
                j['site_published_at'] = datetime.now().strftime('%Y-%m-%d')
                j['status'], j['is_expired'] = status(j)
                made.append(j)
                log.info('AI OK | %s | %s', j.get('title'), j.get('category'))
            except RuntimeError as exc:
                if str(exc) == 'OPENROUTER_RATE_LIMIT':
                    log.error('OpenRouter 429 -> STOP AI WITHOUT FALLBACK')
                    break
                log.warning('AI skipped: %s | %s', raw_job.get('title'), exc)
            except Exception:
                log.exception('AI failed: %s', raw_job.get('title'))

        if not made and not old:
            return

        live = unique(old + made)
        archive = unique(archive)
        still = []
        for j in live:
            j['status'], j['is_expired'] = status(j)
            if j['is_expired']:
                archive.append(j)
            else:
                still.append(j)

        archive = unique(archive)
        for j in archive:
            j['status'] = 'Application Closed'
            j['is_expired'] = True

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

        log.info('DONE | Live=%d Archived=%d NewAI=%d Target=%d', len(still), len(archive), len(made), MAX_AI)

    except Exception:
        log.exception('Fatal Error')
        sys.exit(1)


if __name__ == '__main__':
    main()
