# ==========================================================
# Search Engine V4
# Part 1 : Imports + Configuration + Helpers
# ==========================================================

import json
import re
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("SearchEngineV4")

ROOT_DIR = Path(__file__).resolve().parent.parent

POSTS_DIR = ROOT_DIR / "generated" / "posts"

SEARCH_DATA_FILE = ROOT_DIR / "search-data.js"

BASE_URL = "https://educationupdatehub.in"

DEFAULT_IMAGE = "images/default-job.png"

# ==========================================================
# Safe Value
# ==========================================================

def safe(value, default=""):

    if value is None:
        return default

    return str(value).strip()


# ==========================================================
# Slug Generator
# ==========================================================

def slugify(title):

    title = safe(title).lower()

    title = re.sub(r"[^a-z0-9]+", "-", title)

    title = re.sub(r"-+", "-", title)

    return title.strip("-")


# ==========================================================
# Image Helper
# ==========================================================

def get_image(job):

    return (
        job.get("featured_image")
        or job.get("thumbnail")
        or job.get("image")
        or DEFAULT_IMAGE
    )


# ==========================================================
# Search Keywords
# ==========================================================

def build_keywords(job):

    keywords = []

    fields = [
        "title",
        "category",
        "department",
        "qualification",
        "description",
        "content"
    ]

    for field in fields:

        value = safe(job.get(field))

        if value:

            keywords.extend(
                value.lower().split()
            )

    return sorted(set(keywords))


# ==========================================================
# Search Record
# ==========================================================

def build_record(job):

    title = safe(job.get("title"))

    slug = slugify(title)

    return {

        "title": title,

        "category": safe(
            job.get("category")
        ),

        "description": safe(
            job.get("description")
        ),

        "image": get_image(job),

        "url":
        f"generated/posts/{slug}.html",

        "keywords":
        build_keywords(job)

    }


logger.info(
    "Search Engine V4 Part 1 Loaded Successfully"
)
# ==========================================================
# Search Engine V4
# Part 2 : Search Index Generator
# ==========================================================

def remove_duplicates(records):

    unique = []

    seen = set()

    for record in records:

        url = record["url"]

        if url in seen:
            continue

        seen.add(url)

        unique.append(record)

    return unique


# ==========================================================
# Sort Records
# ==========================================================

def sort_records(records):

    return sorted(
        records,
        key=lambda x: x["title"].lower()
    )


# ==========================================================
# Build Search Index
# ==========================================================

def build_search_index(jobs):

    records = []

    for job in jobs:

        title = safe(job.get("title"))

        if not title:
            continue

        records.append(
            build_record(job)
        )

    records = remove_duplicates(records)

    records = sort_records(records)

    logger.info(
        "Search Records : %d",
        len(records)
    )

    return records


# ==========================================================
# Search Statistics
# ==========================================================

def search_statistics(records):

    logger.info("=" * 50)

    logger.info(
        "Total Search Records : %d",
        len(records)
    )

    categories = {}

    for item in records:

        cat = item["category"]

        categories[cat] = (
            categories.get(cat, 0) + 1
        )

    for cat, total in sorted(categories.items()):

        logger.info(
            "%s : %d",
            cat,
            total
        )

    logger.info("=" * 50)


logger.info(
    "Search Engine V4 Part 2 Loaded Successfully"
)
# ==========================================================
# Search Engine V4
# Part 3 : Search Data Exporter
# ==========================================================

def build_search_json(records):

    return json.dumps(
        records,
        ensure_ascii=False,
        indent=2
    )


# ==========================================================
# JavaScript Wrapper
# ==========================================================

def build_search_js(records):

    json_data = build_search_json(records)

    return (
        "const SEARCH_DATA = "
        + json_data
        + ";\n\n"
        + "window.SEARCH_DATA = SEARCH_DATA;"
    )


# ==========================================================
# Write search-data.js
# ==========================================================

