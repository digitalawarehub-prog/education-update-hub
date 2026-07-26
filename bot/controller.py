from automation import publish
from scraper import load_sources
from utils.logger import logger


def start():

    logger.info("=" * 60)
    logger.info("Education Update Hub Production v4")
    logger.info("=" * 60)

    sources = load_sources()

    if not sources:

        logger.warning("No Sources Found")

        return

    publish(sources)

    logger.info("=" * 60)
    logger.info("Completed Successfully")
    logger.info("=" * 60)


if __name__ == "__main__":

    start()
