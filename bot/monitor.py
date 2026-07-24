import logging
import sys

from sources_manager import SourceManager
from scraper import scrape_all_sources
from parser import parse_jobs
from duplicate_checker import filter_new_jobs
from html_generator import generate_all
from homepage_updater import update_homepage
from sitemap_generator import update_sitemap


# ===========================
# Logging
# ===========================

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

        # ===========================
        # Load Sources
        # ===========================

        manager = SourceManager()

        logger.info(f"Total Sources : {manager.count()}")

        sources = manager.get_html_sources()

        logger.info(f"HTML Sources : {len(sources)}")

        if not sources:
            logger.warning("No HTML sources found.")
            return

        # ===========================
        # Scrape
        # ===========================

        logger.info("Scraping Websites...")

        all_jobs = scrape_all_sources(
            sources,
            workers=10
        )

        logger.info(f"Links Found : {len(all_jobs)}")

        if not all_jobs:
            logger.info("No links found.")
            return

        # ===========================
        # Parse
        # ===========================

        logger.info("Parsing Jobs...")

        parsed_jobs = parse_jobs(all_jobs)

        logger.info(f"Parsed Jobs : {len(parsed_jobs)}")

        if not parsed_jobs:
            logger.info("No valid jobs found.")
            return

        # ===========================
        # Remove Duplicates
        # ===========================

        logger.info("Checking Duplicates...")

        new_jobs = filter_new_jobs(parsed_jobs)

        logger.info(f"New Jobs : {len(new_jobs)}")

        if not new_jobs:
            logger.info("No New Jobs Found.")
            return

        for job in new_jobs:
            logger.info(f"NEW : {job['title']}")

        # ===========================
        # Generate HTML
        # ===========================

        logger.info("Generating HTML Files...")

        generated = generate_all(new_jobs)

        if generated:

            logger.info(f"Generated Files : {len(generated)}")

            for file in generated:
                logger.info(file)

        # ===========================
        # Update Homepage
        # ===========================

        logger.info("Updating Homepage...")

        update_homepage(new_jobs)

        # ===========================
        # Update Sitemap
        # ===========================

        logger.info("Updating Sitemap...")

        update_sitemap(new_jobs)

        logger.info("=" * 60)
        logger.info("Automation Completed Successfully")
        logger.info("=" * 60)

    except Exception as e:

        logger.exception(f"Fatal Error : {e}")

        sys.exit(1)


if __name__ == "__main__":
    main()
