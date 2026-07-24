"""
=========================================================
Education Update Hub
Homepage Generator v1.0
Part 1
=========================================================
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime

# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_DIR = BASE_DIR / "database"

DATABASE_FILE = DATABASE_DIR / "jobs.json"

INDEX_FILE = BASE_DIR / "index.html"

HEADER_FILE = BASE_DIR / "header.html"

FOOTER_FILE = BASE_DIR / "footer.html"

GENERATED_DIR = BASE_DIR / "generated"

# =========================================================
# LOGGING
# =========================================================

logger = logging.getLogger("HomepageGenerator")

# =========================================================
# CONSTANTS
# =========================================================

LATEST_CARDS = 4

LATEST_POSTS = 15

BREAKING_NEWS = 8

MARQUEE_POSTS = 8

NEW_DAYS = 7

# =========================================================
# FILE HELPERS
# =========================================================

def read_text(path):

    try:

        with open(path, "r", encoding="utf-8") as f:

            return f.read()

    except Exception as e:

        logger.error("Cannot Read %s", path)

        logger.error(e)

        return ""


def write_text(path, data):

    try:

        with open(path, "w", encoding="utf-8") as f:

            f.write(data)

        return True

    except Exception as e:

        logger.error("Cannot Write %s", path)

        logger.error(e)

        return False

# =========================================================
# DATABASE
# =========================================================

def load_jobs():

    if not DATABASE_FILE.exists():

        return []

    try:

        with open(
            DATABASE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            jobs = json.load(f)

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

# =========================================================
# DATE HELPERS
# =========================================================

def is_new(job):

    scraped = job.get("scraped_at")

    if not scraped:

        return False

    try:

        dt = datetime.fromisoformat(scraped)

    except Exception:

        return False

    return (datetime.utcnow() - dt).days <= NEW_DAYS


def new_badge(job):

    if is_new(job):

        return '<span class="new-badge">NEW</span>'

    return ""

# =========================================================
# LINK HELPERS
# =========================================================

def html_link(job):

    url = job.get("html_file")

    if url:

        return url

    url = job.get("url", "")

    if url.endswith(".html"):

        return os.path.basename(url)

    slug = (
        job.get("title", "")
        .lower()
        .replace(" ", "-")
        .replace("/", "-")
    )

    return f"{slug}.html"

# =========================================================
# FILTERS
# =========================================================

def latest_jobs(jobs, limit):

    return jobs[:limit]


def jobs_by_category(jobs, category):

    output = []

    for job in jobs:

        if job.get("category") == category:

            output.append(job)

    return output

# =========================================================
# STARTUP
# =========================================================

logger.info("Homepage Generator Loaded")
# =========================================================
# PART 2
# Breaking News & Header Marquee Generator
# =========================================================

def make_marquee_links(jobs, limit=MARQUEE_POSTS):

    html = []

    for job in latest_jobs(jobs, limit):

        title = job.get("title", "Latest Update")

        link = html_link(job)

        badge = new_badge(job)

        html.append(
            f'''
<a href="{link}">
🔥 {title} {badge}
</a>
&nbsp;&nbsp;|&nbsp;&nbsp;
'''
        )

    return "\n".join(html)


# ---------------------------------------------------------

def make_breaking_news(jobs, limit=BREAKING_NEWS):

    html = []

    for job in latest_jobs(jobs, limit):

        title = job.get("title", "Latest Update")

        link = html_link(job)

        badge = new_badge(job)

        html.append(
            f'''
🔴 <a href="{link}">
{title} {badge}
</a>
&nbsp; | &nbsp;
'''
        )

    return "\n".join(html)


# ---------------------------------------------------------

def update_header(jobs):

    logger.info("Updating Header")

    header = read_text(HEADER_FILE)

    if not header:

        return

    marquee_html = make_marquee_links(jobs)

    breaking_html = make_breaking_news(jobs)

    # -------------------------------------------------
    # Replace Top Marquee
    # -------------------------------------------------

    if "<div class=\"top-news\">" in header:

        start = header.find("<div class=\"top-news\">")

        end = header.find("</div>", start)

        if start != -1 and end != -1:

            block = f'''
<div class="top-news">
<marquee scrollamount="5"
onmouseover="this.stop();"
onmouseout="this.start();">

{marquee_html}

</marquee>
</div>
'''

            header = (
                header[:start]
                + block
                + header[end + 6:]
            )

    # -------------------------------------------------
    # Replace Breaking News
    # -------------------------------------------------

    if '<div class="breaking-news">' in header:

        start = header.find(
            '<div class="breaking-news">'
        )

        end = header.find(
            "</div>",
            header.find("</marquee>", start)
        )

        if start != -1 and end != -1:

            block = f'''
<div class="breaking-news">

<div class="breaking-title">

BREAKING NEWS

</div>

<marquee
scrollamount="5"
onmouseover="this.stop();"
onmouseout="this.start();">

{breaking_html}

</marquee>

</div>
'''

            header = (
                header[:start]
                + block
                + header[end + 6:]
            )

    write_text(
        HEADER_FILE,
        header
    )

    logger.info("Header Updated Successfully")
  # =========================================================
# PART 3
# Latest Updates Cards Generator
# =========================================================

DEFAULT_IMAGE = "images/default-job.png"


# ---------------------------------------------------------

def get_card_image(job):

    if job.get("image"):

        return job["image"]

    if job.get("thumbnail"):

        return job["thumbnail"]

    if job.get("featured_image"):

        return job["featured_image"]

    return DEFAULT_IMAGE


# ---------------------------------------------------------

def format_date(job):

    if job.get("publish_date"):

        return job["publish_date"]

    if job.get("scraped_at"):

        try:

            dt = datetime.fromisoformat(
                job["scraped_at"]
            )

            return dt.strftime("%d %B %Y")

        except Exception:

            pass

    return "Latest Update"


# ---------------------------------------------------------

def latest_card(job):

    title = job.get(
        "title",
        "Latest Update"
    )

    link = html_link(job)

    image = get_card_image(job)

    badge = new_badge(job)

    date = format_date(job)

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


# ---------------------------------------------------------

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


# ---------------------------------------------------------

def update_latest_cards(index_html, jobs):

    marker = '<div class="latest-grid">'

    start = index_html.find(marker)

    if start == -1:

        logger.warning(

            "Latest Grid Not Found"

        )

        return index_html

    start += len(marker)

    end = index_html.find(

        "</div>",

        start

    )

    if end == -1:

        logger.warning(

            "Latest Grid End Not Found"

        )

        return index_html

    cards = latest_cards_html(jobs)

    new_html = (

        index_html[:start]

        + "\n"

        + cards

        + "\n"

        + index_html[end:]

    )

    logger.info(

        "Latest Cards Updated"

    )

    return new_html
    # =========================================================
# PART 4
# Latest Posts Generator (3 Columns)
# =========================================================

POST_COLUMNS = 3


# ---------------------------------------------------------

def latest_post_item(job):

    title = job.get("title", "Latest Update")

    link = html_link(job)

    badge = new_badge(job)

    return (
        f'<li><a href="{link}">'
        f'{title} {badge}'
        f'</a></li>'
    )


# ---------------------------------------------------------

def latest_posts_html(jobs):

    posts = latest_jobs(
        jobs,
        LATEST_POSTS
    )

    if not posts:
        return ""

    columns = [[] for _ in range(POST_COLUMNS)]

    for index, job in enumerate(posts):

        columns[index % POST_COLUMNS].append(
            latest_post_item(job)
        )

    html = []

    for column in columns:

        html.append(
            """