def write_search_data(records):

    javascript = build_search_js(records)

    with open(
        SEARCH_DATA_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(javascript)

    logger.info(
        "search-data.js generated successfully."
    )

    return SEARCH_DATA_FILE


# ==========================================================
# Generate Search Data
# ==========================================================

def generate_search_data(jobs):

    records = build_search_index(jobs)

    search_statistics(records)

    filepath = write_search_data(records)

    logger.info(
        "Search database exported : %s",
        filepath.name
    )

    return filepath


# ==========================================================
# Preview Records
# ==========================================================

def preview_records(records, limit=5):

    logger.info("=" * 50)

    logger.info(
        "Preview : First %d Records",
        limit
    )

    logger.info("=" * 50)

    for record in records[:limit]:

        logger.info(
            "%s -> %s",
            record["title"],
            record["url"]
        )

    logger.info("=" * 50)


logger.info(
    "Search Engine V4 Part 3 Loaded Successfully"
)
# ==========================================================
# Search Engine V4
# Part 4 : Fast Search + Relevance Engine
# ==========================================================

def calculate_score(record, query):

    score = 0

    query = safe(query).lower()

    title = record["title"].lower()

    description = record["description"].lower()

    category = record["category"].lower()

    keywords = " ".join(
        record["keywords"]
    )

    # Exact title match
    if query == title:
        score += 100

    # Title contains query
    elif query in title:
        score += 60

    # Category match
    if query in category:
        score += 30

    # Description match
    if query in description:
        score += 20

    # Keyword match
    if query in keywords:
        score += 15

    return score


# ==========================================================
# Filter By Category
# ==========================================================

def filter_category(records, category):

    if not category:
        return records

    category = category.lower()

    return [

        record

        for record in records

        if category in record["category"].lower()

    ]


# ==========================================================
# Search Records
# ==========================================================

def search_records(

    records,

    query,

    category=None

):

    query = safe(query)

    if not query:

        return []

    records = filter_category(

        records,

        category

    )

    results = []

    for record in records:

        score = calculate_score(

            record,

            query

        )

        if score > 0:

            item = record.copy()

            item["score"] = score

            results.append(item)

    results.sort(

        key=lambda x: x["score"],

        reverse=True

    )

    return results


# ==========================================================
# Preview Search
# ==========================================================

def preview_search(

    records,

    query,

    limit=10

):

    results = search_records(

        records,

        query

    )

    logger.info("=" * 50)

    logger.info(

        "Search : %s",

        query

    )

    logger.info("=" * 50)

    for row in results[:limit]:

        logger.info(

            "%3d | %s",

            row["score"],

            row["title"]

        )

    logger.info("=" * 50)


logger.info(
    "Search Engine V4 Part 4 Loaded Successfully"
)
# ==========================================================
# Search Engine V4
# Part 5 : Fuzzy Search + Synonyms + Ranking
# ==========================================================

# Common Search Synonyms
SEARCH_SYNONYMS = {

    "job": [
        "jobs",
        "recruitment",
        "vacancy",
        "notification"
    ],

    "result": [
        "results",
        "scorecard",
        "merit"
    ],

    "admit": [
        "hall ticket",
        "admit card"
    ],

    "answer": [
        "answer key",
        "key"
    ],

    "scholarship": [
        "scheme",
        "financial aid"
    ]

}


# ==========================================================
# Expand Query
# ==========================================================

def expand_query(query):

    query = safe(query).lower()

    words = query.split()

    expanded = set(words)

    for word in words:

        if word in SEARCH_SYNONYMS:

            expanded.update(
                SEARCH_SYNONYMS[word]
            )

    return expanded


# ==========================================================
# Fuzzy Score
# ==========================================================

def fuzzy_score(record, query):

    expanded = expand_query(query)

    searchable = " ".join([

        record["title"],

        record["description"],

        record["category"],

        " ".join(record["keywords"])

    ]).lower()

    score = 0

    for word in expanded:

        if word in searchable:

            score += 10

    return score


# ==========================================================
# Improved Search
# ==========================================================

def advanced_search(

    records,

    query,

    category=None

):

    results = search_records(

        records,

        query,

        category

    )

    if results:

        return results

    fallback = []

    for record in records:

        score = fuzzy_score(

            record,

            query

        )

        if score > 0:

            item = record.copy()

            item["score"] = score

            fallback.append(item)

    fallback.sort(

        key=lambda x: x["score"],

        reverse=True

    )

    return fallback


# ==========================================================
# Top Results
# ==========================================================

def top_results(

    records,

    query,

    limit=10

):

    results = advanced_search(

        records,

        query

    )

    return results[:limit]


logger.info(
    "Search Engine V4 Part 5 Loaded Successfully"
)
# ==========================================================
# Search Engine V4
# Part 6 : Validation + Statistics + Final Runner
# ==========================================================

def validate_search_data(records):

    logger.info("=" * 60)
    logger.info("Search Validation")
    logger.info("=" * 60)

    if not records:

        logger.warning(
            "No Search Records Found."
        )

        return False

    urls = set()

    duplicate = 0

    for record in records:

        url = record["url"]

        if url in urls:
            duplicate += 1

        urls.add(url)

    logger.info(
        "Total Records : %d",
        len(records)
    )

    logger.info(
        "Duplicate Records : %d",
        duplicate
    )

    logger.info("=" * 60)

    return duplicate == 0


# ==========================================================
# Search File Statistics
# ==========================================================

def search_file_statistics():

    if not SEARCH_DATA_FILE.exists():

        logger.warning(
            "search-data.js not found."
        )

        return

    size = SEARCH_DATA_FILE.stat().st_size / 1024

    logger.info("=" * 60)

    logger.info(
        "Search Database"
    )

    logger.info("=" * 60)

    logger.info(
        "File : %s",
        SEARCH_DATA_FILE.name
    )

    logger.info(
        "Size : %.2f KB",
        size
    )

    logger.info(
        "Generated : %s",
        datetime.now().strftime(
            "%d-%m-%Y %H:%M:%S"
        )
    )

    logger.info("=" * 60)


# ==========================================================
# Build Search Database
# ==========================================================

def build_search(jobs):

    logger.info(
        "Generating Search Database..."
    )

    records = build_search_index(jobs)

    validate_search_data(records)

    search_statistics(records)

    preview_records(records)

    filepath = write_search_data(records)

    search_file_statistics()

    logger.info(
        "Search Database Generated Successfully."
    )

    return filepath


# ==========================================================
# Main Runner
# ==========================================================

def run(jobs):

    try:

        return build_search(jobs)

    except Exception as e:

        logger.exception(
            "Search Engine Error : %s",
            e
        )

        return None


logger.info("=" * 60)
logger.info("Search Engine V4 Loaded Successfully")
logger.info("=" * 60)
