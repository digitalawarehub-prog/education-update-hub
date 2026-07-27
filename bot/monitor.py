import logging
import sys

from sources_manager import SourceManager
from scraper import scrape_all_sources
from parser import parse_jobs
from optimizer import run_optimizer
from html_generator import generate_all
from homepage import update_homepage
from sitemap_generator import update_sitemap

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
            logger.warning("No valid jobs after parsing.")
            return

        # ==========================================
        # Optimize
        # ==========================================

        logger.info("Optimizing Jobs...")

        new_jobs = run_optimizer(parsed_jobs)

        logger.info("New Jobs : %d", len(new_jobs))

        if not new_jobs:
            logger.info("No new jobs to publish.")
            return
            # ==========================================
        # Generate HTML
        # ==========================================

        logger.info("Generating HTML Pages...")

        summary = generate_all(new_jobs)

        logger.info("Generated : %d", summary.get("success", 0))

        # ==========================================
        # Update Homepage
        # ==========================================

        logger.info("Updating Homepage...")

        update_homepage(new_jobs)

        # ==========================================
        # Update Sitemap
        # ==========================================

        logger.info("Updating Sitemap...")

        update_sitemap(new_jobs)

        logger.info("=" * 60)
        logger.info("Publishing Completed Successfully")
        logger.info("=" * 60)

    except Exception as e:
        logger.exception("Fatal Error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
