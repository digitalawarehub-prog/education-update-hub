import json, logging, os, re, inspect
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("EUH_FINAL")

MAX_AI = max(1, int(os.getenv("MAX_AI_POSTS_PER_RUN", "5")))
CANDIDATE_MULTIPLIER = 10
ROOT = Path(__file__).resolve().parent.parent
ARCH = ROOT / "database" / "archive.json"


def norm(x):
    if isinstance(x, tuple):
        return (x[0] or [], x[1] or [])
    return (x or [], [])


def scrape_compat(sources):
    params = inspect.signature(scrape_all_sources).parameters
    if "workers" in params:
        return scrape_all_sources(sources, workers=10)
    if "max_workers" in params:
        return scrape_all_sources(sources, max_workers=10)
    return scrape_all_sources(sources)


def text_key(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).strip()


def identity(job):
    # Prefer source URL/job id. Fall back to normalized title + source.
    for value in (job.get("job_id"), job.get("url")):
        v = text_key(value)
        if v:
            return ("stable", v)
    title = text_key(job.get("title"))
    source = text_key(job.get("source") or job.get("department"))
    return ("title", title, source)


def unique(jobs):
    out, seen = [], set()
    for job in jobs or []:
        k = identity(job)
        if k in seen:
            continue
        seen.add(k)
        out.append(job)
    return out


def load_archive():
    try:
        if not ARCH.exists():
            return []
        data = json.loads(ARCH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        log.exception("Unable to read archive.json")
        return []


def save_archive(jobs):
    ARCH.parent.mkdir(parents=True, exist_ok=True)
    ARCH.write_text(
        json.dumps(unique(jobs), ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2,
    "mar": 3, "march": 3, "apr": 4, "april": 4, "may": 5,
    "jun": 6, "june": 6, "jul": 7, "july": 7, "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9, "oct": 10, "october": 10,
    "nov": 11, "november": 11, "dec": 12, "december": 12,
}


def parse_date(value):
    s = re.sub(r"\s+", " ", str(value or "").strip())
    if not s:
        return None

    formats = (
        "%Y-%m-%d", "%Y/%m/%d",
        "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y",
        "%d %B %Y", "%d %b %Y",
        "%B %d, %Y", "%b %d, %Y",
    )
    for fmt in formats:
        try:
            return datetime.strptime(s[:40], fmt).date()
        except ValueError:
            pass

    # ISO / numeric dates embedded in longer text.
    m = re.search(r"\b(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})\b", s)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass

    m = re.search(r"\b(\d{1,2})[-/.](\d{1,2})[-/.](20\d{2})\b", s)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            pass

    m = re.search(r"\b(\d{1,2})\s+([A-Za-z]+)\.?\s+(20\d{2})\b", s, re.I)
    if m and m.group(2).lower() in MONTHS:
        try:
            return date(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1)))
        except ValueError:
            pass

    m = re.search(r"\b([A-Za-z]+)\.?\s+(\d{1,2}),?\s+(20\d{2})\b", s, re.I)
    if m and m.group(1).lower() in MONTHS:
        try:
            return date(int(m.group(3)), MONTHS[m.group(1).lower()], int(m.group(2)))
        except ValueError:
            pass

    return None


def application_deadline(job):
    fields = (
        "last_date", "deadline", "application_last_date",
        "last_date_to_apply", "application_deadline", "closing_date"
    )
    for field in fields:
        d = parse_date(job.get(field))
        if d:
            return d

    text = " ".join(
        str(job.get(k, ""))
        for k in ("title", "description", "content", "summary", "notification_text")
    )

    patterns = (
        r"(?:last\s*date(?:\s*to\s*apply)?|application\s*(?:last\s*)?date|"
        r"application\s*deadline|closing\s*date|registration\s*(?:last\s*)?date|"
        r"apply\s*(?:online\s*)?(?:till|by|before))\s*[:\-–]?\s*([^|<;\n]{3,80})",
        r"(?:अंतिम\s*तिथि|अंतिम\s*तारीख|आवेदन\s*की\s*अंतिम\s*तिथि|"
        r"आवेदन\s*की\s*अंतिम\s*तारीख)\s*[:\-–]?\s*([^|<;\n]{3,80})",
    )
    for pattern in patterns:
        m = re.search(pattern, text, re.I)
        if m:
            d = parse_date(m.group(1))
            if d:
                return d
    return None