<div class="post-column">
<ul>
"""
        )

        html.extend(column)

        html.append(
            """
</ul>
</div>
"""
        )

    return "\n".join(html)


# ---------------------------------------------------------

def update_latest_posts(index_html, jobs):

    marker = '<div class="post-list">'

    start = index_html.find(marker)

    if start == -1:

        logger.warning(
            "Latest Posts Section Not Found"
        )

        return index_html

    start += len(marker)

    end = index_html.find(
        "</div>",
        index_html.find(
            "</div>",
            index_html.find(
                "</div>",
                start
            ) + 6
        ) + 6
    )

    if end == -1:

        logger.warning(
            "Latest Posts End Not Found"
        )

        return index_html

    html = latest_posts_html(jobs)

    index_html = (
        index_html[:start]
        + "\n"
        + html
        + "\n"
        + index_html[end:]
    )

    logger.info(
        "Latest Posts Updated"
    )

    return index_html
    # =========================================================
# PART 5
# Category Section Generator
# =========================================================

CATEGORY_LIMIT = 6


# ---------------------------------------------------------
# Category HTML
# ---------------------------------------------------------

def category_links(jobs, category):

    html = []

    count = 0

    for job in jobs:

        if job.get("category") != category:
            continue

        title = job.get("title", "Latest Update")

        link = html_link(job)

        badge = new_badge(job)

        html.append(
            f'<li><a href="{link}">{title} {badge}</a></li>'
        )

        count += 1

        if count >= CATEGORY_LIMIT:
            break

    return "\n".join(html)


# ---------------------------------------------------------
# Replace Between Markers
# ---------------------------------------------------------

def replace_section(html, start_marker, end_marker, content):

    start = html.find(start_marker)

    end = html.find(end_marker)

    if start == -1 or end == -1:

        logger.warning(
            "Marker Not Found : %s",
            start_marker
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


# ---------------------------------------------------------
# Update Category Sections
# ---------------------------------------------------------

def update_category_sections(index_html, jobs):

    uk_html = category_links(
        jobs,
        "Uttarakhand Jobs"
    )

    central_html = category_links(
        jobs,
        "Central Government Jobs"
    )

    state_html = category_links(
        jobs,
        "Other State Jobs"
    )

    index_html = replace_section(
        index_html,
        "<!-- AUTO_UK_JOBS_START -->",
        "<!-- AUTO_UK_JOBS_END -->",
        uk_html
    )

    index_html = replace_section(
        index_html,
        "<!-- AUTO_CENTRAL_JOBS_START -->",
        "<!-- AUTO_CENTRAL_JOBS_END -->",
        central_html
    )

    index_html = replace_section(
        index_html,
        "<!-- AUTO_STATE_JOBS_START -->",
        "<!-- AUTO_STATE_JOBS_END -->",
        state_html
    )

    logger.info(
        "Category Sections Updated"
    )

    return index_html
    # =========================================================
# PART 6
# Homepage Update Engine
# =========================================================

def update_homepage(new_jobs=None):

    logger.info("=" * 60)
    logger.info("Homepage Generator Started")
    logger.info("=" * 60)

    try:

        jobs = load_jobs()

        if not jobs:

            logger.warning("No Jobs Found")

            return False

        # -------------------------------
        # Update Header
        # -------------------------------

        update_header(jobs)

        # -------------------------------
        # Read Homepage
        # -------------------------------

        index_html = read_text(INDEX_FILE)

        if not index_html:

            logger.error("index.html Not Found")

            return False

        # -------------------------------
        # Latest Cards
        # -------------------------------

        index_html = update_latest_cards(
            index_html,
            jobs
        )

        # -------------------------------
        # Latest Posts
        # -------------------------------

        index_html = update_latest_posts(
            index_html,
            jobs
        )

        # -------------------------------
        # Category Sections
        # -------------------------------

        index_html = update_category_sections(
            index_html,
            jobs
        )

        # -------------------------------
        # Save Homepage
        # -------------------------------

        write_text(
            INDEX_FILE,
            index_html
        )

        logger.info(
            "Homepage Saved Successfully"
        )

        logger.info("=" * 60)
        logger.info("Homepage Updated Successfully")
        logger.info("=" * 60)

        return True

    except Exception as e:

        logger.exception(e)

        return False
        # =========================================================
# PART 7
# Featured Post, Trending Jobs & Popular Searches
# =========================================================

FEATURED_LIMIT = 1
TRENDING_LIMIT = 8
POPULAR_TAG_LIMIT = 20


# ---------------------------------------------------------
# Featured Post
# ---------------------------------------------------------

def get_featured_post(jobs):

    if not jobs:
        return None

    return jobs[0]


def featured_post_html(job):

    if not job:
        return ""

    return f"""
