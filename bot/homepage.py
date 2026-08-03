# ==========================================================
# Homepage Generator V4
# Part 1 : Imports + Configuration + Helpers
# ==========================================================

import os
import re
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("HomepageGeneratorV4")

ROOT_DIR = Path(__file__).resolve().parent.parent

INDEX_FILE = ROOT_DIR / "index.html"

POSTS_DIR = ROOT_DIR / "generated" / "posts"

BASE_URL = "https://educationupdatehub.in"

# ==========================================================
# Homepage Sections
# ==========================================================

SECTIONS = {

    "AUTO_LATEST_GRID": [],

    "AUTO_LATEST_POSTS": [],

    "AUTO_UK_JOBS": [],

    "AUTO_CENTRAL_JOBS": [],

    "AUTO_STATE_JOBS": []

}

# ==========================================================
# Create Slug
# ==========================================================

def slugify(title):

    title = str(title).lower().strip()

    title = re.sub(r"[^a-z0-9]+", "-", title)

    title = re.sub(r"-+", "-", title)

    return title.strip("-")

# ==========================================================
# Safe Value
# ==========================================================

def safe(value, default=""):

    if value is None:
        return default

    return str(value).strip()

# ==========================================================
# Image Helper
# ==========================================================

def get_image(job):

    return (
        job.get("featured_image")
        or job.get("thumbnail")
        or job.get("image")
        or "images/default-job.png"
    )

# ==========================================================
# Category Helper
# ==========================================================

def category(job):

    return safe(
        job.get("category"),
        "Latest Jobs"
    )

# ==========================================================
# Date Helper
# ==========================================================

def publish_date(job):

    return safe(
        job.get("publish_date") or job.get("date")
            datetime.today().strftime("%d %B %Y")
        )
    )

logger.info(
    "Homepage Generator V4 Part 1 Loaded"
)
# ==========================================================
# Homepage Generator V4
# Part 2 : Homepage Card Builder
# ==========================================================

def build_homepage_card(job):

    title = safe(job.get("title"))

    image = get_image(job)

    slug = slugify(title)

    category_name = category(job)

    last_date = safe(
        job.get("last_date")
        or job.get("date"),
        "Check Notification"
    )

    return f"""
<div class="post-card">

    <a href="generated/posts/{slug}.html">

        <img
            src="{image}"
            alt="{title}"
            loading="lazy">

    </a>

    <div class="post-content">

        <span class="post-category">

            {category_name}

        </span>

        <h3>

            <a href="generated/posts/{slug}.html">

                {title}

            </a>

        </h3>

        <p class="post-date">

            📅 Last Date : {last_date}

        </p>

        <a
            class="read-more-btn"
            href="generated/posts/{slug}.html">

            Read More →

        </a>

    </div>

</div>
"""


# ==========================================================
# Sidebar Job List Item
# ==========================================================

def build_job_item(job):

    title = safe(job.get("title"))

    slug = slugify(title)

    return f"""
<li>

    <a href="generated/posts/{slug}.html">

        {title}

    </a>

</li>
"""


# ==========================================================
# Latest Posts Card
# ==========================================================

def build_latest_post(job):

    title = safe(job.get("title"))

    slug = slugify(title)

    image = get_image(job)

    return f"""
<div class="latest-post-card">

    <a href="generated/posts/{slug}.html">

        <img
            src="{image}"
            alt="{title}"
            loading="lazy">

        <h3>

            {title}

        </h3>

    </a>

</div>
"""


logger.info(
    "Homepage Generator V4 Part 2 Loaded Successfully"
)
# ==========================================================
# Homepage Generator V4
# Part 3 : Category Mapping & Auto Sections
# ==========================================================

def clear_sections():

    for section in SECTIONS:

        SECTIONS[section].clear()


# ==========================================================
# Add HTML To Section
# ==========================================================

def add_to_section(section, html):

    if section in SECTIONS:

        SECTIONS[section].append(html)


# ==========================================================
# Register Job
# ==========================================================

