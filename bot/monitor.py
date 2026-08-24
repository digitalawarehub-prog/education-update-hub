import logging
import sys
import re
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

from sources_manager import SourceManager
from scraper import scrape_all_sources
from parser import parse_jobs
from optimizer import run_optimizer
from database import load_jobs, save_jobs
from html_generator import generate_all
import homepage
from sitemap_generator import update_sitemap
from adapters.base import BaseAdapter

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
    s = str(value or "").strip().casefold()
    if s in {"", "not mentioned", "check official notification", "check notification", "as per rules", "not available", "उपलब्ध नहीं", "आधिकारिक अधिसूचना देखें", ".", "none", "null"}:
        return True
    if field == "vacancy" and not __import__('re').search(r"\b\d{1,6}\b", s):
        return True
    if field == "qualification" and any(x in s for x in ("certification and work", "slips, etc", "stipulated dates before registering", "official notification")):
        return True
    if field == "salary" and any(x in s for x in ("slips, etc", "as per rules", "official notification")):
        return True
    if field == "application_fee":
        if len(s) > 240 or (not __import__('re').search(r"\d", s) and not __import__('re').search(r"\b(?:free|no\s*fee|nil|शुल्क\s*नहीं|निःशुल्क)\b", s, __import__('re').I)):
            return True
    return False


def _needs_detail_repair(job):
    """Repair recruitment records with missing/garbled details or stale source date."""
    category = str(job.get("category", "") or "").strip().casefold()
    post_type = str(job.get("post_type", "") or "").strip().casefold()
    title = str(job.get("title", "") or "").lower()
    if category not in {"recruitment", "latest jobs", "job", "jobs"} and post_type not in {"recruitment", "latest jobs"}:
        return False
    if any(x in title for x in ("admit card", "admit-card", "hall ticket", "call letter", "answer key", "answer-key", "result", "syllabus", "scholarship")):
        return False
    if any(_detail_bad(job.get(k), k) for k in ("vacancy", "qualification", "salary", "application_fee")):
        return True
    # Re-verify active PDF-backed recruitment records periodically. This catches
    # plausible-looking but wrong values such as vacancy=2 or salary=Rs that
    # cannot be detected by simple empty-field checks. The repair cap prevents a
    # large legacy database from causing another timeout.
    pdf = str(job.get("notification_pdf") or "").casefold()
    title_low = str(job.get("title") or "").casefold()
    if pdf and ("backlog" in pdf or "samplecopy" in pdf or "complete_sample" in pdf):
        if "backlog" not in title_low and "special recruitment drive" not in title_low:
            return True
    if pdf and str(job.get("salary") or "").strip().casefold() in {"rs", "rs.", "₹", "₹50", "rs1", "rs.1"}:
        return True
    if pdf and str(job.get("qualification") or "").strip().casefold() in {"a", "an", "1", "o:- (a)", "o:- (a) 1"}:
        return True
    # If an old record was stamped with the scrape date, give it one chance to
    # recover the real notification date. Do not overwrite a genuine source date.
    publish = str(job.get("publish_date") or "")[:10]
    scraped = str(job.get("scraped_at") or "")[:10]
    if publish and scraped and publish == scraped and not job.get("notification_date"):
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
    candidates = [job for job in (jobs or []) if _needs_detail_repair(job)]
    # Never try to re-download hundreds of old PDFs in one GitHub Actions run.
    # Prioritise records that are still active or have no deadline yet; the rest
    # will be repaired progressively on later 30-minute runs.
    def _priority(job):
        last = str(job.get("last_date") or "").strip().casefold()
        if not last or last in {"check notification", "उपलब्ध नहीं", "आधिकारिक अधिसूचना देखें"}:
            return 0
        try:
            d = BaseAdapter().parse_date(last)
            return 1 if d and d >= __import__('datetime').date.today() else 2
        except Exception:
            return 1
    candidates.sort(key=_priority)
    max_repairs = int(os.getenv("EUH_LEGACY_REPAIR_CAP", "4"))
    if len(candidates) > max_repairs:
        logger.info("LEGACY DETAIL REPAIR CAP | Candidates=%d | ThisRun=%d", len(candidates), max_repairs)
    for job in candidates[:max_repairs]:
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

