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
import re
from datetime import datetime
from pathlib import Path
from filters import classify_post

logger = logging.getLogger("SearchIndexV5")

# ==========================================================
# Paths
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

BOT_DIR = Path(__file__).resolve().parent

DATABASE_FILE = PROJECT_ROOT / "database" / "jobs.json"

OUTPUT_FILE = PROJECT_ROOT / "search-index.json"

MAX_DESCRIPTION = 250
BASE_URL = "https://educationupdatehub.in"


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

def slugify(title, job=None):
    job = job or {}
    raw = safe(title).lower().strip().replace("&", " and ")
    raw = re.sub(r"\{\{.*?\}\}", "", raw)
    slug = re.sub(r"[^a-z0-9]+", "-", raw)
    slug = re.sub(r"-+", "-", slug).strip("-")
    if slug:
        if len(slug) > 150:
            import hashlib
            suffix=hashlib.sha1((raw+"|"+str(job.get("job_id",""))).encode("utf-8")).hexdigest()[:10]
            slug=slug[:139].rstrip("-")+"-"+suffix
        return slug
    cat=re.sub(r"[^a-z0-9]+","-",safe(job.get("category","government-jobs")).lower()).strip("-") or "government-jobs"
    years=re.findall(r"20\d{2}",safe(title)+" "+safe(job.get("year","")))
    year=years[-1] if years else str(datetime.now().year)
    jid=re.sub(r"[^a-z0-9]","",safe(job.get("job_id","")).lower())[-8:] or "update"
    return f"{cat}-{year}-{jid}"


def load_jobs():
    if not DATABASE_FILE.exists():
        logger.warning("Database not found: %s", DATABASE_FILE)
        return []
    try:
        with open(DATABASE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except Exception:
        logger.exception("Unable to load jobs database")
        return []


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
    slug = slugify(job.get("title"), job)
    return BASE_URL + "/generated/posts/" + slug + ".html"


# ==========================================================
# Build Search Item
# ==========================================================

def build_search_item(job):

    return {

        "title": safe(

            job.get("title")

        ),

        "slug": slugify(job.get("title"), job),

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
    for job in jobs or []:
        slug = slugify(job.get("title"), job)
        if not slug or slug in seen:
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

        if not title or title.lower() in INVALID_TITLES or len(title) < 5:
            continue
        if not classify_post(title, job.get("url", ""), job.get("description", ""), job.get("source", "")):
            continue
        slug = slugify(title, job)
        if not slug:
            continue
        if not (PROJECT_ROOT / "generated" / "posts" / f"{slug}.html").is_file():
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
