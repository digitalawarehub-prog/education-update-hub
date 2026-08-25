import logging
import sys
from datetime import datetime,timedelta,timezone

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
    if field == "qualification" and (
        any(x in s for x in ("certification and work", "slips, etc", "stipulated dates before registering", "official notification", "click here", "हेतु क्लिक करें"))
        or s in {"a", "an", "1", "(a)", "o:- (a)"}
        or len(s) < 8
    ):
        return True
    if field == "salary" and (
        any(x in s for x in ("slips, etc", "as per rules", "official notification", "click here", "हेतु क्लिक करें"))
        or s in {"rs", "rs.", "₹", "inr"}
        or len(s) < 3
    ):
        return True
    if field == "selection_process" and any(x in s for x in ("click here", "हेतु क्लिक करें", "के संबंध में जानकारी", "visit the website", "exam programme")):
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
    """Bounded, parallel detail repair; failed items are not retried every run."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    adapter = BaseAdapter()
    now = datetime.now(timezone.utc)
    candidates = []
    for job in jobs or []:
        if not _needs_detail_repair(job):
            continue
        if not str(job.get("title") or "").strip():
            continue
        last = str(job.get("detail_last_attempt") or "").strip()
        if last:
            try:
                dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
                dt = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
                if now - dt < timedelta(hours=12):
                    continue
            except Exception:
                pass
        candidates.append(job)

    candidates.sort(key=lambda j: (
        not bool(j.get("notification_pdf")),
        str(j.get("scraped_at") or "")
    ))
    # Repair a meaningful batch each run; six records was too small for a 500+ job database.
    batch = candidates[:60]
    logger.info("DETAIL QUEUE | Candidates=%d | ThisRun=%d | Workers=8", len(candidates), len(batch))
    if not batch:
        return jobs

    def one(job):
        local = BaseAdapter()
        j = dict(job)
        before = {k: str(j.get(k, "") or "").strip() for k in (
            "vacancy","qualification","salary","age_limit","application_fee",
            "selection_process","exam_date","application_start_date",
            "last_date","notification_date","notification_pdf"
        )}
        j["detail_last_attempt"] = now.isoformat()
        # A repair is authoritative: stale values from an unrelated/old PDF
        # must not survive into the new extraction. The detail page/PDF is
        # allowed to repopulate whatever is genuinely present.
        for key in (
            "vacancy","qualification","salary","age_limit","application_fee",
            "selection_process","exam_date","application_start_date","last_date",
            "notification_date","notification_pdf","official_notification_pdf"
        ):
            j[key] = ""
        try:
            enriched = local.enrich_job(j)
            for key, value in enriched.items():
                if key in {"title","url","job_id","category","post_type","department"}:
                    continue
                if value is not None:
                    j[key] = value
            after = {k: str(j.get(k, "") or "").strip() for k in before}
            j["detail_status"] = "repaired" if after != before else "needs_review"
            return j
        except Exception:
            j["detail_status"] = "needs_review"
            logger.exception("Detail repair failed: %s", j.get("title", ""))
            return j

    repaired = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(one, job): job for job in batch}
        for fut in as_completed(futures):
            old = futures[fut]
            try:
                new_job = fut.result()
                old.update(new_job)
                if new_job.get("detail_status") == "repaired":
                    repaired += 1
                    logger.info(
                        "DETAIL REPAIRED | %s | vacancy=%s | qualification=%s | salary=%s | selection=%s | last_date=%s",
                        old.get("title",""), old.get("vacancy",""), old.get("qualification",""),
                        old.get("salary",""), old.get("selection_process",""), old.get("last_date","")
                    )
            except Exception:
                logger.exception("Detail worker failed: %s", old.get("title",""))
                old["detail_status"] = "needs_review"

    logger.info("DETAIL QUEUE SUMMARY | Attempted=%d | Repaired=%d | Deferred=%d",
                len(batch), repaired, max(0, len(candidates)-len(batch)))
    return jobs

def write_archive_page(all_jobs, active_jobs):
    """Write a lightweight archive while keeping expired jobs out of active categories/homepage."""
    from pathlib import Path
    from url_utils import post_relative_url, post_exists
    import html
    active_ids={str(j.get("job_id") or j.get("url") or j.get("title")) for j in active_jobs}
    expired=[j for j in (all_jobs or []) if str(j.get("post_type",""))=="recruitment" and str(j.get("job_id") or j.get("url") or j.get("title")) not in active_ids and j.get("title") and post_exists(j)]
    cards=[]
    for j in sorted(expired,key=lambda x:str(x.get("last_date") or x.get("publish_date") or ""),reverse=True)[:500]:
        link="/"+post_relative_url(j).lstrip("/")
        cards.append(f'<article><h3><a href="{html.escape(link)}">{html.escape(str(j.get("title","")))}</a></h3><p>Last Date: {html.escape(str(j.get("last_date","")))}</p></article>')
    root=Path(__file__).resolve().parent.parent
    page='<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Archived Jobs | Education Update Hub</title></head><body><main style="max-width:900px;margin:30px auto;padding:20px"><h1>Archived Jobs</h1>'+''.join(cards)+'</main></body></html>'
    (root/"archive.html").write_text(page,encoding="utf-8")
    logger.info("ARCHIVE | %d expired recruitment posts",len(expired))

_SOURCE_PRIORITY = {
    "upsc", "ssc", "ibps", "sbi careers", "reserve bank of india",
    "rbi", "nabard", "sebi", "lic", "rrb", "ukpsc", "uksssc",
    "upsc recruitment", "nta"
}

def _source_name(source):
    if isinstance(source, dict):
        return str(source.get("name") or source.get("title") or source.get("source") or "").strip()
    return str(getattr(source, "name", "") or getattr(source, "title", "") or "").strip()

def _select_source_batch(sources):
    """Select sources for this run.

    The previous production build hard-coded 60 of 283 sources, so most
    categories could only receive new posts when their source happened to be
    in the rotating slot.  Default is now ALL sources every run.  An optional
    SOURCE_BATCH_SIZE can be used only if GitHub Actions runtime ever needs a
    deliberate cap.
    """
    import os

    sources = list(sources or [])
    try:
        requested = int(os.getenv("SOURCE_BATCH_SIZE", "0"))
    except ValueError:
        requested = 0

    if requested <= 0 or requested >= len(sources):
        selected = sources
    else:
        # Keep priority sources in every run and rotate the remaining sources.
        priority, rest = [], []
        for source in sources:
            name = _source_name(source).casefold()
            if name in _SOURCE_PRIORITY:
                priority.append(source)
            else:
                rest.append(source)
        slot = datetime.now().hour * 2 + datetime.now().minute // 30
        chunk_size = max(0, requested - len(priority))
        if chunk_size <= 0:
            selected = priority[:requested]
        else:
            start = (slot * chunk_size) % max(1, len(rest))
            rotated = rest[start:start + chunk_size]
            if len(rotated) < chunk_size:
                rotated += rest[:chunk_size-len(rotated)]
            selected = priority + rotated
            selected = selected[:requested]

    logger.info(
        "SOURCE BATCH | Total=%d | Selected=%d | Mode=%s",
        len(sources), len(selected),
        "ALL" if len(selected) == len(sources) else "ROTATING"
    )
    return selected


def _has_real_date(value):
    import re
    s=str(value or "").strip()
    return bool(re.search(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b",s))

def _publishable_active_jobs(jobs):
    """Publish usable active posts while retaining repair status.

    A recruitment post should not disappear from category pages merely because
    one optional field could not be extracted.  If the post has a real deadline
    plus two core fields, or an identity-checked official notification PDF,
    publish it and mark the remaining fields for repair.
    """
    out = []
    held = 0
    reasons = {}
    for job in jobs or []:
        if str(job.get("post_type", "")).casefold() != "recruitment":
            out.append(job)
            continue

        core = sum(
            1 for key in ("vacancy", "qualification", "salary", "selection_process")
            if str(job.get(key) or "").strip()
        )
        last = _has_real_date(job.get("last_date"))
        has_pdf = bool(str(job.get("notification_pdf") or "").strip())
        usable = (last and core >= 2) or (has_pdf and core >= 1) or (last and core >= 1)

        if usable:
            job["detail_status"] = "publishable" if core >= 3 and last else "publishable_with_repair"
            out.append(job)
        else:
            job["detail_status"] = "needs_review"
            held += 1
            reason = "missing_last_date_and_core_details"
            if not last:
                reason = "missing_last_date"
            elif core == 0:
                reason = "missing_core_details"
            reasons[reason] = reasons.get(reason, 0) + 1

    logger.info(
        "ACTIVE QUALITY GATE | Publishable=%d | HeldForRepair=%d | Reasons=%s",
        len(out), held, reasons
    )
    return out


def normalize_published_dates_in_html():
    """Fix only the human-visible Published date; schema dates remain ISO."""
    import re
    from pathlib import Path
    root=Path(__file__).resolve().parent.parent
    changed=0
    rx=re.compile(r"(📅\s*[^:]{1,40}:\s*)(20\d{2})-(\d{2})-(\d{2})")
    for path in root.rglob("*.html"):
        try:
            text=path.read_text(encoding="utf-8")
            new=rx.sub(lambda m: f"{m.group(1)}{m.group(4)}-{m.group(3)}-{m.group(2)}",text)
            if new!=text:
                path.write_text(new,encoding="utf-8")
                changed+=1
        except Exception:
            continue
    logger.info("PUBLISH DATE DISPLAY FIX | FilesChanged=%d | Format=DD-MM-YYYY",changed)


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
        scrape_sources = _select_source_batch(sources)
        all_jobs, failed_sources = _normalise_scrape_result(
            scrape_all_sources(scrape_sources)
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

        # Remove source-page CTA text from titles before any HTML is generated.
        for job in merged_jobs:
            job["title"] = BaseAdapter().clean_title(job.get("title", ""))
            if not job["title"]:
                job["title"] = str(job.get("title") or "").strip()

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
        normalize_published_dates_in_html()
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

        from html_generator import filter_active_jobs
        active_jobs=filter_active_jobs(merged_jobs)
        active_jobs=_publishable_active_jobs(active_jobs)
        logger.info("ACTIVE DATASET | %d active of %d total",len(active_jobs),len(merged_jobs))
        from category_generator import build_categories
        build_categories(active_jobs)
        write_archive_page(merged_jobs, active_jobs)

        # --------------------------------------------------
        # 5. Homepage + header + search index from complete DB
        # --------------------------------------------------
        logger.info("Updating Homepage + Header + Search...")
        if homepage.run(active_jobs):
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
