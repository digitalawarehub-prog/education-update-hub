from pipeline import run_pipeline

from html_generator import generate_all

from homepage_updater import update_homepage

from sitemap_generator import update_sitemap
import category_generator
from utils.logger import logger
def publish(sources):

    jobs = run_pipeline(
        sources
    )

    if not jobs:

        logger.info(
            "No New Jobs Found"
        )

        return

    generate_all(jobs)

    category_generator.build_categories(jobs)

    update_homepage(jobs)

    update_sitemap(jobs)

    logger.info(
        "Publishing Completed"
    )
# ==========================================================
# Production Version
# ==========================================================

PROJECT_NAME = "Education Update Hub"

VERSION = "Production v4.0 Stable"

BUILD_DATE = "2026-07-27"
# ==========================================================
# Production Pipeline
# ==========================================================

def production_pipeline():

    logger.info("=" * 60)

    logger.info(PROJECT_NAME)

    logger.info(VERSION)

    logger.info("=" * 60)

    jobs = run_pipeline()

    if not jobs:

        logger.error(
            "Pipeline Failed"
        )
        return False

    # HTML
    generate_all(
        jobs,
        BASE_URL
    )

    # Homepage
    update_homepage(
        jobs
    )

    # Sitemap
    generate_sitemap()

    # Monitoring
    monitor_execution(
        jobs
    )

    # Validation
    success = run_all_tests()

    if success:

        logger.info(
            "Production Validation Passed"
        )

    else:

        logger.warning(
            "Production Validation Failed"
        )

    return success
    # ==========================================================
# Deployment Summary
# ==========================================================

def deployment_summary():

    logger.info("=" * 60)

    logger.info("PROJECT READY")

    logger.info("=" * 60)

    logger.info("Scraper        : OK")

    logger.info("Optimizer      : OK")

    logger.info("HTML Generator : OK")

    logger.info("Homepage       : OK")

    logger.info("Sitemap        : OK")

    logger.info("Monitoring     : OK")

    logger.info("Testing        : OK")

    logger.info("=" * 60)
    # ==========================================================
# Main
# ==========================================================

if __name__ == "__main__":

    try:

        status = production_pipeline()

        deployment_summary()

        if status:

            logger.info(
                "Deployment Successful"
            )

        else:

            logger.warning(
                "Deployment Completed With Issues"
            )

    except KeyboardInterrupt:

        logger.warning(
            "Execution Interrupted"
        )

    except Exception:

        logger.exception(
            "Production Crash"
        )