def refresh_status(job):
    d = application_deadline(job)
    expired = bool(d and d < date.today())
    job["status"] = "Application Closed" if expired else "Active"
    job["is_expired"] = expired
    if d and not job.get("last_date"):
        job["last_date"] = d.strftime("%d-%m-%Y")
    return job


def main():
    log.info("Education Update Hub | FINAL ACCUMULATING PUBLISHER")

    sources = SourceManager().get_html_sources()
    raw, failed = norm(scrape_compat(sources))
    parsed = unique(parse_jobs(raw))
    log.info("Links=%d FailedSources=%d Parsed=%d", len(raw), len(failed), len(parsed))

    old_live = unique(load_jobs())
    old_archive = unique(load_archive())

    # A source that is already live OR archived is never considered a new post.
    known = {identity(j) for j in (old_live + old_archive)}

    try:
        result = run_optimizer(old_live, parsed)
        optimizer_candidates = (
            result.get("new_jobs", []) if isinstance(result, dict) else []
        )
    except Exception:
        log.exception("Optimizer failed; falling back to parsed source candidates")
        optimizer_candidates = []

    # Optimizer output first, raw parsed candidates second. This lets us keep
    # trying when the optimizer returns too few unique items.
    candidate_pool = unique(list(optimizer_candidates) + list(parsed))
    fresh = [j for j in candidate_pool if identity(j) not in known]

    # Try many candidates so a few bad/duplicate/failed AI attempts don't reduce
    # a normal run below the requested 5 posts.
    fresh = fresh[: max(MAX_AI * CANDIDATE_MULTIPLIER, MAX_AI)]
    log.info(
        "NEW CANDIDATES | Known=%d FreshCandidates=%d Target=%d",
        len(known), len(fresh), MAX_AI
    )

    from ai_editor import enrich

    made = []
    made_ids = set()

    for raw_job in fresh:
        if len(made) >= MAX_AI:
            break

        try:
            j = enrich(dict(raw_job))
            if not isinstance(j, dict):
                raise RuntimeError("AI returned invalid post object")

            j["ai_generated"] = True
            j["site_published_at"] = datetime.now().strftime("%Y-%m-%d")

            # IMPORTANT: keep source identity even if AI rewrites the title.
            for field in ("job_id", "url", "source", "department", "category"):
                if not j.get(field) and raw_job.get(field):
                    j[field] = raw_job[field]

            refresh_status(j)

            kid = identity(j)
            if kid in known or kid in made_ids:
                log.warning("DUPLICATE AI OUTPUT SKIPPED | %s", j.get("title"))
                continue

            made.append(j)
            made_ids.add(kid)
            log.info(
                "AI OK | %d/%d | %s | %s",
                len(made), MAX_AI, j.get("title"), j.get("category")
            )

        except RuntimeError as exc:
            log.warning("AI runtime failed for %s: %s", raw_job.get("title"), exc)
        except Exception:
            log.exception("AI failed: %s", raw_job.get("title"))

    # Preserve every existing live post; append only the new AI posts.
    live = unique(old_live + made)
    archive = unique(old_archive)

    still_live = []
    moved = 0

    for job in live:
        refresh_status(job)
        if job.get("is_expired"):
            archive.append(job)
            moved += 1
        else:
            still_live.append(job)

    archive = unique(archive)
    for job in archive:
        job["status"] = "Application Closed"
        job["is_expired"] = True

    save_jobs(still_live)
    save_archive(archive)

    # Regenerate the site from the COMPLETE datasets so accumulated posts are
    # not deleted when the latest run publishes only five new items.
    clean_output_directory()
    all_public = unique(still_live + archive)
    generate_all(all_public, category_jobs=still_live)
    category_generator.build_categories(still_live)
    homepage.run(still_live)

    from archive_generator import build_archive
    build_archive(archive)

    try:
        update_sitemap(all_public)
    except TypeError:
        update_sitemap()

    log.info(
        "DONE | Live=%d Archived=%d NewAI=%d ArchivedThisRun=%d Target=%d",
        len(still_live), len(archive), len(made), moved, MAX_AI
    )

    if len(made) < MAX_AI:
        log.warning(
            "TARGET NOT REACHED | created=%d target=%d | "
            "No more unique candidates or AI responses available.",
            len(made), MAX_AI
        )


if __name__ == "__main__":
    main()
