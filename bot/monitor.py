import logging

from scraper import production_runner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Education Update Hub Auto Publisher Started")
    logger.info("=" * 60)

    production_runner()

    logger.info("=" * 60)
    logger.info("Education Update Hub Auto Publisher Finished")
    logger.info("=" * 60)
