from concurrent.futures import ThreadPoolExecutor, as_completed

from database import load_jobs, save_jobs
from optimizer import (
    optimize_jobs,
    add_timestamp,
    merge_jobs,
    filter_new_jobs
)
from summary import print_summary
from scraper import scrape_source
from utils.logger import logger
def scrape_all_sources(
    sources,
    workers=10
):

    jobs = []

    with ThreadPoolExecutor(
        max_workers=workers
    ) as executor:

        future_map = {

            executor.submit(
                scrape_source,
                source
            ): source

            for source in sources

        }

        for future in as_completed(future_map):

            source = future_map[future]

            try:

                data = future.result()

                if data:

                    jobs.extend(data)

            except Exception as e:

                logger.error(
                    "%s Failed",
                    source["name"]
                )

                logger.error(e)

    return jobs


def run_pipeline(sources):

    logger.info(
        "Pipeline Started"
    )

    jobs = scrape_all_sources(
        sources
    )

    jobs = optimize_jobs(jobs)

    jobs = add_timestamp(jobs)

    old_jobs = load_jobs()

    new_jobs = filter_new_jobs(
        old_jobs,
        jobs
    )

    # Merge only new jobs with old database
    final_jobs = merge_jobs(
        old_jobs,
        new_jobs
    )

    # Save merged database
    save_jobs(final_jobs)

    print_summary(final_jobs)

    logger.info(
        "Total Jobs : %d",
        len(final_jobs)
    )

    logger.info(
        "New Jobs : %d",
        len(new_jobs)
    )

    return final_jobs