def _is_recruitment(job):
    p = str(job.get("post_type", "") or "").strip().casefold()
    c = str(job.get("category", "") or "").strip().casefold()
    title = str(job.get("title", "") or "").casefold()
    if p in {"result", "admit card", "answer key", "syllabus", "scholarship", "other"}:
        return False
    if any(x in title for x in ("admit card", "hall ticket", "answer key", "result", "syllabus", "scholarship", "scorecard")):
        return False
    return p in {"recruitment", "job", "jobs", ""} or c in {"recruitment", "latest jobs", "latest job"}


def _deadline_date(value):
    s = str(value or "").strip()
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d", "%d %B %Y", "%d %b %Y"):
        try:
            from datetime import datetime
            return datetime.strptime(s, fmt).date()
        except Exception:
            pass
    return None


def _is_active_recruitment(job):
    if not _is_recruitment(job):
        return False
    d = _deadline_date(job.get("last_date"))
    return d is None or d >= date.today()


def reset_unverified_active_details(jobs):
    """Remove legacy/contaminated recruitment fields before regeneration.

    A wrong value is worse than an empty value. Active records without an
    explicitly verified detail source are cleared so the HTML layer cannot
    display cross-post data such as another recruitment's selection process.
    """
    fields = (
        "vacancy", "qualification", "salary", "age_limit", "application_fee",
        "selection_process", "exam_date", "application_start_date", "last_date",
        "notification_pdf", "official_notification_pdf", "notification_text"
    )
    cleared = 0
    for job in jobs or []:
        if not _is_active_recruitment(job):
            continue
        if bool(job.get("detail_verified")):
            continue
        # Keep source-card dates/apply URLs only when they are independently
        # present; PDF/detail extraction can replace them with authoritative data.
        keep_last = str(job.get("last_date") or "").strip()
        keep_start = str(job.get("application_start_date") or "").strip()
        card_pdf = str(job.get("notification_pdf") or "").strip()
        card_pdf_source = str(job.get("notification_pdf_source") or "").strip().casefold()
        for key in fields:
            if key in {"last_date", "application_start_date"} and (keep_last if key == "last_date" else keep_start):
                continue
            # Preserve an advertisement URL that a source-specific adapter
            # extracted from the exact recruitment card.  Clearing this URL
            # before enrichment was the reason SBI/other card-based portals
            # could lose their only path to the correct PDF.
            if key in {"notification_pdf", "official_notification_pdf"} and card_pdf and card_pdf_source in {"sbi_card", "card", "source_card"}:
                if key == "notification_pdf":
                    continue
            if job.get(key):
                job[key] = ""
                cleared += 1
        job["detail_verified"] = False
        job["detail_source"] = "unverified"
        job["detail_reset"] = True
    logger.info("UNVERIFIED ACTIVE DETAIL RESET | FieldsCleared=%d", cleared)
    return jobs


def _detail_queue(jobs, new_jobs):
    """Queue active recruitment records that need authoritative enrichment."""
    new_ids = {str(j.get("job_id")) for j in (new_jobs or []) if j.get("job_id")}
    candidates = []
    for job in jobs or []:
        if not _is_active_recruitment(job):
            continue
        jid = str(job.get("job_id") or "")
        if not jid:
            continue
        missing = any(_detail_bad(job.get(k), k) for k in ("vacancy", "qualification", "salary"))
        missing_dates = not _deadline_date(job.get("last_date"))
        is_new = jid in new_ids
        unverified = not bool(job.get("detail_verified"))
        if not (is_new or missing or missing_dates or unverified):
            continue
        priority = 0
        if is_new: priority -= 40
        if unverified: priority -= 25
        if missing: priority -= 10
        if missing_dates: priority -= 5
        candidates.append((priority, str(job.get("title", "")), job))
    candidates.sort(key=lambda x: (x[0], x[1].casefold()))
    cap = int(os.getenv("EUH_DETAIL_QUEUE_CAP", "16"))
    return [x[2] for x in candidates[:max(1, cap)]]


