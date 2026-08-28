import logging
import sys
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
    adapter = BaseAdapter()
    cleared = 0
    for job in jobs or []:
        raw_category = str(job.get("category", "") or "").strip().casefold()
        title_probe = str(job.get("title", "") or "").strip().casefold()
        explicit_recruitment = any(x in title_probe for x in (
            "recruitment", "vacancy", "apply online", "applications are invited",
            "walk-in", "walk in", "appointment of", "engagement of",
            "भर्ती", "रिक्ति", "आवेदन आमंत्रित"
        ))
        if raw_category in {"government scheme", "government schemes", "scheme"} and not explicit_recruitment:
            ptype = "government-scheme"
        else:
            ptype = adapter.detect_post_type(job.get("title", ""), job.get("url", ""), job.get("category", ""))
        job["post_type"] = ptype
        if ptype == "government-scheme":
            job["category"] = "Government Schemes"
        if ptype != "recruitment":
            for key in ("vacancy", "qualification", "salary", "age_limit", "application_fee", "selection_process"):
                if job.get(key):
                    job[key] = ""
                    cleared += 1
    logger.info("POST TYPE NORMALIZATION | NonRecruitmentCleared=%d", cleared)
    return jobs

def sanitize_detail_fields(jobs):
    bad_common = (
        "caste certificates", "disability certificate", "ews certificate",
        "will be verified with the concerned issuing authority", "veracity and validity",
        "stipulated dates before registering", "slips, etc", "go to index",
        "check official notification", "not available", "as per rules",
        "slips, etc", "go to index", "previous button", "page no.", "step-1",
        "candidates are warned", "stipulated dates before registering",
        "page no", "page no.-", "misconduct", "go to index", "previous button",
    )
    for job in jobs or []:
        # Remove OCR/control characters and leading punctuation from titles too.
        title = re.sub(r"[\\x00-\\x08\\x0b\\x0c\\x0e-\\x1f\\x7f]", " ", str(job.get("title", "") or ""))
        title = re.sub(r"^[\\s=.:;,_|/\\\\\\-–—•·]+", "", title)
        title = re.sub(r"\\s+", " ", title).strip()
        if title:
            job["title"] = title
        for field in ("qualification", "salary", "vacancy", "application_fee", "selection_process"):
            value = str(job.get(field, "") or "").strip()
            low = value.casefold()
            if not value or any(x in low for x in bad_common):
                job[field] = ""
                continue
            value = re.sub(r"(?m)^\s*(?:\d+[-.)]|[A-Za-z][.)]|[क-ह][.)])\s*", "", value)
            value = re.sub(r"^[\s=.:;,_|/\\\-–—•·]+", "", value)
            value = re.sub(r"\s+", " ", value).strip(" -:;,|.=/" )
            words = re.findall(r"[A-Za-zÀ-ÿ]+|[\u0900-\u097F]+", value.casefold())
            if words and words[-1] in {"and","or","of","with","for","to","the","के","की","का","में","से","हेतु","तथा","और","या"}:
                value = ""
            job[field] = value
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
