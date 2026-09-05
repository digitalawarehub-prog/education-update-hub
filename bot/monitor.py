import logging
import sys

from sources_manager import SourceManager
from scraper import scrape_all_sources
from parser import parse_jobs
from optimizer import run_optimizer
from database import load_jobs, save_jobs
from html_generator import generate_all
import homepage
from sitemap_generator import update_sitemap

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
            logger.info("Generated : %s", result)


def _validate_generated_posts_for_live_jobs(jobs):
    """
    Validate only posts that are actually eligible for the live website.

    IMPORTANT:
    The database intentionally keeps historical/expired records, while
    html_generator.py only creates HTML for active records. Therefore it is
    incorrect to require every database record to have a generated HTML file.
    """
    from url_utils import post_exists

    live_jobs = []
    missing = []

    # Use html_generator's own active filter when available so validation and
    # generation use exactly the same definition of an active post.
    try:
        from html_generator import filter_active_jobs
        live_jobs = filter_active_jobs(jobs or [])
    except Exception:
        # Safe fallback for older html_generator versions.
        live_jobs = list(jobs or [])

    for job in live_jobs:
        if post_exists(job):
            continue
        missing.append(job)

    logger.info(
        "POST LINK VALIDATION | Database=%d | LiveCandidates=%d | MissingLivePosts=%d",
        len(jobs or []),
        len(live_jobs),
        len(missing)
    )

    # Log missing live posts, but do not delete/replace the complete database.
    # A generation failure for one record should not make all older records
    # disappear from jobs.json.
    for job in missing[:25]:
        logger.warning(
            "MISSING LIVE POST | title=%s | html_file=%s | job_id=%s",
            job.get("title", ""),
            job.get("html_file", ""),
            job.get("job_id", "")
        )

    return live_jobs, missing


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

        logger.info("Old Jobs    : %d", len(old_jobs))
        logger.info("Merged Jobs : %d", len(merged_jobs))
        logger.info("New Jobs    : %d", len(new_jobs))

        if not merged_jobs:
            logger.warning("Optimizer returned no merged jobs.")
            return

        # Save the complete database. Historical/expired records must remain
        # available for archive/history and must NOT be removed just because
        # their generated HTML is no longer part of the live site.
        save_jobs(merged_jobs)
        logger.info("Database Saved : %d jobs", len(merged_jobs))

        # --------------------------------------------------
        # 4. Reconcile active generated posts
        # --------------------------------------------------
        logger.info("Reconciling generated posts from complete database...")
        summary = generate_all(merged_jobs, category_jobs=merged_jobs)
        _log_generation(summary)

        # CRITICAL FIX:
        # Do NOT replace merged_jobs with [job for job in merged_jobs
        # if post_exists(job)]. That incorrectly removes expired/history
        # records from jobs.json and can create stale/broken references.
        live_jobs, missing_live_posts = _validate_generated_posts_for_live_jobs(
            merged_jobs
        )

        # If some live posts are missing, keep the database intact. The
        # homepage/category layer will be built only from the live records
        # that have actually been generated.
        generated_live_jobs = [
            job for job in live_jobs
            if job not in missing_live_posts
        ]

        # If all live candidates are missing, do not publish an empty site.
        if live_jobs and not generated_live_jobs:
            raise RuntimeError(
                "No live generated posts available after HTML generation"
            )

        # Save the complete database again so any canonical slug/html_file
        # updates made by generate_all() are preserved.
        save_jobs(merged_jobs)
        logger.info(
            "Database Re-saved with canonical post metadata : %d jobs",
            len(merged_jobs)
        )

        # --------------------------------------------------
        # 5. Category pages
        # --------------------------------------------------
        from category_generator import build_categories

        logger.info(
            "Building categories from live generated dataset : %d jobs",
            len(generated_live_jobs)
        )
        build_categories(generated_live_jobs)

        # --------------------------------------------------
        # 6. Homepage + header + search
        # --------------------------------------------------
        # IMPORTANT: only generated live posts are sent to the navigation
        # layer. This prevents homepage/category/search links to missing files.
        logger.info("Updating Homepage + Header + Search...")

        if homepage.run(generated_live_jobs):
            logger.info(
                "Homepage + Header + Search Updated Successfully."
            )
        else:
            raise RuntimeError(
                "Homepage generation returned False"
            )

        # --------------------------------------------------
        # 7. Sitemap
        # --------------------------------------------------
        logger.info("Updating Sitemap...")

        try:
            # Sitemap may intentionally contain the complete database, because
            # historical URLs can remain useful for indexing/archive purposes.
            update_sitemap(merged_jobs)
            logger.info("Sitemap Updated Successfully.")
        except TypeError:
            update_sitemap()
            logger.info(
                "Sitemap Updated Successfully (database mode)."
            )

        logger.info("=" * 60)
        logger.info("Automation Completed Successfully")
        logger.info("Total Jobs : %d", len(merged_jobs))
        logger.info("Live Jobs  : %d", len(generated_live_jobs))
        logger.info("New Jobs   : %d", len(new_jobs))
        logger.info(
            "Missing Live Posts : %d",
            len(missing_live_posts)
        )
        logger.info("=" * 60)

    except Exception:
        logger.exception("Fatal Error")
        sys.exit(1)


if __name__ == "__main__":
    main()
