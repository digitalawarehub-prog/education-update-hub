# ==========================================================
# Production Testing Framework
# ==========================================================

from pathlib import Path
import json
import xml.etree.ElementTree as ET

BASE_DIR = Path(__file__).resolve().parent

DATABASE_FILE = BASE_DIR / "database" / "jobs.json"
SITEMAP_FILE = BASE_DIR / "generated" / "sitemap.xml"
POSTS_DIR = BASE_DIR / "generated" / "posts"
# ==========================================================
# Database Validation
# ==========================================================

def validate_database():

    if not DATABASE_FILE.exists():

        logger.error("Database Missing")

        return False

    try:

        with open(

            DATABASE_FILE,

            "r",

            encoding="utf-8"

        ) as f:

            jobs = json.load(f)

        logger.info(

            "Database OK (%d Jobs)",

            len(jobs)

        )

        return True

    except Exception:

        logger.exception(

            "Database Validation Failed"

        )

        return False
      # ==========================================================
# HTML Validation
# ==========================================================

def validate_html():

    if not POSTS_DIR.exists():

        return False

    html_files = list(

        POSTS_DIR.glob("*.html")

    )

    logger.info(

        "HTML Files : %d",

        len(html_files)

    )

    return len(html_files) > 0
  # ==========================================================
# Sitemap Validation
# ==========================================================

def validate_sitemap():

    try:

        ET.parse(SITEMAP_FILE)

        logger.info(

            "Sitemap OK"

        )

        return True

    except Exception:

        logger.exception(

            "Invalid Sitemap"

        )

        return False
      # ==========================================================
# Duplicate Detection
# ==========================================================

def detect_duplicates():

    with open(

        DATABASE_FILE,

        "r",

        encoding="utf-8"

    ) as f:

        jobs = json.load(f)

    urls = set()

    duplicates = []

    for job in jobs:

        url = job.get("url")

        if url in urls:

            duplicates.append(url)

        else:

            urls.add(url)

    logger.info(

        "Duplicate URLs : %d",

        len(duplicates)

    )

    return duplicates
  # ==========================================================
# End-to-End Test
# ==========================================================

def run_all_tests():

    logger.info("=" * 60)

    logger.info("Production Testing Started")

    logger.info("=" * 60)

    db = validate_database()

    html = validate_html()

    sitemap = validate_sitemap()

    duplicates = detect_duplicates()

    logger.info("")

    logger.info(

        "Database : %s",

        "PASS" if db else "FAIL"

    )

    logger.info(

        "HTML : %s",

        "PASS" if html else "FAIL"

    )

    logger.info(

        "Sitemap : %s",

        "PASS" if sitemap else "FAIL"

    )

    logger.info(

        "Duplicates : %d",

        len(duplicates)

    )

    logger.info("=" * 60)

    return (

        db

        and html

        and sitemap

        and len(duplicates) == 0

    )


logger.info(
    "Production Testing Ready"
)
