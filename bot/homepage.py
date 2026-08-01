"""
=========================================================
Education Update Hub
Homepage Generator v3
Part 1
=========================================================
"""

import json
import logging

from pathlib import Path
from datetime import datetime

logger = logging.getLogger("HomepageGenerator")

# --------------------------------------------------
# PATHS
# --------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent.parent

DATABASE_FILE = ROOT_DIR / "database" / "jobs.json"

INDEX_FILE = ROOT_DIR / "index.html"

HEADER_FILE = ROOT_DIR / "header.html"

SEARCH_DATA_FILE = ROOT_DIR / "search-data.js"

# --------------------------------------------------
# SETTINGS
# --------------------------------------------------

LATEST_CARDS = 4
LATEST_POSTS = 15
CATEGORY_LIMIT = 6
BREAKING_LIMIT = 8
MARQUEE_LIMIT = 8
NEW_DAYS = 7

DEFAULT_IMAGE = "images/default-job.png"

# --------------------------------------------------
# FILE HELPERS
# --------------------------------------------------

def read_text(path):

    try:
        return path.read_text(
            encoding="utf-8"
        )

    except Exception as e:
        logger.exception(e)
        return ""


def write_text(path, text):

    path.write_text(
        text,
        encoding="utf-8"
    )

# --------------------------------------------------
# DATABASE
# --------------------------------------------------

def load_jobs():

    if not DATABASE_FILE.exists():
        return []

    try:

        jobs = json.loads(
            DATABASE_FILE.read_text(
                encoding="utf-8"
            )
        )

    except Exception as e:

        logger.exception(e)

        return []

    filtered = []

    for job in jobs:

        title = str(
            job.get("title", "")
        ).strip()

        title_lower = title.lower()

        # Skip template posts
        if (
            "{{" in title
            or "}}" in title
            or "translate" in title_lower
        ):
            continue

        # Skip junk pages
        if any(x in title_lower for x in [
            "notifications notices",
            "work recruitments",
            "notification board",
            "watch this video",
            "gallery",
            "photo",
            "video",
            "contact",
            "privacy",
            "policy",
            "chairman",
            "member"
        ]):
            continue

        filtered.append(job)

    filtered.sort(
        key=lambda x: (
            x.get("priority", 0),
            x.get("scraped_at", "")
        ),
        reverse=True
    )

    logger.info(
        "Homepage Jobs : %d",
        len(filtered)
    )

    return filtered
# =========================================================
# PART 2
# Latest Update Cards Generator
# =========================================================

def latest_card(job):

    title = job.get(
        "title",
        "Latest Update"
    )

    image = (
        job.get("featured_image")
        or job.get("thumbnail")
        or job.get("image")
        or DEFAULT_IMAGE
    )

    link = html_link(job)

    date = publish_date(job)

    badge = new_badge(job)

    category = job.get(
        "category",
        "Latest Jobs"
    )

    return f"""
<div class="latest-card">

<img src="{image}"
alt="{title}"
loading="lazy">

<div class="card-category">
{category}
</div>

<h3>
{title}
{badge}
</h3>

<p class="card-date">
📅 {date}
</p>

<a class="read-more-btn"
href="{link}">
Read More →
</a>

</div>
"""


# --------------------------------------------------------

def latest_cards_html(jobs):

    cards = []

    added = 0

    seen = set()

    for job in jobs:

        title = job.get(
            "title",
            ""
        ).strip()

        if not title:
            continue

        if title.lower() in seen:
            continue

        seen.add(
            title.lower()
        )

        cards.append(
            latest_card(job)
        )

        added += 1

        if added >= LATEST_CARDS:
            break

    return "\n".join(cards)


# --------------------------------------------------------

def update_latest_cards(
    index_html,
    jobs
):

    html = latest_cards_html(jobs)

    return replace_between_markers(

        index_html,

        "<!-- AUTO_LATEST_GRID_START -->",

        "<!-- AUTO_LATEST_GRID_END -->",

        html

    )


logger.info(
    "Homepage Generator Part 2 Loaded"
)
# =========================================================
# PART 3
# Latest Posts Generator
# =========================================================

POST_COLUMNS = 3


# ---------------------------------------------------------
# Single Post Item
# ---------------------------------------------------------

def latest_post_item(job):

    title = job.get(
        "title",
        "Latest Update"
    )

    link = html_link(job)

    badge = new_badge(job)

    category = job.get(
        "category",
        "Latest Jobs"
    )

    return f"""
<li>

<a href="{link}">

<span class="post-title">

{title}

</span>

{badge}

</a>

<div class="post-category">

{category}

</div>

</li>
"""


# ---------------------------------------------------------
# Generate Latest Posts HTML
# ---------------------------------------------------------

def latest_posts_html(jobs):

    columns = [[] for _ in range(POST_COLUMNS)]

    seen = set()

    count = 0

    for job in jobs:

        title = job.get(
            "title",
            ""
        ).strip()

        if not title:
            continue

        if title.lower() in seen:
            continue

        seen.add(
            title.lower()
        )

        columns[
            count % POST_COLUMNS
        ].append(

            latest_post_item(job)

        )

        count += 1

        if count >= LATEST_POSTS:
            break

    html = []

    for column in columns:

        html.append(
            '<div class="post-column"><ul>'
        )

        html.extend(column)

        html.append(
            "</ul></div>"
        )

    return "\n".join(html)


# ---------------------------------------------------------
# Update Latest Posts
# ---------------------------------------------------------

