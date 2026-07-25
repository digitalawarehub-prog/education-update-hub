"""
=========================================================
Education Update Hub
Homepage Generator v2
Production Version
=========================================================
"""

import json
import logging
import os

from pathlib import Path
from datetime import datetime

logger = logging.getLogger("HomepageGenerator")

# --------------------------------------------------
# PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_FILE = BASE_DIR / "database" / "jobs.json"

INDEX_FILE = BASE_DIR / "index.html"

HEADER_FILE = BASE_DIR / "header.html"

SEARCH_DATA_FILE = BASE_DIR / "search-data.js"

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

    except Exception:

        return []

    jobs.sort(

        key=lambda x: (

            x.get("priority", 0),

            x.get("scraped_at", "")

        ),

        reverse=True

    )

    return jobs

# --------------------------------------------------
# DATE
# --------------------------------------------------

def new_badge(job):

    try:

        dt = datetime.fromisoformat(

            job["scraped_at"]

        )

        if (

            datetime.utcnow()

            - dt

        ).days <= NEW_DAYS:

            return '<span class="new-badge">NEW</span>'

    except Exception:

        pass

    return ""

# --------------------------------------------------
# HTML LINK
# --------------------------------------------------

def html_link(job):

    if job.get("html_file"):

        return job["html_file"]

    return os.path.basename(

        job.get("url", "#")

    )
    # =========================================================
# PART 2
# Marker Engine
# =========================================================

def replace_between_markers(

    html,

    start_marker,

    end_marker,

    content

):

    start = html.find(start_marker)

    end = html.find(end_marker)

    if start == -1:

        logger.warning(

            "Start Marker Missing : %s",

            start_marker

        )

        return html

    if end == -1:

        logger.warning(

            "End Marker Missing : %s",

            end_marker

        )

        return html

    start += len(start_marker)

    return (

        html[:start]

        + "\n"

        + content

        + "\n"

        + html[end:]

    )


# --------------------------------------------------------
# Latest Jobs Helper
# --------------------------------------------------------

def latest_jobs(

    jobs,

    limit

):

    return jobs[:limit]


# --------------------------------------------------------
# Category Filter
# --------------------------------------------------------

def jobs_by_category(

    jobs,

    category,

    limit=CATEGORY_LIMIT

):

    result = []

    for job in jobs:

        if job.get(

            "category"

        ) == category:

            result.append(job)

        if len(result) >= limit:

            break

    return result


# --------------------------------------------------------
# Image Helper
# --------------------------------------------------------

def card_image(job):

    return (

        job.get("image")

        or job.get("thumbnail")

        or job.get("featured_image")

        or DEFAULT_IMAGE

    )


# --------------------------------------------------------
# Date Helper
# --------------------------------------------------------

def publish_date(job):

    if job.get(

        "publish_date"

    ):

        return job["publish_date"]

    try:

        dt = datetime.fromisoformat(

            job["scraped_at"]

        )

        return dt.strftime(

            "%d %B %Y"

        )

    except Exception:

        return ""

logger.info(
    "Homepage Generator Part 2 Loaded"
)
# =========================================================
# PART 3
# Latest Update Cards Generator
# =========================================================

def latest_card(job):

    title = job.get(
        "title",
        "Latest Update"
    )

    image = card_image(job)

    link = html_link(job)

    date = publish_date(job)

    badge = new_badge(job)

    return f"""
<div class="latest-card">

<img src="{image}"
alt="{title}">

<h3>
{title}
{badge}
</h3>

<p>{date}</p>

<a href="{link}">
Read More →
</a>

</div>
"""


# --------------------------------------------------------

def latest_cards_html(jobs):

    cards = []

    for job in latest_jobs(

        jobs,

        LATEST_CARDS

    ):

        cards.append(

            latest_card(job)

        )

    return "\n".join(cards)


# --------------------------------------------------------

def update_latest_cards(

    index_html,

    jobs

):

    html = latest_cards_html(

        jobs

    )

    return replace_between_markers(

        index_html,

        "<!-- AUTO_LATEST_GRID_START -->",

        "<!-- AUTO_LATEST_GRID_END -->",

        html

    )


logger.info(
    "Homepage Generator Part 3 Loaded"
)
# =========================================================
# PART 4
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

    return (
        f'<li>'
        f'<a href="{link}">'
        f'{title} {badge}'
        f'</a>'
        f'</li>'
    )


# ---------------------------------------------------------
# Generate Latest Posts HTML
# ---------------------------------------------------------

def latest_posts_html(jobs):

    posts = latest_jobs(
        jobs,
        LATEST_POSTS
    )

    columns = [[] for _ in range(POST_COLUMNS)]

    for i, job in enumerate(posts):

        columns[i % POST_COLUMNS].append(
            latest_post_item(job)
        )

    html = []

    for column in columns:

        html.append(
            '<div class="post-column"><ul>'
        )

        html.extend(column)

        html.append(
            '</ul></div>'
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
    "Homepage Generator Part 4 Loaded"
)
# =========================================================
# PART 5
# Job Category Generator
# =========================================================

def category_html(jobs):

    html = []

    for job in jobs:

        html.append(

            f'<li><a href="{html_link(job)}">'

            f'{job.get("title")} '

            f'{new_badge(job)}'

            f'</a></li>'

        )

    return "\n".join(html)


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
    "Homepage Generator Part 5 Loaded"
)
