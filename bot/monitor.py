import logging, os, sys, inspect, json, re
from datetime import datetime, date
from pathlib import Path
from sources_manager import SourceManager
from scraper import scrape_all_sources
from parser import parse_jobs
from optimizer import run_optimizer, is_expired as optimizer_is_expired
from database import load_jobs, save_jobs
from html_generator import generate_all, clean_output_directory
import homepage, category_generator
from sitemap_generator import update_sitemap

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
log = logging.getLogger('EUH_FINAL')

MAX_AI = max(1, int(os.getenv('MAX_AI_POSTS_PER_RUN', '5')))
CANDIDATES = max(20, MAX_AI * 4)
ROOT = Path(__file__).resolve().parent.parent
ARCH = ROOT / 'database' / 'archive.json'


def norm(x):
    return (x[0] or [], x[1] or []) if isinstance(x, tuple) else (x or [], [])


def scrape_compat(s):
    p = inspect.signature(scrape_all_sources).parameters
    if 'workers' in p:
        return scrape_all_sources(s, workers=10)
    if 'max_workers' in p:
        return scrape_all_sources(s, max_workers=10)
    return scrape_all_sources(s)


def clean_key_value(v):
    return re.sub(r'\s+', ' ', str(v or '').strip()).casefold()


def key(j):
    # Prefer canonical URL/job_id, but title is also used for duplicate protection.
    return clean_key_value(j.get('job_id') or j.get('url') or j.get('title'))


def identity_keys(j):
    vals = [j.get('job_id'), j.get('url'), j.get('title')]
    return {clean_key_value(v) for v in vals if clean_key_value(v)}


def unique(a):
    out, seen = [], set()
    for j in a or []:
        if not isinstance(j, dict):
            continue
        ids = identity_keys(j)
        marker = next(iter(sorted(ids)), '') if ids else ''
        if marker and marker not in seen:
            seen.add(marker)
            out.append(j)
    return out


def pdate(v):
    s = str(v or '').strip()
    formats = ('%d-%m-%Y', '%d/%m/%Y', '%d.%m.%Y', '%Y-%m-%d', '%d %B %Y', '%d %b %Y')
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    m = re.search(r'\b(\d{1,2})\s+([A-Za-z]+)\s+(20\d{2})\b', s)
    if m:
        months = {'jan':1,'january':1,'feb':2,'february':2,'mar':3,'march':3,'apr':4,'april':4,'may':5,
                  'jun':6,'june':6,'jul':7,'july':7,'aug':8,'august':8,'sep':9,'sept':9,'september':9,
                  'oct':10,'october':10,'nov':11,'november':11,'dec':12,'december':12}
        month = months.get(m.group(2).casefold())
        if month:
            try:
                return date(int(m.group(3)), month, int(m.group(1)))
            except ValueError:
                pass
    return None


def deadline(j):
    for k in ('last_date','deadline','application_last_date','last_date_to_apply','closing_date','application_deadline'):
        d = pdate(j.get(k))
        if d:
            return d
    return None


def status(j):
    """Return the live/archive status for a job.

    This function is intentionally defined in monitor.py so the publisher never
    depends on an optional hotfix symbol being injected at runtime.
    """
    try:
        expired = bool(optimizer_is_expired(j))
    except Exception:
        d = deadline(j)
        expired = bool(d and d < date.today())
    return ('Application Closed', True) if expired else ('Active', False)


def load_arch():
    try:
        data = json.loads(ARCH.read_text(encoding='utf-8')) if ARCH.exists() else []
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_arch(a):
    ARCH.parent.mkdir(parents=True, exist_ok=True)
    ARCH.write_text(json.dumps(unique(a), ensure_ascii=False, indent=2), encoding='utf-8')


def already_exists(job, jobs):
    ids = identity_keys(job)
    if not ids:
        return True
    for old in jobs:
        if ids & identity_keys(old):
            return True
    return False


def main():
    try:
        log.info('Education Update Hub | FINAL AI PUBLISHER')
        sources = SourceManager().get_html_sources()
        raw, failed = norm(scrape_compat(sources))
        parsed = parse_jobs(raw)
        log.info('Links=%d FailedSources=%d Parsed=%d', len(raw), len(failed), len(parsed))
        if not parsed:
            log.warning('No parsed jobs; nothing to publish')
            return

        old = unique(load_jobs())
        archive = load_arch()

        # Keep all existing publisher posts. Do not discard live history between runs.
        existing = unique(old + archive)
        result = run_optimizer(old, parsed)
        optimizer_fresh = unique(result.get('new_jobs', []) if isinstance(result, dict) else [])

        # The optimizer also reports changed records as "fresh". For a 5-new-post
        # run we must exclude anything already present in live/archive by URL/title/job_id.
        new = []
        for job in optimizer_fresh:
            if already_exists(job, existing):
                continue
            new.append(job)
            if len(new) >= CANDIDATES:
                break

        # If optimizer's changed-job filter consumed the candidates, fall back to
        # the merged/current parsed records while still excluding all existing IDs.
        if len(new) < MAX_AI:
            pool = []
            merged = result.get('jobs', []) if isinstance(result, dict) else []
            pool.extend(merged)
            pool.extend(parsed)
            for job in pool:
                if not isinstance(job, dict) or already_exists(job, existing):
                    continue
                if not job.get('title') or not job.get('url'):
                    continue
                if any(identity_keys(job) == identity_keys(x) for x in new):
                    continue
                try:
                    if optimizer_is_expired(job):
                        continue
                except Exception:
                    if status(job)[1]:
                        continue
                new.append(job)
                if len(new) >= CANDIDATES:
                    break

        log.info('NEW POST SELECTION | ExistingLive=%d | Archived=%d | Candidates=%d | Target=%d',
                 len(old), len(archive), len(new), MAX_AI)

        from ai_editor import enrich
        made = []
        for raw_job in new:
            if len(made) >= MAX_AI:
                break
            try:
                j = enrich(dict(raw_job))
                if not isinstance(j, dict) or not j.get('title') or not j.get('url'):
                    raise ValueError('AI returned incomplete job')
                j['ai_generated'] = True
                j['site_published_at'] = datetime.now().strftime('%Y-%m-%d')
                j['status'], j['is_expired'] = status(j)
                if j['is_expired']:
                    log.info('SKIP CLOSED NEW POST | %s', j.get('title'))
                    continue
                made.append(j)
                log.info('AI OK | %d/%d | %s | %s', len(made), MAX_AI, j.get('title'), j.get('category'))
            except RuntimeError as e:
                if 'OPENROUTER_RATE_LIMIT' in str(e) or '429' in str(e):
                    log.error('OpenRouter rate limit; stopping AI generation without fake fallback')
                    break
                log.warning('AI skipped: %s | %s', raw_job.get('title'), e)
            except Exception as e:
                log.warning('AI failed: %s | %s', raw_job.get('title'), e)

        # Preserve all old live posts and append genuinely new AI posts.
        live = unique(old + made)
        still = []
        archived_this_run = 0
        archive_by_ids = {}
        for a in archive:
            for ident in identity_keys(a):
                archive_by_ids[ident] = a

        for j in live:
            j['status'], j['is_expired'] = status(j)
            if j['is_expired']:
                archived_this_run += 1
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

        log.info('DONE | Live=%d Archived=%d NewAI=%d ArchivedThisRun=%d Target=%d',
                 len(still), len(archive), len(made), archived_this_run, MAX_AI)
    except Exception:
        log.exception('Fatal Error')
        sys.exit(1)


if __name__ == '__main__':
    main()