def register_job(job):

    card = build_homepage_card(job)

    latest_post = build_latest_post(job)

    job_item = build_job_item(job)

    # Latest Updates
    add_to_section(
        "AUTO_LATEST_GRID",
        card
    )

    # Latest Posts
    add_to_section(
        "AUTO_LATEST_POSTS",
        latest_post
    )

    category_name = category(job).lower()
    department = safe(
        job.get("department")
    ).lower()
    # Uttarakhand Jobs
    if (
        "uttarakhand" in category_name
        or "uk" in category_name
    ):

        add_to_section(
            "AUTO_UK_JOBS",
            job_item
        )

    # Central Government Jobs
    elif (
        "central" in category_name
        or "upsc" in category_name
        or "ssc" in category_name
        or "banking" in department
        or "railway" in department
        or "defence" in department
        or "government" in department
    ):

        add_to_section(
            "AUTO_CENTRAL_JOBS",
            job_item
        )

    # Other State Jobs
    else:

        add_to_section(
            "AUTO_STATE_JOBS",
            job_item
        )


# ==========================================================
# Register All Jobs
# ==========================================================

def register_jobs(jobs):

    clear_sections()

    seen = set()

    for job in jobs:

        title = safe(
            job.get("title")
        )

        if not title:
            continue

        slug = slugify(title)

        if slug in seen:
            continue

        seen.add(slug)

        register_job(job)


logger.info(
    "Homepage Generator V4 Part 3 Loaded Successfully"
)
# ==========================================================
# Homepage Generator V4
# Part 4 : Homepage Update Engine
# ==========================================================

def replace_auto_section(content, marker, items):

    start_marker = f"<!-- {marker}_START -->"
    end_marker = f"<!-- {marker}_END -->"

    if start_marker not in content:
        return content

    if end_marker not in content:
        return content

    before = content.split(start_marker)[0]

    after = content.split(end_marker)[1]

    middle = (
        start_marker
        + "\n\n"
        + "\n".join(items)
        + "\n\n"
        + end_marker
    )

    return before + middle + after


# ==========================================================
# Update Homepage
# ==========================================================

