import logging
import sys
import re
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from time import monotonic

from sources_manager import SourceManager
from scraper import scrape_all_sources
from parser import parse_jobs
from optimizer import run_optimizer
from database import load_jobs, save_jobs
from html_generator import generate_all
import homepage
from sitemap_generator import update_sitemap
from adapters.base import BaseAdapter

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# These limits are deliberately small. The workflow runs every 30 minutes, so
# repairs are rotated across runs instead of trying to enrich 70+ records in one
# run. This is the main protection against the 55-minute timeout seen previously.
DETAIL_ENRICH_LIMIT = 12
LEGACY_REPAIR_LIMIT = 8
DETAIL_WORKERS = 3
DETAIL_BUDGET_SECONDS = 22 * 60
REPAIR_STATE_FILE = Path(__file__).resolve().parent / "generated" / "detail_repair_state.json"


def _read_repair_offset(total):
    if total <= 0:
        return 0
    try:
        data = json.loads(REPAIR_STATE_FILE.read_text(encoding="utf-8"))
        return int(data.get("offset", 0)) % total
    except Exception:
        return 0


def _write_repair_offset(offset):
    try:
        REPAIR_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        REPAIR_STATE_FILE.write_text(json.dumps({"offset": int(offset)}, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        logger.exception("Unable to save detail repair cursor")


def _enrich_one(job):
    adapter = BaseAdapter()
    before = {k: str(job.get(k, "") or "").strip() for k in (
        "vacancy", "qualification", "salary", "age_limit", "application_fee",
        "selection_process", "exam_date", "application_start_date", "last_date",
        "notification_date", "notification_pdf", "official_notification_pdf"
    )}
    try:
        adapter.enrich_job(job)
        after = {k: str(job.get(k, "") or "").strip() for k in before}
        return job, before != after, None
    except Exception as exc:
        return job, False, exc


def _bounded_enrich(jobs, limit, label, deadline):
    if not jobs or monotonic() >= deadline:
        return jobs
    selected = list(jobs)[:max(0, int(limit))]
    logger.info("%s | Candidates=%d | Processing=%d | Workers=%d", label, len(jobs), len(selected), DETAIL_WORKERS)
    if not selected:
        return jobs

    with ThreadPoolExecutor(max_workers=DETAIL_WORKERS) as executor:
        futures = {executor.submit(_enrich_one, job): job for job in selected}
        for future in as_completed(futures):
            if monotonic() >= deadline:
                logger.warning("%s | Detail budget reached; remaining jobs will rotate to the next run.", label)
                break
            job = futures[future]
            try:
                result_job, changed, exc = future.result()
                if exc:
                    logger.warning("%s failed: %s | %s", label, job.get("title", ""), exc.__class__.__name__)
                elif changed:
                    logger.info("%s OK | %s | vacancy=%s | qualification=%s | salary=%s | selection=%s | last_date=%s | pdf=%s",
                                label, result_job.get("title", ""), result_job.get("vacancy", ""),
                                result_job.get("qualification", ""), result_job.get("salary", ""),
                                result_job.get("selection_process", ""), result_job.get("last_date", ""),
                                bool(result_job.get("notification_pdf")))
            except Exception:
                logger.exception("%s result handling failed: %s", label, job.get("title", ""))
    return jobs


def _normalise_scrape_result(result):
    if isinstance(result, tuple):
        jobs = result[0] if result else []
        failed = result[1] if len(result) > 1 else []
        return jobs or [], failed or []
    return result or [], []


def _log_generation(summary):
    summary = summary if isinstance(summary, dict) else {}
    logger.info("Generation Summary")
    logger.info("Generated : %d", int(summary.get("success", 0) or 0))
    logger.info("Failed    : %d", int(summary.get("failed", 0) or 0))
    logger.info("Total     : %d", int(summary.get("total", 0) or 0))
    for result in summary.get("results", []):
        if isinstance(result, dict):
            if result.get("success"):
                logger.info("Generated : %s", result.get("file", ""))
            else:
                logger.error("Failed : %s", result.get("title", "Unknown"))
                logger.error("%s", result.get("error", "Unknown error"))


def _detail_bad(value, field):
    s = str(value or "").strip().casefold()
    if s in {"", "not mentioned", "check official notification", "check notification", "as per rules", "not available", "उपलब्ध नहीं", "आधिकारिक अधिसूचना देखें", ".", "none", "null"}:
        return True
    if field == "vacancy" and not re.search(r"\b\d{1,6}\b", s):
        return True
    if field == "qualification" and ("official notification" in s or "आधिकारिक अधिसूचना" in s or len(s) < 8):
        return True
    if field == "salary" and ("official notification" in s or "पदों की संख्या" in s or not re.search(r"(?:₹|rs\.?|inr|pay|level|salary|remuneration|वेतन|मानदेय|\d[\d,]*\s*[-–]\s*\d)", s, re.I)):
        return True
    if field == "selection_process" and any(x in s for x in ("के संबंध में जानकारी", "के लिए आयोग की वेबसाइट", "visit the website", "click here")):
        return True
    if field == "age_limit" and not re.search(r"(?:age|वर्ष|years?|year|आयु|उम्र|\b\d{1,2}\s*[-–]\s*\d{1,2}\b)", s, re.I):
        return True
    if field == "application_fee" and (len(s) > 240 or (not re.search(r"\d", s) and not re.search(r"\b(?:free|no\s*fee|nil|शुल्क\s*नहीं|निःशुल्क)\b", s, re.I))):
        return True
    return False


def _needs_detail_repair(job):
    category = str(job.get("category", "") or "").strip().casefold()
    post_type = str(job.get("post_type", "") or "").strip().casefold()
    title = str(job.get("title", "") or "").lower()
    if category not in {"recruitment", "latest jobs", "job", "jobs"} and post_type not in {"recruitment", "latest jobs"}:
        return False
    if any(x in title for x in ("admit card", "admit-card", "hall ticket", "call letter", "answer key", "answer-key", "result", "syllabus", "scholarship")):
        return False
    return any(_detail_bad(job.get(k), k) for k in ("vacancy", "qualification", "salary", "age_limit", "application_fee", "selection_process", "last_date"))


def normalize_post_types(jobs):
    adapter = BaseAdapter()
    cleared = 0
    for job in jobs or []:
        ptype = adapter.detect_post_type(job.get("title", ""), job.get("url", ""), job.get("category", ""))
        job["post_type"] = ptype
        if ptype != "recruitment":
            for key in ("vacancy", "qualification", "salary", "age_limit", "application_fee", "selection_process"):
                if job.get(key):
                    job[key] = ""
                    cleared += 1
    logger.info("POST TYPE NORMALIZATION | NonRecruitmentCleared=%d", cleared)
    return jobs


def repair_missing_details(jobs, deadline):
    candidates = [job for job in jobs or [] if _needs_detail_repair(job)]
    if not candidates or monotonic() >= deadline:
        logger.info("LEGACY DETAIL REPAIR SUMMARY | Candidates=%d", len(candidates))
        return jobs
    offset = _read_repair_offset(len(candidates))
    ordered = candidates[offset:] + candidates[:offset]
    batch = ordered[:LEGACY_REPAIR_LIMIT]
    before_count = len(batch)
    _bounded_enrich(batch, before_count, "LEGACY DETAIL REPAIR", deadline)
    nxt = (offset + len(batch)) % len(candidates)
    _write_repair_offset(nxt)
    logger.info("LEGACY DETAIL REPAIR SUMMARY | Candidates=%d | Attempted=%d | NextOffset=%d", len(candidates), len(batch), nxt)
    return jobs


def main():
    started = monotonic()
    deadline = started + DETAIL_BUDGET_SECONDS
    try:
        logger.info("=" * 60)
        logger.info("Education Update Hub Auto Publisher Started")
        logger.info("Detail budget : %d seconds", DETAIL_BUDGET_SECONDS)
        logger.info("=" * 60)

        manager = SourceManager()
        logger.info("Total Sources : %d", manager.count())
        sources = manager.get_html_sources()
        logger.info("HTML Sources : %d", len(sources))
        if not sources:
            logger.warning("No HTML sources found.")
            return

        logger.info("Scraping Websites...")
        all_jobs, failed_sources = _normalise_scrape_result(scrape_all_sources(sources))
        logger.info("Links Found : %d", len(all_jobs))
        if failed_sources:
            logger.warning("Failed Sources : %d", len(failed_sources))
        if not all_jobs:
            logger.info("No links found.")
            return

        logger.info("Parsing Jobs...")
        parsed_jobs = parse_jobs(all_jobs)
        logger.info("Parsed Jobs : %d", len(parsed_jobs))
        parsed_jobs = _bounded_enrich(parsed_jobs, DETAIL_ENRICH_LIMIT, "NEW DETAIL EXTRACTION", deadline)
        if not parsed_jobs:
            logger.warning("No valid jobs after parsing.")
            return

        logger.info("Optimizing Jobs...")
        old_jobs = load_jobs()
        result = run_optimizer(old_jobs, parsed_jobs)
        merged_jobs = normalize_post_types(result.get("jobs", []))
        new_jobs = result.get("new_jobs", [])

        # Rotate old incomplete records across runs instead of repairing all of
        # them in one run. This keeps the site improving continuously without a
        # workflow timeout.
        merged_jobs = repair_missing_details(merged_jobs, deadline)

        logger.info("Old Jobs    : %d", len(old_jobs))
        logger.info("Merged Jobs : %d", len(merged_jobs))
        logger.info("New Jobs    : %d", len(new_jobs))
        if not merged_jobs:
            logger.warning("Optimizer returned no merged jobs.")
            return

        save_jobs(merged_jobs)
        logger.info("Database Saved : %d jobs", len(merged_jobs))

        logger.info("Reconciling generated posts from complete database...")
        summary = generate_all(merged_jobs, category_jobs=merged_jobs)
        _log_generation(summary)

        from url_utils import post_exists
        valid_jobs = [job for job in merged_jobs if post_exists(job)]
        logger.info("POST LINK VALIDATION | Database=%d | Local Posts=%d | Missing=%d", len(merged_jobs), len(valid_jobs), len(merged_jobs) - len(valid_jobs))
        if not valid_jobs:
            raise RuntimeError("No generated posts available after HTML generation")
        merged_jobs = valid_jobs
        save_jobs(merged_jobs)

        from category_generator import build_categories
        build_categories(merged_jobs)

        logger.info("Updating Homepage + Header + Search...")
        if not homepage.run(merged_jobs):
            raise RuntimeError("Homepage generation returned False")

        logger.info("Updating Sitemap...")
        try:
            update_sitemap(merged_jobs)
        except TypeError:
            update_sitemap()

        logger.info("=" * 60)
        logger.info("Automation Completed Successfully")
        logger.info("Total Jobs : %d | New Jobs : %d | Runtime : %.1fs", len(merged_jobs), len(new_jobs), monotonic() - started)
        logger.info("=" * 60)
    except Exception:
        logger.exception("Fatal Error")
        sys.exit(1)


if __name__ == "__main__":
    main()