def _enrich_one_detail(job):
    """Enrich one record with a fresh adapter instance (thread-safe worker)."""
    adapter = BaseAdapter()
    before = {k: str(job.get(k, "") or "").strip() for k in (
        "vacancy", "qualification", "salary", "age_limit", "application_fee",
        "selection_process", "exam_date", "application_start_date", "last_date",
        "notification_date", "notification_pdf", "official_notification_pdf", "apply_link",
        "detail_verified", "detail_source"
    )}
    try:
        enriched = adapter.enrich_job(dict(job))
        for key, value in enriched.items():
            if key in {"title", "url", "job_id", "category", "post_type", "department"}:
                continue
            if value is not None:
                job[key] = value
        after = {k: str(job.get(k, "") or "").strip() for k in before}
        changed = after != before
        return job, changed, None
    except Exception as exc:
        return job, False, exc


def enrich_detail_queue(jobs, new_jobs):
    """Deep-enrich a large active queue concurrently.

    The previous implementation processed only six records sequentially. That
    made hundreds of active posts keep empty/wrong tables forever. This version
    processes a bounded but much larger queue in parallel, then subsequent hourly
    runs continue the queue until all active records are verified.
    """
    queue = _detail_queue(jobs, new_jobs)
    workers = max(1, int(os.getenv("EUH_DETAIL_WORKERS", "4")))
    logger.info("DETAIL QUEUE | ActiveCandidates=%d | ThisRun=%d | Workers=%d",
                len([j for j in jobs if _is_active_recruitment(j)]), len(queue), workers)
    if not queue:
        return jobs

    by_id = {str(j.get("job_id")): j for j in queue if j.get("job_id")}
    changed = 0
    attempted = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {executor.submit(_enrich_one_detail, job): str(job.get("job_id")) for job in queue}
        for future in as_completed(future_map):
            attempted += 1
            jid = future_map[future]
            try:
                updated, did_change, error = future.result()
                target = by_id.get(jid)
                if target is not None:
                    target.clear()
                    target.update(updated)
                if did_change:
                    changed += 1
                if error:
                    logger.error("DETAIL QUEUE FAILED | %s | %s", jid, error)
                else:
                    logger.info(
                        "DETAIL QUEUE RESULT | %s | vacancy=%s | qualification=%s | salary=%s | selection=%s | last_date=%s | pdf=%s | verified=%s",
                        updated.get("title", ""), updated.get("vacancy", ""), updated.get("qualification", ""),
                        updated.get("salary", ""), updated.get("selection_process", ""), updated.get("last_date", ""),
                        updated.get("notification_pdf", ""), updated.get("detail_verified", False)
                    )
            except Exception:
                logger.exception("Detail queue worker failed: %s", jid)
    logger.info("DETAIL QUEUE SUMMARY | Attempted=%d | Changed=%d", attempted, changed)
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
        # 1. Scrape / discover only
        # --------------------------------------------------
        # Deep PDF/OCR extraction is intentionally deferred. Without this
        # switch every adapter tried to process PDFs while all 284 sources
        # were being scraped, which is what caused the 45-minute timeout.
        os.environ["EUH_DEFER_DETAIL"] = "1"
        logger.info("Scraping Websites (discovery-only mode)...")
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

        # Deep detail/PDF extraction is now the authoritative second stage.
        # First clear unverified active values so contaminated legacy fields
        # cannot leak into the new HTML; then rebuild them from the actual
        # detail page/notification PDF.
        os.environ["EUH_DEFER_DETAIL"] = "0"
        merged_jobs = reset_unverified_active_details(merged_jobs)
        merged_jobs = enrich_detail_queue(merged_jobs, new_jobs)

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

        # Expired recruitment remains in the database for history, but is
        # moved to archive and removed from all live recruitment categories.
        try:
            from archive_manager import archive_expired_jobs, rebuild_archive_page
            archive_expired_jobs(merged_jobs)
            rebuild_archive_page()
            logger.info("ARCHIVE UPDATED")
        except Exception:
            logger.exception("Archive update failed")

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
