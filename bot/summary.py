from utils.logger import logger


def print_summary(jobs):

    logger.info("=" * 60)

    logger.info(
        "Total Jobs : %d",
        len(jobs)
    )

    category = {}

    for job in jobs:

        c = job.get(
            "category",
            "Latest Jobs"
        )

        category[c] = category.get(c, 0) + 1

    for key, value in sorted(category.items()):

        logger.info(
            "%s : %d",
            key,
            value
        )

    logger.info("=" * 60)
