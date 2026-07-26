from pipeline import run_pipeline

from html_generator import generate_all

from homepage_updater import update_homepage

from sitemap_generator import update_sitemap

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

    update_homepage(jobs)

    update_sitemap(jobs)

    logger.info(
        "Publishing Completed"
    )
