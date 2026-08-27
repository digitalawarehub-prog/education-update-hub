import logging
import sys
import os
import re

from sources_manager import SourceManager
from scraper import scrape_all_sources
from parser import parse_jobs
from optimizer import run_optimizer
from database import load_jobs, save_jobs
from html_generator import generate_all
import homepage
from sitemap_generator import update_sitemap
from adapters.base import BaseAdapter
from filters import classify_post

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
    cleared = 0
    for job in jobs or []:
        ptype = classify_post(job.get("title", ""), job.get("url", ""), job.get("description", ""), job.get("source", "")) or str(job.get("category", "") or "").strip() or "Recruitment"
        job["post_type"] = ptype
        if ptype != "recruitment":
            for key in ("vacancy", "qualification", "salary", "age_limit", "application_fee", "selection_process"):
                if job.get(key):
                    job[key] = ""
                    cleared += 1
    logger.info("POST TYPE NORMALIZATION | NonRecruitmentCleared=%d", cleared)
    return jobs

def sanitize_detail_fields(jobs):
    """Remove OCR fragments, leading symbols and incomplete field values."""
    bad_common = (
        "caste certificates", "disability certificate", "ews certificate",
        "will be verified with the concerned issuing authority", "veracity and validity",
        "stipulated dates before registering", "slips, etc", "go to index",
        "check official notification", "not available", "not mentioned",
    )
    def clean(value, field):
        text = str(value or "").replace("\xa0", " ").strip()
        text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
        text = re.sub(r"\s+", " ", text)
        # Remove leading OCR/table punctuation such as '=' and stray dots.
        text = re.sub(r"^[\s=.:;,|/\\\-–—•·]+", "", text)
        text = re.sub(r"^(?:i{1,3}|iv|v|[a-z])\s*[.)-]\s*", "", text, flags=re.I)
        text = re.sub(r"\s+", " ", text).strip(" -:;,|./")
        # OCR often leaves a broken marker before a number, e.g. 'ू0-600'.
        text = re.sub(r"^[^0-9₹]{1,3}(?=\d)", "", text)
        if not text or len(text) > (650 if field == "qualification" else 320):
            return ""
        low = text.casefold()
        if any(x in low for x in bad_common) or re.search(r"page\s*no\.?\s*[-:]?\s*\d+", low):
            return ""
        if re.match(r"^(?:allied|relevant discipline|and/or|or |and |criteria\s*/|research project|parent pay|specific requirements)", low):
            return ""
        if field == "qualification" and ("|" in text or "per month maximum" in low or re.search(r"\b(?:rs\.?|pay|salary)\s*\d", low)):
            return ""
        if field == "salary" and re.fullmatch(r"\d{1,2}", text):
            return ""
        if field in {"selection_process", "application_fee"} and len(text) < 3:
            return ""
        if re.search(r"\b(?:age|qualification|salary|pay|fee|selection)\s+(?:qualification|salary|pay|fee|selection|1)\b", low):
            return ""
        # Reject fragments ending with a connector or obvious OCR truncation.
        if re.search(r"(?:\b(?:and|or|of|for|with|to|as|the|perform|based)\s*)$", low):
            return ""
        # A field beginning with a slash or broken list marker is not a complete value.
        if text.startswith(("/", "\\")) or re.match(r"^(?:ii|iii|iv|v)[.)]", text, re.I):
            return ""
        if field == "vacancy" and not re.search(r"\b\d{1,6}\b", text):
            return ""
        if field == "application_fee" and not re.search(r"\d", text) and not re.search(r"free|nil|no fee|निःशुल्क|शुल्क नहीं", low, re.I):
            return ""
        return text

    for job in jobs or []:
        for field in ("qualification", "salary", "vacancy", "application_fee", "selection_process", "age_limit", "last_date"):
            if field in job:
                job[field] = clean(job.get(field), field)
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
    max_repairs = 12
    for job in jobs or []:
        if attempted >= max_repairs:
            break
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
        total_sources = manager.count()
        batch_size = os.getenv("EHU_SOURCE_BATCH_SIZE", "80")
        sources = manager.get_run_sources(batch_size)
        logger.info("Total Sources Found : %d", total_sources)
        logger.info("Source Batch Size   : %s", batch_size)
        logger.info("Current Batch       : %d", len(sources))

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

        # Even when the current batch has no successful source, keep the
        # persistent database alive and rebuild only its active records. This
        # prevents a temporary government-site outage from leaving stale/
        # malformed generated pages on the website.
        if all_jobs:
            logger.info("Parsing Jobs...")
            parsed_jobs = parse_jobs(all_jobs)
            logger.info("Parsed Jobs : %d", len(parsed_jobs))
        else:
            parsed_jobs = []
            logger.warning("Current batch returned no jobs; using persistent database only.")

        # --------------------------------------------------
        # 2. Parse + persistent database
        # --------------------------------------------------

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
        merged_jobs = sanitize_detail_fields(merged_jobs)

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
        logger.info("Failed Sources : %d", len(failed_sources))
        logger.info("=" * 60)

    except Exception:
        logger.exception("Fatal Error")
        sys.exit(1)


if __name__ == "__main__":
    main()
