import logging
import re
import sys
from pathlib import Path

from sources_manager import SourceManager
from scraper import scrape_all_sources
from parser import parse_jobs
from optimizer import run_optimizer
from database import load_jobs, save_jobs
from html_generator import generate_all
import homepage
from sitemap_generator import update_sitemap
from adapters.base import BaseAdapter
from archive_manager import update as update_archive

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
    import re
    s = str(value or "").strip()
    low = s.casefold()
    if low in {"", "not mentioned", "check official notification", "check notification", "as per rules", "not available", "उपलब्ध नहीं", "आधिकारिक अधिसूचना देखें", ".", "none", "null"}:
        return True
    if "�" in s or any(x in low for x in ("disclaimer", "i agree", "press release", "faq.pdf", "stipulated dates", "before registering online", "slips, etc", "http://", "https://", "www.", "आवेदन किया जाता है और आयोग के संज्ञान में", "पूर्ण न होने पर भी आवेदन", "परीक्षाओं से विवर्जित", "tts", "s1%", "support_agent")):
        return True
    mojibake=len(re.findall(r"(?:Ã|Â|â€|à¤|à¥|ðŸ|\ufffd)", s))
    if mojibake >= 2:
        return True
    if field == "vacancy":
        m=re.search(r"\b(\d{1,6})\b", s)
        if not m:
            return True
        n=int(m.group(1))
        if n > 100000 or 1900 <= n <= 2100:
            return True
    if field == "qualification":
        if re.match(r"^\(?\s*as\s+on\b", s, re.I) or len(s) < 4 or len(s) > 500 or re.fullmatch(r"[A-Za-z]", s):
            return True
    if field == "salary":
        if len(s) > 300 or re.fullmatch(r"(?:rs\.?|₹)\s*\d{1,2}", s, re.I):
            return True
    if field == "age_limit":
        if re.match(r"^\(?\s*as\s+on\b", s, re.I) or len(s) < 3:
            return True
    if field == "selection_process":
        if len(s) < 8 or re.search(r"\b(?:www\.|https?://)", low):
            return True
    if field == "application_fee":
        if len(s) > 240:
            return True
        if not re.search(r"(?:₹|rs\.?|inr|\b\d{2,6}\b|free|no\s*fee|nil|निः?शुल्क|शुल्क\s*नहीं)", s, re.I):
            return True
    return False


def _needs_detail_repair(job):
    """Return True when legacy data is missing, stale or visibly corrupted."""
    category = str(job.get("category", "") or "").strip().casefold()
    post_type = str(job.get("post_type", "") or "").strip().casefold()
    title = str(job.get("title", "") or "").lower()
    if category not in {"recruitment", "latest jobs", "job", "jobs"} and post_type not in {"recruitment", "latest jobs"}:
        return False
    if any(x in title for x in ("admit card", "admit-card", "hall ticket", "call letter", "answer key", "answer-key", "result", "syllabus", "scholarship")):
        return False
    if any(_detail_bad(job.get(k), k) for k in ("vacancy", "qualification", "salary", "age_limit", "application_fee", "selection_process", "exam_date", "application_start_date", "last_date")):
        return True
    # A page-level scraper description must never be treated as editorial copy.
    desc=str(job.get("description", "") or "")
    if any(x in desc.casefold() for x in ("disclaimer", "i agree", "press release", "skip to", "cookie")):
        return True
    # Stale/wrong action links from old generic scraping.
    pdf=str(job.get("notification_pdf", "") or "").lower()
    apply=str(job.get("apply_link", "") or "").lower()
    if any(x in pdf for x in ("press_release", "press-release", "faq.pdf", "/faq")):
        return True
    if apply.endswith("faq.pdf") or "/faq" in apply:
        return True
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
            # Remove known-bad legacy values first; otherwise merge logic can
            # keep an old FAQ/press-release URL forever.
            for key in ("vacancy", "qualification", "salary", "age_limit", "application_fee", "selection_process", "exam_date", "application_start_date", "last_date"):
                if _detail_bad(job.get(key), key):
                    job[key] = ""
            pdf=str(job.get("notification_pdf", "") or "").lower()
            apply=str(job.get("apply_link", "") or "").lower()
            if any(x in pdf for x in ("press_release", "press-release", "faq.pdf", "/faq")):
                job["notification_pdf"]=""
            if apply.endswith("faq.pdf") or "/faq" in apply or apply.startswith("javascript:"):
                job["apply_link"]=""
            job["description"] = ""
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