def update_homepage():

    if not INDEX_FILE.exists():

        logger.error(
            "index.html not found."
        )

        return False

    with open(
        INDEX_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        html = file.read()

    html = replace_auto_section(
        html,
        "AUTO_LATEST_GRID",
        SECTIONS["AUTO_LATEST_GRID"]
    )

    html = replace_auto_section(
        html,
        "AUTO_LATEST_POSTS",
        SECTIONS["AUTO_LATEST_POSTS"]
    )

    html = replace_auto_section(
        html,
        "AUTO_UK_JOBS",
        SECTIONS["AUTO_UK_JOBS"]
    )

    html = replace_auto_section(
        html,
        "AUTO_CENTRAL_JOBS",
        SECTIONS["AUTO_CENTRAL_JOBS"]
    )

    html = replace_auto_section(
        html,
        "AUTO_STATE_JOBS",
        SECTIONS["AUTO_STATE_JOBS"]
    )

    with open(
        INDEX_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(html)

    logger.info(
        "Homepage Updated Successfully."
    )

    return True


# ==========================================================
# Preview
# ==========================================================

def homepage_summary():

    logger.info("=" * 50)

    logger.info("Homepage Summary")

    logger.info(
        "Latest Grid : %d",
        len(SECTIONS["AUTO_LATEST_GRID"])
    )

    logger.info(
        "Latest Posts : %d",
        len(SECTIONS["AUTO_LATEST_POSTS"])
    )

    logger.info(
        "UK Jobs : %d",
        len(SECTIONS["AUTO_UK_JOBS"])
    )

    logger.info(
        "Central Jobs : %d",
        len(SECTIONS["AUTO_CENTRAL_JOBS"])
    )

    logger.info(
        "Other State Jobs : %d",
        len(SECTIONS["AUTO_STATE_JOBS"])
    )

    logger.info("=" * 50)


logger.info(
    "Homepage Generator V4 Part 4 Loaded Successfully"
)
# ==========================================================
# Homepage Generator V4
# Part 5 : Sorting + Featured + Generate Homepage
# ==========================================================

MAX_LATEST_GRID = 24
MAX_LATEST_POSTS = 12
MAX_UK_JOBS = 15
MAX_CENTRAL_JOBS = 15
MAX_STATE_JOBS = 15


# ==========================================================
# Sort Jobs (Latest First)
# ==========================================================

def sort_jobs(jobs):

    def sort_key(job):

        return safe(
            job.get("publish_date"),
            "9999-12-31"
        )

    return sorted(
        jobs,
        key=sort_key,
        reverse=True
    )


# ==========================================================
# Remove Duplicate Jobs
# ==========================================================

def unique_jobs(jobs):

    unique = []

    seen = set()

    for job in jobs:

        slug = slugify(
            safe(job.get("title"))
        )

        if slug in seen:
            continue

        seen.add(slug)

        unique.append(job)

    return unique


# ==========================================================
# Apply Section Limits
# ==========================================================

def apply_limits():

    SECTIONS["AUTO_LATEST_GRID"] = \
        SECTIONS["AUTO_LATEST_GRID"][:MAX_LATEST_GRID]

    SECTIONS["AUTO_LATEST_POSTS"] = \
        SECTIONS["AUTO_LATEST_POSTS"][:MAX_LATEST_POSTS]

    SECTIONS["AUTO_UK_JOBS"] = \
        SECTIONS["AUTO_UK_JOBS"][:MAX_UK_JOBS]

    SECTIONS["AUTO_CENTRAL_JOBS"] = \
        SECTIONS["AUTO_CENTRAL_JOBS"][:MAX_CENTRAL_JOBS]

    SECTIONS["AUTO_STATE_JOBS"] = \
        SECTIONS["AUTO_STATE_JOBS"][:MAX_STATE_JOBS]


# ==========================================================
# Generate Homepage
# ==========================================================

def generate_homepage(jobs):

    jobs = unique_jobs(jobs)

    jobs = sort_jobs(jobs)

    register_jobs(jobs)

    apply_limits()

    update_homepage()

    homepage_summary()

    logger.info(
        "Homepage Generated Successfully."
    )

    return True


logger.info(
    "Homepage Generator V4 Part 5 Loaded Successfully"
)
# ==========================================================
# Homepage Generator V4
# Part 6 : Validation + Statistics + Final Build
# ==========================================================

def validate_sections():

    total = 0

    logger.info("=" * 60)
    logger.info("Homepage Validation")
    logger.info("=" * 60)

    for name, items in SECTIONS.items():

        count = len(items)

        total += count

        logger.info(
            "%-25s : %d",
            name,
            count
        )

    logger.info("=" * 60)

    logger.info(
        "Total Homepage Items : %d",
        total
    )

    logger.info("=" * 60)

    return total


# ==========================================================
# Homepage Statistics
# ==========================================================

def homepage_statistics():

    if not INDEX_FILE.exists():

        logger.warning(
            "Homepage file not found."
        )

        return

    size = INDEX_FILE.stat().st_size / 1024

    logger.info("=" * 60)
    logger.info("Homepage Statistics")
    logger.info("=" * 60)

    logger.info(
        "Homepage File : %s",
        INDEX_FILE.name
    )

    logger.info(
        "File Size : %.2f KB",
        size
    )

    logger.info(
        "Generated Time : %s",
        datetime.now().strftime(
            "%d-%m-%Y %H:%M:%S"
        )
    )

    logger.info("=" * 60)


# ==========================================================
# Build Homepage
# ==========================================================

def build_homepage(jobs):

    logger.info(
        "Starting Homepage Generation..."
    )

    success = generate_homepage(jobs)

    if not success:

        logger.error(
            "Homepage Generation Failed."
        )

        return False

    validate_sections()

    homepage_statistics()

    logger.info(
        "Homepage Build Completed Successfully."
    )

    return True


# ==========================================================
# Main Entry
# ==========================================================

def run(jobs):

    try:

        return build_homepage(jobs)

    except Exception as e:

        logger.exception(
            "Homepage Generator Error : %s",
            e
        )

        return False


logger.info("=" * 60)
logger.info("Homepage Generator V4 Loaded Successfully")
logger.info("=" * 60)
