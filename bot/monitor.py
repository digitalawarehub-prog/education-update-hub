import logging
import re
import sys

from sources_manager import SourceManager
from scraper import scrape_all_sources
from parser import parse_jobs
from optimizer import run_optimizer
from database import load_jobs, save_jobs
from html_generator import generate_all
import homepage
from sitemap_generator import update_sitemap
from adapters.base import BaseAdapter
from detail_quality import is_bad_detail

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


def _normalise_scrape_result(result):
    """Accept both list and (jobs, failed_sources) scraper contracts."""
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
        else:
            # Backward compatibility with older html_generator versions.
            logger.info("Generated : %s", result)



def _detail_bad(value, field):
    """Single quality gate shared with the PDF/HTML extraction layer."""
    return is_bad_detail(value, field)



def _needs_detail_repair(job):
    """Decide whether an existing recruitment record needs PDF re-extraction."""
    category = str(job.get("category", "") or "").strip().casefold()
    post_type = str(job.get("post_type", "") or "").strip().casefold()
    title = str(job.get("title", "") or "").lower()

    if category not in {"recruitment", "latest jobs", "job", "jobs"} and post_type not in {"recruitment", "latest jobs"}:
        return False

    if any(x in title for x in (
        "admit card", "admit-card", "hall ticket", "call letter",
        "answer key", "answer-key", "result", "syllabus", "scholarship"
    )):
        return False

    # Do not spend the workflow budget repairing very old archive records.
    # Current/recent records are the ones that need accurate live details.
    current_year = "2026"
    title_year = re.search(r"\b(20\d{2})\b", title)
    publish = str(job.get("publish_date") or "")[:10]
    recent = False
    if publish:
        try:
            from datetime import date, datetime
            recent = (date.today() - datetime.strptime(publish, "%Y-%m-%d").date()).days <= 120
        except Exception:
            recent = False
    if title_year and title_year.group(1) != current_year and not recent:
        return False

    # Any malformed value is enough to trigger a repair. This catches the
    # exact fragments seen in the current site: "(As on 31", "(As on 01",
    # "c. At the time of Main", single-letter qualifications, etc.
    fields = (
        "vacancy", "qualification", "salary", "age_limit",
        "application_fee", "selection_process", "exam_date",
        "application_start_date", "last_date"
    )
    malformed = any(_detail_bad(job.get(k), k) for k in fields)

    # A known notification PDF is the preferred repair path. If there is no
    # PDF, only attempt recent/current records because page-level extraction
    # is less reliable and can be expensive.
    if malformed and (job.get("notification_pdf") or recent or (title_year and title_year.group(1) == current_year)):
        return True

    if job.get("notification_pdf") and not job.get("notification_text"):
        return True

    return False


def normalize_post_types(jobs):
    """Normalize post type from title before enrichment/HTML generation.

    This is deliberately title-first: notification PDFs contain words such as
    call letter/result/exam even inside recruitment advertisements.
    """
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

def repair_missing_details(jobs):
    """Repair legacy database records before HTML is regenerated.

    Existing posts were historically saved with placeholders and were never
    passed through the PDF/OCR enrichment stage again. Re-enrich only those
    recruitment records so every workflow run can progressively repair old
    posts without re-downloading every result/admit-card record.
    """
    adapter = BaseAdapter()
    repaired = 0
    attempted = 0
    for job in jobs or []:
        if not _needs_detail_repair(job):
            continue
        attempted += 1
        before = {k: str(job.get(k, "") or "").strip() for k in (
            "vacancy", "qualification", "salary", "age_limit", "application_fee",
            "selection_process", "exam_date", "application_start_date", "last_date",
            "notification_date", "notification_pdf", "official_notification_pdf"
        )}
        try:
            enriched = adapter.enrich_job(dict(job))
            # Keep the canonical job object while accepting only useful values.
            for key, value in enriched.items():
                if key in {"title", "url", "job_id", "category", "post_type", "department"}:
                    continue
                if value is not None:
                    job[key] = value
            after = {k: str(job.get(k, "") or "").strip() for k in before}
            if after != before:
                repaired += 1
                logger.info(
                    "LEGACY DETAIL REPAIRED | %s | vacancy=%s | qualification=%s | salary=%s | last_date=%s | notification_date=%s",
                    job.get("title", ""), job.get("vacancy", ""), job.get("qualification", ""),
                    job.get("salary", ""), job.get("last_date", ""), job.get("notification_date", "")
                )
        except Exception:
            logger.exception("Legacy detail repair failed: %s", job.get("title", ""))
    logger.info("LEGACY DETAIL REPAIR SUMMARY | Attempted=%d | Repaired=%d", attempted, repaired)
    return jobs