def update_latest_posts(
    index_html,
    jobs
):

    html = latest_posts_html(
        jobs
    )

    return replace_between_markers(

        index_html,

        "<!-- AUTO_POSTS_START -->",

        "<!-- AUTO_POSTS_END -->",

        html

    )


logger.info(
    "Homepage Generator Part 3 Loaded"
)
# =========================================================
# PART 4
# Job Category Generator
# =========================================================

CATEGORY_MAP = {
    "Latest Jobs": "Latest Jobs",
    "Results": "Results",
    "Admit Card": "Admit Card",
    "Answer Key": "Answer Key",
    "Scholarship": "Scholarship",
    "Syllabus": "Syllabus",
    "Government Schemes": "Government Schemes",
    "Uttarakhand Jobs": "Uttarakhand Jobs",
    "Central Government Jobs": "Central Government Jobs",
    "Other State Jobs": "Other State Jobs"
}


# ---------------------------------------------------------
# Category HTML
# ---------------------------------------------------------

def category_html(jobs):

    html = []

    seen = set()

    for job in jobs:

        title = job.get("title", "").strip()

        if not title:
            continue

        if title.lower() in seen:
            continue

        seen.add(title.lower())

        html.append(
            f'<li>'
            f'<a href="{html_link(job)}">'
            f'{title} {new_badge(job)}'
            f'</a>'
            f'</li>'
        )

    return "\n".join(html)


# ---------------------------------------------------------
# Filter Category
# ---------------------------------------------------------

def jobs_by_category(
    jobs,
    category,
    limit=CATEGORY_LIMIT
):

    result = []

    for job in jobs:

        job_category = CATEGORY_MAP.get(
            job.get("category", ""),
            job.get("category", "")
        )

        if job_category != category:
            continue

        result.append(job)

        if len(result) >= limit:
            break

    return result


# ---------------------------------------------------------
# Update Uttarakhand Jobs
# ---------------------------------------------------------

def update_uk_jobs(index_html, jobs):

    html = category_html(

        jobs_by_category(
            jobs,
            "Uttarakhand Jobs"
        )

    )

    return replace_between_markers(

        index_html,

        "<!-- AUTO_UK_JOBS_START -->",

        "<!-- AUTO_UK_JOBS_END -->",

        html

    )


# ---------------------------------------------------------
# Update Central Jobs
# ---------------------------------------------------------

def update_central_jobs(index_html, jobs):

    html = category_html(

        jobs_by_category(
            jobs,
            "Central Government Jobs"
        )

    )

    return replace_between_markers(

        index_html,

        "<!-- AUTO_CENTRAL_JOBS_START -->",

        "<!-- AUTO_CENTRAL_JOBS_END -->",

        html

    )


# ---------------------------------------------------------
# Update Other State Jobs
# ---------------------------------------------------------

def update_state_jobs(index_html, jobs):

    html = category_html(

        jobs_by_category(
            jobs,
            "Other State Jobs"
        )

    )

    return replace_between_markers(

        index_html,

        "<!-- AUTO_STATE_JOBS_START -->",

        "<!-- AUTO_STATE_JOBS_END -->",

        html

    )


logger.info(
    "Homepage Generator Part 4 Loaded"
)
# =========================================================
# PART 5
# Homepage Update Engine
# =========================================================

def update_homepage(new_jobs=None):

    logger.info("=" * 60)
    logger.info("Homepage Generator Started")
    logger.info("=" * 60)

    try:

        jobs = new_jobs if new_jobs else load_jobs()

        if not jobs:
            logger.warning("No Jobs Found")
            return False

        # Remove duplicate titles
        unique = []
        seen = set()

        for job in jobs:

            title = job.get("title", "").strip().lower()

            if not title:
                continue

            if title in seen:
                continue

            seen.add(title)

            unique.append(job)

        jobs = unique

        logger.info(
            "Homepage Jobs : %d",
            len(jobs)
        )

        # ------------------------------
        # Header
        # ------------------------------

        update_header(jobs)

        # ------------------------------
        # Homepage
        # ------------------------------

        index_html = read_text(INDEX_FILE)

        if not index_html:

            logger.error(
                "index.html Not Found"
            )

            return False

        # Latest Cards

        index_html = update_latest_cards(
            index_html,
            jobs
        )

        # Latest Posts

        index_html = update_latest_posts(
            index_html,
            jobs
        )

        # Categories

        index_html = update_uk_jobs(
            index_html,
            jobs
        )

        index_html = update_central_jobs(
            index_html,
            jobs
        )

        index_html = update_state_jobs(
            index_html,
            jobs
        )

        # Popular Search

        index_html = update_popular_search(
            index_html,
            jobs
        )

        # Save Homepage

        write_text(
            INDEX_FILE,
            index_html
        )

        # Search Data

        generate_search_data(
            jobs
        )

        logger.info("=" * 60)
        logger.info("Homepage Updated Successfully")
        logger.info("=" * 60)

        return True

    except Exception as e:

        logger.exception(e)

        return False


# =========================================================
# Final Wrapper
# =========================================================

_old_update_homepage = update_homepage


def update_homepage(new_jobs=None):

    result = _old_update_homepage(new_jobs)

    if result:

        jobs = (
            new_jobs
            if new_jobs
            else load_jobs()
        )

        homepage_stats(jobs)

    return result


logger.info(
    "Homepage Generator v3 Loaded Successfully"
)