<div class="featured-post">

<span class="featured-label">
⭐ Featured Update
</span>

<h2>
<a href="{html_link(job)}">
{job.get("title")}
</a>
</h2>

<p>

{job.get("category","Latest Jobs")}

</p>

<a class="featured-btn"
href="{html_link(job)}">

Read Full Update →

</a>

</div>
"""


# ---------------------------------------------------------
# Trending Jobs
# ---------------------------------------------------------

def trending_jobs_html(jobs):

    html = []

    for job in latest_jobs(jobs, TRENDING_LIMIT):

        html.append(f"""
<li>

<a href="{html_link(job)}">

🔥 {job.get("title")}

</a>

</li>
""")

    return "\n".join(html)


# ---------------------------------------------------------
# Popular Search Tags
# ---------------------------------------------------------

def popular_search_html(jobs):

    tags = []

    seen = set()

    for job in jobs:

        for tag in job.get("tags", []):

            tag = tag.strip()

            if not tag:
                continue

            if tag in seen:
                continue

            seen.add(tag)

            tags.append(tag)

            if len(tags) >= POPULAR_TAG_LIMIT:
                break

        if len(tags) >= POPULAR_TAG_LIMIT:
            break

    html = []

    for tag in tags:

        slug = (
            tag.lower()
            .replace(" ", "-")
        )

        html.append(
            f'<a href="search.html?q={slug}">{tag}</a>'
        )

    return "\n".join(html)


# ---------------------------------------------------------
# Update Featured Section
# ---------------------------------------------------------

def update_featured(index_html, jobs):

    featured = featured_post_html(

        get_featured_post(jobs)

    )

    index_html = replace_section(

        index_html,

        "<!-- AUTO_FEATURED_START -->",

        "<!-- AUTO_FEATURED_END -->",

        featured

    )

    return index_html


# ---------------------------------------------------------
# Update Trending Section
# ---------------------------------------------------------

def update_trending(index_html, jobs):

    trending = trending_jobs_html(jobs)

    index_html = replace_section(

        index_html,

        "<!-- AUTO_TRENDING_START -->",

        "<!-- AUTO_TRENDING_END -->",

        trending

    )

    return index_html


# ---------------------------------------------------------
# Update Popular Searches
# ---------------------------------------------------------

def update_popular_search(index_html, jobs):

    popular = popular_search_html(jobs)

    index_html = replace_section(

        index_html,

        "<!-- AUTO_POPULAR_START -->",

        "<!-- AUTO_POPULAR_END -->",

        popular

    )

    return index_html


logger.info("Homepage Part 7 Loaded")
# =========================================================
# PART 8
# Final Engine & Search Data Generator
# =========================================================

SEARCH_DATA_FILE = BASE_DIR / "search-data.js"


# ---------------------------------------------------------
# Generate Search Data
# ---------------------------------------------------------

def generate_search_data(jobs):

    data = []

    for job in jobs:

        data.append({

            "title": job.get("title", ""),

            "url": html_link(job),

            "category": job.get(
                "category",
                "Latest Jobs"
            )

        })

    js = (
        "const searchData = "
        + json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        )
        + ";"
    )

    write_text(
        SEARCH_DATA_FILE,
        js
    )

    logger.info(
        "Search Data Generated"
    )


# ---------------------------------------------------------
# Homepage Statistics
# ---------------------------------------------------------

def homepage_stats(jobs):

    stats = {

        "total_jobs": len(jobs),

        "banking": 0,

        "railway": 0,

        "defence": 0,

        "teaching": 0,

        "medical": 0

    }

    for job in jobs:

        dept = job.get(
            "department",
            ""
        ).lower()

        if dept == "banking":

            stats["banking"] += 1

        elif dept == "railway":

            stats["railway"] += 1

        elif dept == "defence":

            stats["defence"] += 1

        elif dept == "teaching":

            stats["teaching"] += 1

        elif dept == "medical":

            stats["medical"] += 1

    return stats


# ---------------------------------------------------------
# Finalize Homepage
# ---------------------------------------------------------

def finalize_homepage(jobs):

    generate_search_data(jobs)

    stats = homepage_stats(jobs)

    logger.info("=" * 50)

    logger.info(
        "Homepage Statistics"
    )

    for key, value in stats.items():

        logger.info(
            "%s : %s",
            key,
            value
        )

    logger.info("=" * 50)


# ---------------------------------------------------------
# Patch update_homepage()
# ---------------------------------------------------------

# write_text(INDEX_FILE, index_html)
# से ठीक पहले यह लाइन जोड़ें:
#
# finalize_homepage(jobs)
#
# यानी:
#
# finalize_homepage(jobs)
# write_text(INDEX_FILE, index_html)

logger.info(
    "Homepage Generator v1 Completed"
)
