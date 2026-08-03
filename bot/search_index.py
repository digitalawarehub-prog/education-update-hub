"""
=========================================================
Education Update Hub
Search Index Generator V5
Part 1
Configuration + Helpers
=========================================================
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger("SearchIndexV5")

# ==========================================================
# Paths
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

BOT_DIR = Path(__file__).resolve().parent

DATABASE_FILE = PROJECT_ROOT / "database" / "jobs.json"

OUTPUT_FILE = PROJECT_ROOT / "search-index.json"

MAX_DESCRIPTION = 250


# ==========================================================
# Safe Value
# ==========================================================

def safe(value, default=""):

    if value is None:
        return default

    return str(value).strip()


# ==========================================================
# Slugify
# ==========================================================

def slugify(title):

    title = safe(title).lower()

    slug = []

    for ch in title:

        if ch.isalnum():

            slug.append(ch)

        else:

            slug.append("-")

    slug = "".join(slug)

    while "--" in slug:

        slug = slug.replace("--", "-")

    return slug.strip("-")


# ==========================================================
# Load Database
# ==========================================================

def load_jobs():

    if not DATABASE_FILE.exists():

        logger.warning(
            "jobs.json not found."
        )

        return []

    with open(
        DATABASE_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        try:

            jobs = json.load(file)

            logger.info(
                "Loaded %d Jobs",
                len(jobs)
            )

            return jobs

        except Exception:

            logger.exception(
                "Invalid jobs.json"
            )

            return []


logger.info(
    "Search Index Part 1 Loaded Successfully"
)
# ==========================================================
# Search Index Generator V5
# Part 2
# Build Search Records
# ==========================================================

BASE_URL = "https://educationupdatehub.in"


# ==========================================================
# Image Helper
# ==========================================================

def get_image(job):

    return (

        safe(job.get("featured_image"))

        or safe(job.get("thumbnail"))

        or safe(job.get("image"))

        or "images/default-job.png"

    )


# ==========================================================
# Build URL
# ==========================================================

def build_url(job):

    slug = safe(

        job.get("slug")

    )

    if not slug:

        slug = slugify(

            job.get("title")

        )

    return (

        BASE_URL

        + "/generated/posts/"

        + slug

        + ".html"

    )


# ==========================================================
# Build Search Item
# ==========================================================

def build_search_item(job):

    return {

        "title": safe(

            job.get("title")

        ),

        "slug": safe(

            job.get("slug")

        )

        or

        slugify(

            job.get("title")

        ),

        "url": build_url(job),

        "category": safe(

            job.get("category")

        ),

        "department": safe(

            job.get("department")

        ),

        "state": safe(

            job.get("state")

        ),

        "publish_date": safe(

            job.get("publish_date")

        ),

        "last_date": safe(

            job.get("last_date")

        ),

        "image": get_image(job),

        "description": safe(

            job.get("description")

        )[:MAX_DESCRIPTION]

    }


# ==========================================================
# Remove Duplicate Jobs
# ==========================================================

def unique_jobs(jobs):

    final = []

    seen = set()

    for job in jobs:

        slug = safe(

            job.get("slug")

        )

        if not slug:

            slug = slugify(

                job.get("title")

            )

        if slug in seen:

            continue

        seen.add(slug)

        final.append(job)

    return final


logger.info(
    "Search Index Part 2 Loaded Successfully"
)
# ==========================================================
# Search Index Generator V5
# Part 3
# Generate + Save + Validation
# ==========================================================

# ==========================================================
# Sort Jobs
# ==========================================================

def sort_jobs(jobs):

    return sorted(

        jobs,

        key=lambda x: safe(

            x.get("publish_date")

            or

            x.get("date")

        ),

        reverse=True

    )

# ==========================================================
# Generate Search Index
# ==========================================================

def generate_index():

    jobs = load_jobs()

    jobs = unique_jobs(jobs)

    jobs = sort_jobs(jobs)

    search_index = []

    # ==========================================================
    # Production Filter V5.1
    # ==========================================================

    INVALID_TITLES = {

        "",

        "support",

        "student",

        "results",

        "more",

        "more...",

        "support_agent support",

        "event student",

        "event key dates"

    }

    seen_urls = set()

    for job in jobs:

        title = safe(job.get("title")).strip()

        slug = safe(job.get("slug")).strip()

        if not title:
            continue

        if title.lower() in INVALID_TITLES:
            continue

        if len(title) < 5:
            continue

        if not slug:
            slug = slugify(title)

        if not slug:
            continue

        item = build_search_item(job)

        url = safe(item.get("url"))

        if (
            not url
            or url.endswith("/.html")
            or "generated/posts/.html" in url
        ):
            continue

        if url in seen_urls:
            continue

        seen_urls.add(url)

        search_index.append(item)

    return search_index

# ==========================================================
# Save Search Index
# ==========================================================

def save_index(search_index):

    with open(

        OUTPUT_FILE,

        "w",

        encoding="utf-8"

    ) as file:

        json.dump(

            search_index,

            file,

            ensure_ascii=False,

            indent=2

        )

    logger.info(

        "Search Index Saved : %d Records",

        len(search_index)

    )


# ==========================================================
# Statistics
# ==========================================================

def statistics(search_index):

    logger.info("=" * 60)

    logger.info("Search Index Statistics")

    logger.info("=" * 60)

    logger.info(

        "Total Records : %d",

        len(search_index)

    )

    logger.info(

        "Output File : %s",

        OUTPUT_FILE.name

    )

    logger.info("=" * 60)


# ==========================================================
# Validate Search Index
# ==========================================================

def validate(search_index):

    if not search_index:

        logger.warning(

            "Search Index Empty"

        )

        return False

    required = [

        "title",

        "url",

        "slug"

    ]

    for item in search_index:

        for field in required:

            if not safe(

                item.get(field)

            ):

                logger.warning(

                    "Missing %s",

                    field

                )

                return False

    logger.info(

        "Search Index Validation Passed"

    )

    return True


# ==========================================================
# Run Generator
# ==========================================================

def run():

    logger.info("Generating Search Index...")

    search_index = generate_index()

    print("Generated Records:", len(search_index))

    if not validate(search_index):
        return False

    save_index(search_index)

    statistics(search_index)

    return True

logger.info(
    "Search Index Part 3 Loaded Successfully"
)
# ==========================================================
# Direct Execution
# ==========================================================

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s - %(message)s"
    )

    result = run()

    print("Search Index Result:", result)