def main():
    try:
        logger.info("=" * 60)
        logger.info("Education Update Hub Auto Publisher Started")
        logger.info("=" * 60)

        manager = SourceManager()
        logger.info("Total Sources : %d", manager.count())
        sources = manager.get_html_sources()
        logger.info("HTML Sources : %d", len(sources))

        if not sources:
            logger.warning("No HTML sources found.")
            return

        # --------------------------------------------------
        # 1. Scrape
        # --------------------------------------------------
        logger.info("Scraping Websites...")
        all_jobs, failed_sources = _normalise_scrape_result(
            scrape_all_sources(sources)
        )
        logger.info("Links Found : %d", len(all_jobs))
        if failed_sources:
            logger.warning("Failed Sources : %d", len(failed_sources))

        if not all_jobs:
            logger.info("No links found.")
            return

        # --------------------------------------------------
        # 2. Parse
        # --------------------------------------------------
        logger.info("Parsing Jobs...")
        parsed_jobs = parse_jobs(all_jobs)
        logger.info("Parsed Jobs : %d", len(parsed_jobs))
        if not parsed_jobs:
            logger.warning("No valid jobs after parsing.")
            return

        # --------------------------------------------------
        # 3. Optimizer + persistent database
        # --------------------------------------------------
        logger.info("Optimizing Jobs...")
        old_jobs = load_jobs()
        result = run_optimizer(old_jobs, parsed_jobs)
        merged_jobs = result.get("jobs", [])
        new_jobs = result.get("new_jobs", [])

        # Normalize content type before any PDF/detail repair. This prevents a
        # Call Letter/Admit Card/Result record from inheriting recruitment data.
        merged_jobs = normalize_post_types(merged_jobs)

        # IMPORTANT: repair legacy recruitment records before HTML generation.
        # Older records may contain placeholders even though the source PDF is
        # now available; regenerating HTML without this step simply reproduces
        # the same empty table forever.
        merged_jobs = repair_missing_details(merged_jobs)

        logger.info("Old Jobs    : %d", len(old_jobs))
        logger.info("Merged Jobs : %d", len(merged_jobs))
        logger.info("New Jobs    : %d", len(new_jobs))

        if not merged_jobs:
            logger.warning("Optimizer returned no merged jobs.")
            return

        # Save BEFORE HTML/search/homepage so every downstream module
        # sees the same canonical dataset.
        save_jobs(merged_jobs)
        logger.info("Database Saved : %d jobs", len(merged_jobs))

        # --------------------------------------------------
        # 4. Reconcile ALL active posts.
        # The database can contain old records whose generated HTML was
        # deleted or whose filename changed. Generating only new jobs was
        # the main source of 404s and stale category links.
        # --------------------------------------------------
        logger.info("Reconciling generated posts from complete database...")
        summary = generate_all(merged_jobs, category_jobs=merged_jobs)
        _log_generation(summary)
        # generate_all updates html_file/slug on the in-memory records.
        # Downstream pages must never link to a post that does not exist.
        from url_utils import post_exists
        valid_jobs = [job for job in merged_jobs if post_exists(job)]
        logger.info("POST LINK VALIDATION | Database=%d | Local Posts=%d | Missing=%d", len(merged_jobs), len(valid_jobs), len(merged_jobs)-len(valid_jobs))
        if not valid_jobs:
            raise RuntimeError("No generated posts available after HTML generation")
        merged_jobs = valid_jobs
        save_jobs(merged_jobs)
        logger.info("Database Re-saved with canonical post URLs : %d jobs", len(merged_jobs))

        from category_generator import build_categories
        build_categories(merged_jobs)

        # --------------------------------------------------
        # 5. Homepage + header + search index from complete DB
        # --------------------------------------------------
        logger.info("Updating Homepage + Header + Search...")
        if homepage.run(merged_jobs):
            logger.info("Homepage + Header + Search Updated Successfully.")
        else:
            raise RuntimeError("Homepage generation returned False")

        # --------------------------------------------------
        # 6. Sitemap
        # --------------------------------------------------
        logger.info("Updating Sitemap...")
        try:
            update_sitemap(merged_jobs)
            logger.info("Sitemap Updated Successfully.")
        except TypeError:
            # Compatibility with sitemap generators that read database/jobs.json.
            update_sitemap()
            logger.info("Sitemap Updated Successfully (database mode).")

        logger.info("=" * 60)
        logger.info("Automation Completed Successfully")
        logger.info("Total Jobs : %d", len(merged_jobs))
        logger.info("New Jobs   : %d", len(new_jobs))
        logger.info("=" * 60)

    except Exception:
        logger.exception("Fatal Error")
        sys.exit(1)


if __name__ == "__main__":
    main()
