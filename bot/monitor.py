import logging
import sys

from sources_manager import SourceManager
from scraper import scrape_all_sources, enrich_jobs
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
            # Backward compatibility with older html_generator versions.
            logger.info("Generated : %s", result)


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
        # 3. Detail Enrichment
        # --------------------------------------------------
        # Parse step only gives title/url/category.
        # Enrich the scraped jobs before optimization so the canonical
        # dataset contains vacancy, qualification, salary and last_date.
        logger.info("Extracting Recruitment Details...")
        parsed_jobs = enrich_jobs(parsed_jobs)
        logger.info("Detail Enrichment Completed : %d jobs", len(parsed_jobs))

        # --------------------------------------------------
        # 4. Optimizer + persistent database
        # --------------------------------------------------
        logger.info("Optimizing Jobs...")
        old_jobs = load_jobs()
        result = run_optimizer(old_jobs, parsed_jobs)
        merged_jobs = result.get("jobs", [])
        new_jobs = result.get("new_jobs", [])

        # Older jobs may have been saved before detail extraction was
        # enabled. Enrich only those incomplete records, then save the
        # complete canonical dataset again.
        detail_keys = (
            "vacancy",
            "qualification",
            "salary",
            "last_date",
        )

        def needs_detail_enrichment(job):
            if not isinstance(job, dict):
                return False

            for key in detail_keys:
                value = str(job.get(key, "") or "").strip().lower()
                if not value:
                    return True

            return False

        incomplete_jobs = [
            job for job in merged_jobs
            if needs_detail_enrichment(job)
        ]

        if incomplete_jobs:
            logger.info(
                "Enriching Incomplete Existing Jobs : %d",
                len(incomplete_jobs)
            )
            enriched_incomplete = enrich_jobs(incomplete_jobs)

            # Map enriched records back by URL so other fields from the
            # optimizer are preserved.
            enriched_by_url = {
                str(job.get("url", "")).strip(): job
                for job in enriched_incomplete
                if isinstance(job, dict) and job.get("url")
            }

            for index, job in enumerate(merged_jobs):
                if not isinstance(job, dict):
                    continue

                url = str(job.get("url", "")).strip()
                enriched = enriched_by_url.get(url)

                if enriched:
                    job.update(enriched)
                    merged_jobs[index] = job

            logger.info("Existing Detail Enrichment Completed")

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
        # 5. Generate only new post files, but update categories
        #    from the complete merged database.
        # --------------------------------------------------
        if new_jobs:
            logger.info("Generating HTML Files for New Jobs...")
            summary = generate_all(
                new_jobs,
                category_jobs=merged_jobs
            )
            _log_generation(summary)
        else:
            logger.info("No new HTML posts to generate; refreshing categories.")
            # category pages are regenerated from the complete dataset.
            from category_generator import build_categories
            build_categories(merged_jobs)

        # --------------------------------------------------
        # 6. Homepage + header + search index from complete DB
        # --------------------------------------------------
        logger.info("Updating Homepage + Header + Search...")
        if homepage.run(merged_jobs):
            logger.info("Homepage + Header + Search Updated Successfully.")
        else:
            raise RuntimeError("Homepage generation returned False")

        # --------------------------------------------------
        # 7. Sitemap
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
