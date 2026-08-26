import logging
import os

from scraper import production_runner

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger=logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Education Update Hub Auto Publisher Started")
    logger.info("SOURCE BATCH=%s | WORKERS=%s | GENERIC_MAX=%s", os.getenv("EHU_SOURCE_BATCH_SIZE","40"), os.getenv("EHU_MAX_WORKERS","4"), os.getenv("EHU_GENERIC_MAX_CANDIDATES","12"))
    logger.info("=" * 60)
    try:
        production_runner()
    except KeyboardInterrupt:
        logger.warning("Execution interrupted")
    except Exception:
        logger.exception("Auto Publisher failed")
        raise
    finally:
        logger.info("Education Update Hub Auto Publisher Finished")
