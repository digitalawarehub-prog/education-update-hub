import logging
import sys

from sources_manager import SourceManager
from scraper import scrape_all_sources
from parser import parse_jobs
from duplicate_checker import filter_new_jobs
from html_generator import generate_all
from homepage import build_homepage
from sitemap_generator import update_sitemap


# ==========================================
# Logging
# ==========================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


def main():

    try:

        logger.info("=" * 60)
        logger.info("Education Update Hub Auto Publisher Started")
        logger.info("=" * 60)

        # ==========================================
        # Load Sources
        # ==========================================

        manager = SourceManager()

        logger.info("Total Sources : %d", manager.count())

        sources = manager.get_html_sources()

        logger.info("HTML Sources : %d", len(sources))

        if not sources:

            logger.warning("No HTML sources found.")

            return

        # ==========================================
        # Scrape
        # ==========================================

        logger.info("Scraping Websites...")

        all_jobs, failed_sources = scrape_all_sources(
            sources
        )

        logger.info("Links Found : %d", len(all_jobs))
        logger.info("Failed Sources : %d", len(failed_sources))

        if not all_jobs:

            logger.info("No links found.")

            return

        # ==========================================
        # Parse
        # ==========================================

        logger.info("Parsing Jobs...")

        parsed_jobs = parse_jobs(all_jobs)

        logger.info("Parsed Jobs : %d", len(parsed_jobs))

        if not parsed_jobs:

            logger.info("No valid jobs found.")

            return

        # ==========================================
        # Remove Duplicates
        # ==========================================

        logger.info("Checking Duplicates...")

        new_jobs = filter_new_jobs(parsed_jobs)

        logger.info("New Jobs : %d", len(new_jobs))

        if not new_jobs:

            logger.info("No New Jobs Found.")

            return

        logger.info("-" * 60)

        for job in new_jobs:

            logger.info("NEW : %s", job.get("title", "Untitled"))

        logger.info("-" * 60)

        # ==========================================
        # Generate HTML
        # ==========================================

        logger.info("Generating HTML Files...")

        summary = generate_all(new_jobs)

        logger.info("")

        logger.info("Generation Summary")

        logger.info("Generated : %d", summary["success"])

        logger.info("Failed    : %d", summary["failed"])

        logger.info("Total     : %d", summary["total"])

        for result in summary["results"]:

            if result["success"]:

                logger.info(
                    "Generated : %s",
                    result["file"]
                )

            else:

                logger.error(
                    "Failed : %s",
                    result["title"]
                )

                logger.error(
                    result["error"]
                )

        # ==========================================
        # Homepage
        # ==========================================

        logger.info("Updating Homepage...")

        if build_homepage(new_jobs):

            logger.info("Homepage Updated Successfully.")

        else:

            logger.warning("Homepage Update Failed.")

        # ==========================================
        # Sitemap
        # ==========================================

        logger.info("Updating Sitemap...")

        if update_sitemap(new_jobs):

            logger.info("Sitemap Updated Successfully.")

        else:

            logger.warning("Sitemap Update Failed.")

        logger.info("=" * 60)

        logger.info("Automation Completed Successfully")

        logger.info("=" * 60)

    except Exception:

        logger.exception("Fatal Error")

        sys.exit(1)


if __name__ == "__main__":

    main()