def _clean_public_text(value, max_len=900):
    """Remove source-page chrome/OCR junk from text that can reach HTML."""
    text = str(value or "").replace("\ufffd", " ")
    text = re.sub(r"(?i)\bDisclaimer\s*[:\-–]?\s*I\s*Agree\b", " ", text)
    text = re.sub(r"(?i)\bSkip\s+to\s+(?:main\s+)?content\b", " ", text)
    text = re.sub(r"(?i)\b(?:A\s*[-–]?\s*A\s*[-–]?\s*A\s*[-–]?\s*A|English\s+Hindi)\b", " ", text)
    text = re.sub(r"(?i)\b(?:cookie|privacy policy|accessibility|support agent|screen reader)\b[^.]{0,120}", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" -|:;,." )
    return text[:max_len]


def final_quality_gate(jobs):
    """Final firewall: publish only clean, type-correct structured data."""
    adapter = BaseAdapter()
    cleared = 0
    for job in jobs or []:
        title = _clean_public_text(job.get("title", ""), 300)
        title = re.sub(r"\s+New\s*$", "", title, flags=re.I)
        job["title"] = title
        ptype = adapter.detect_post_type(job.get("title", ""), job.get("url", ""), job.get("category", ""))
        job["post_type"] = ptype
        if ptype != "recruitment":
            for key in ("vacancy", "qualification", "salary", "age_limit", "application_fee", "selection_process"):
                if job.get(key):
                    job[key] = ""
                    cleared += 1
        else:
            for key in ("vacancy", "qualification", "salary", "age_limit", "application_fee", "selection_process"):
                value = _clean_public_text(job.get(key, ""), 650)
                field = key if key in {"vacancy", "salary", "qualification", "application_fee"} else None
                if key == "age_limit" and re.match(r"^\(?\s*as\s+on\b", value, re.I):
                    value = ""
                if key == "salary" and re.search(r"(?:application|exam(?:ination)?)\s+fee|आवेदन\s+शुल्क|परीक्षा\s+शुल्क", value, re.I):
                    value = ""
                if "sbi" in str(job.get("title", "")).casefold() and "junior associate" in str(job.get("title", "")).casefold() and key == "vacancy":
                    try:
                        if int(re.search(r"\d+", value).group()) < 100:
                            value = ""
                    except Exception:
                        value = ""
                if not value or _detail_bad(value, key) or not adapter._usable_extracted(value, field):
                    if job.get(key):
                        cleared += 1
                    job[key] = ""
                else:
                    job[key] = value
        for key in ("description", "summary"):
            if key in job:
                cleaned = _clean_public_text(job.get(key, ""), 1200)
                if cleaned != str(job.get(key, "") or ""):
                    cleared += 1
                job[key] = cleaned
        pdf = str(job.get("notification_pdf", "") or "").strip()
        if pdf and (not pdf.startswith(("http://", "https://")) or any(x in pdf.lower() for x in ("press_release", "press-release", "faq.pdf", "/faq"))):
            job["notification_pdf"] = ""
            cleared += 1
        apply = str(job.get("apply_link", "") or "").strip()
        if apply and (apply.lower().startswith("javascript:") or apply.lower().endswith("faq.pdf") or "/faq" in apply.lower()):
            job["apply_link"] = ""
            cleared += 1
    logger.info("FINAL QUALITY GATE | Cleared=%d", cleared)
    return jobs


def main():
    try:
        logger.info("=" * 60)
        logger.info("Education Update Hub Auto Publisher Started")
        logger.info("=" * 60)

        manager = SourceManager()
        logger.info("Total Sources : %d", manager.count())
        force_all = not (Path(__file__).resolve().parent.parent / "database" / "source_state.json").exists()
        sources = manager.get_due_sources(force_all=force_all)
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
        manager.mark_scraped([src for src in sources if src not in failed_sources])
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
        merged_jobs = final_quality_gate(merged_jobs)

        active_jobs, archived_jobs, review_jobs = update_archive(merged_jobs)
        logger.info("JOB LIFECYCLE | Active=%d | Archived=%d | NeedsReview=%d", len(active_jobs), len(archived_jobs), len(review_jobs))

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
        # Rebuild archive after canonical slugs/html_file values are known so
        # every archived card links to a real historical post.
        update_archive(merged_jobs)
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
