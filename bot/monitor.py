import logging
import sys
import os

from sources_manager import SourceManager
from scraper import scrape_all_sources
from parser import parse_jobs
from optimizer import run_optimizer
from database import load_jobs, save_jobs
from html_generator import generate_all
import homepage
from sitemap_generator import update_sitemap

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

def _normalise(result):
    if isinstance(result, tuple):
        return (result[0] or [], result[1] or [])
    return (result or [], [])

def _ai_enrich_new_jobs(new_jobs):
    if not os.getenv("OPENROUTER_API_KEY"):
        logger.warning("AI EDITOR SKIPPED | OPENROUTER_API_KEY is not available")
        return 0, 0
    from ai_editor import enrich
    ok = failed = 0
    # Free router has daily limits. Only new records go through AI on each run.
    for job in new_jobs:
        original_title = job.get("title", "")
        try:
            ai = enrich(job)
            if ai.get("post_type"): job["post_type"] = ai["post_type"]
            if ai.get("title"): job["title"] = ai["title"]
            if ai.get("seo_title"): job["seo_title"] = ai["seo_title"]
            if ai.get("summary_hi"): job["description"] = ai["summary_hi"]
            for k in ("department","organization","post_name","vacancy","qualification","salary","age_limit","application_start","last_date","fee","exam_date"):
                if ai.get(k): job[k] = ai[k]
            url_map = {
                "apply_url":"apply_link", "admit_card_url":"admit_card_url",
                "result_url":"result_url", "answer_key_url":"answer_key_url",
                "syllabus_url":"syllabus_url", "notification_url":"notification_pdf",
                "official_url":"official_website"
            }
            for src, dst in url_map.items():
                if ai.get(src): job[dst] = ai[src]
            job["ai_faq"] = ai.get("faq", [])
            job["ai_confidence"] = ai.get("confidence", "low")
            ok += 1
            logger.info("AI EDITED | %s | type=%s", job.get("title", original_title), job.get("post_type", ""))
        except Exception as e:
            failed += 1
            logger.error("AI EDIT FAILED | %s | %s", original_title, e)
    logger.info("AI EDITOR | Success=%d | Failed=%d | Model=%s", ok, failed, os.getenv("OPENROUTER_MODEL", "openrouter/free"))
    return ok, failed

def main():
    try:
        logger.info("="*60)
        logger.info("Education Update Hub Auto Publisher Started")
        logger.info("="*60)
        manager = SourceManager()
        sources = manager.get_html_sources()
        logger.info("Total Sources : %d | HTML Sources : %d", manager.count(), len(sources))
        if not sources: return

        all_jobs, failed_sources = _normalise(scrape_all_sources(sources, workers=12))
        logger.info("Links Found : %d | Failed Sources : %d", len(all_jobs), len(failed_sources))
        if not all_jobs: return

        parsed_jobs = parse_jobs(all_jobs)
        logger.info("Parsed Jobs : %d", len(parsed_jobs))
        if not parsed_jobs: return

        old_jobs = load_jobs()
        result = run_optimizer(old_jobs, parsed_jobs)
        merged_jobs = result.get("jobs", [])
        new_jobs = result.get("new_jobs", [])
        logger.info("Old Jobs : %d | Merged Jobs : %d | New Jobs : %d", len(old_jobs), len(merged_jobs), len(new_jobs))
        if not merged_jobs: return

        _ai_enrich_new_jobs(new_jobs)
        save_jobs(merged_jobs)
        logger.info("Database Saved : %d jobs", len(merged_jobs))

        summary = generate_all(merged_jobs, category_jobs=merged_jobs)
        if isinstance(summary, dict):
            logger.info("Generation Summary | Generated=%s Failed=%s Total=%s", summary.get("success",0), summary.get("failed",0), summary.get("total",0))
        from url_utils import post_exists
        valid_jobs = [j for j in merged_jobs if post_exists(j)]
        if not valid_jobs: raise RuntimeError("No generated posts available after HTML generation")
        save_jobs(valid_jobs)

        from category_generator import build_categories
        build_categories(valid_jobs)
        if not homepage.run(valid_jobs): raise RuntimeError("Homepage generation returned False")
        try: update_sitemap(valid_jobs)
        except TypeError: update_sitemap()
        logger.info("Automation Completed Successfully | Total=%d | New=%d", len(valid_jobs), len(new_jobs))
    except Exception:
        logger.exception("Fatal Error")
        sys.exit(1)

if __name__ == "__main__": main()
