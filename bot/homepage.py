# ==========================================================
# Homepage Generator V5 Professional
# Part 1 : Imports + Configuration + Helpers
# ==========================================================

import re
import logging

from pathlib import Path
from datetime import datetime

logger = logging.getLogger("HomepageGeneratorV5")

# ==========================================================
# Project Paths
# ==========================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

INDEX_FILE = ROOT_DIR / "index.html"

POSTS_DIR = ROOT_DIR / "generated" / "posts"

BASE_URL = "https://educationupdatehub.in"

# ==========================================================
# Homepage Auto Sections
# ==========================================================

SECTIONS = {

    "AUTO_LATEST_GRID": [],

    "AUTO_LATEST_POSTS": [],

    "AUTO_UK_JOBS": [],

    "AUTO_CENTRAL_JOBS": [],

    "AUTO_STATE_JOBS": [],

    # NEW
    "AUTO_MARQUEE": [],

    # NEW
    "AUTO_BREAKING": []

}

# ==========================================================
# Limits
# ==========================================================

MAX_LATEST_GRID = 24

MAX_LATEST_POSTS = 12

MAX_UK_JOBS = 15

MAX_CENTRAL_JOBS = 15

MAX_STATE_JOBS = 15

# NEW
MAX_MARQUEE = 10

# NEW
MAX_BREAKING = 10

# ==========================================================
# Safe Value
# ==========================================================

def safe(value, default=""):

    if value is None:
        return default

    return str(value).strip()

# ==========================================================
# Slug Helper
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
# Publish Date
# ==========================================================

def publish_date(job):

    return safe(

        job.get("publish_date")

        or job.get("date")

        or datetime.today().strftime("%d %B %Y")

    )

logger.info(
    "Homepage Generator V5 Part 1 Loaded Successfully"
)
# ==========================================================
# Homepage Generator V5
# Part 2 : Card Builder + Marquee + Breaking
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
# Sidebar Job Item
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
# Latest Post Card
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


# ==========================================================
# NEW : Top Header Marquee
# ==========================================================

def build_marquee_item(job):

    title = safe(job.get("title"))

    slug = slugify(title)

    return f'''
<a href="generated/posts/{slug}.html">

🔥 {title}

</a>
'''


# ==========================================================
# NEW : Breaking News
# ==========================================================

def build_breaking_item(job):

    title = safe(job.get("title"))

    slug = slugify(title)

    return f'''
🔴 <a href="generated/posts/{slug}.html">

{title}

</a>
'''


logger.info(
    "Homepage Generator V5 Part 2 Loaded Successfully"
)
# ==========================================================
# Homepage Generator V5
# Part 3 : Auto Section Registration
# ==========================================================

def clear_sections():

    for section in SECTIONS:

        SECTIONS[section].clear()


# ==========================================================
# Add HTML
# ==========================================================

def add_to_section(section, html):

    if section in SECTIONS:

        SECTIONS[section].append(html)


# ==========================================================
# Register One Job
# ==========================================================

def register_job(job):

    card = build_homepage_card(job)

    latest = build_latest_post(job)

    item = build_job_item(job)

    marquee = build_marquee_item(job)

    breaking = build_breaking_item(job)

    # Homepage Grid

    add_to_section(
        "AUTO_LATEST_GRID",
        card
    )

    # Latest Posts

    add_to_section(
        "AUTO_LATEST_POSTS",
        latest
    )

    # NEW
    add_to_section(
        "AUTO_MARQUEE",
        marquee
    )

    # NEW
    add_to_section(
        "AUTO_BREAKING",
        breaking
    )

    category_name = category(job).lower()

    department = safe(
        job.get("department")
    ).lower()

    # Uttarakhand

    if (

        "uttarakhand" in category_name

        or "uk" in category_name

    ):

        add_to_section(
            "AUTO_UK_JOBS",
            item
        )

    # Central

    elif (

        "central" in category_name

        or "upsc" in category_name

        or "ssc" in category_name

        or "bank" in department

        or "railway" in department

        or "defence" in department

        or "government" in department

    ):

        add_to_section(
            "AUTO_CENTRAL_JOBS",
            item
        )

    # Other State

    else:

        add_to_section(
            "AUTO_STATE_JOBS",
            item
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
    "Homepage Generator V5 Part 3 Loaded Successfully"
)
# ==========================================================
# Homepage Generator V5
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



# ==========================================================
# Trending Categories Fix
# ==========================================================
def fix_trending_categories(content):
    """Fix Trending Categories links and remove CTET/UTET there only."""
    if not content:
        return content

    start_match = re.search(r"Trending\s+Categories", content, flags=re.I)
    if not start_match:
        return content

    tail = content[start_match.end():]
    end_match = re.search(r"(?:Uttarakhand\s+Jobs|🏔\s*Uttarakhand\s+Jobs)", tail, flags=re.I)
    if not end_match:
        return content

    start = start_match.start()
    end = start_match.end() + end_match.start()
    block = content[start:end]

    block = re.sub(r'(?i)(href\s*=\s*["\'])(?:\.?/)?banking-jobs\.html(["\'])', r'\1banking.html\2', block)
    block = re.sub(r'(?i)(href\s*=\s*["\'])(?:\.?/)?railway-jobs\.html(["\'])', r'\1railway.html\2', block)

    block = re.sub(r'(?is)<li\b[^>]*>.*?\bCTET\b.*?</li>\s*', '', block)
    block = re.sub(r'(?is)<li\b[^>]*>.*?\bUTET\b.*?</li>\s*', '', block)
    block = re.sub(r'(?is)<a\b[^>]*>.*?\bCTET\b.*?</a>\s*', '', block)
    block = re.sub(r'(?is)<a\b[^>]*>.*?\bUTET\b.*?</a>\s*', '', block)

    return content[:start] + block + content[end:]


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

    # Fix static Trending Categories links/items.
    html = fix_trending_categories(html)

    # Homepage Cards

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

    # NEW
    html = replace_auto_section(
        html,
        "AUTO_MARQUEE",
        SECTIONS["AUTO_MARQUEE"][:MAX_MARQUEE]
    )

    # NEW
    html = replace_auto_section(
        html,
        "AUTO_BREAKING",
        SECTIONS["AUTO_BREAKING"][:MAX_BREAKING]
    )

    # Category Sections

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


logger.info(
    "Homepage Generator V5 Part 4 Loaded Successfully"
)
# ==========================================================
# Homepage Generator V5
# Part 5 : Sorting + Limits + Homepage Generation
# ==========================================================

MAX_LATEST_GRID = 24
MAX_LATEST_POSTS = 12
MAX_UK_JOBS = 15
MAX_CENTRAL_JOBS = 15
MAX_STATE_JOBS = 15

# NEW
MAX_MARQUEE = 10
MAX_BREAKING = 10


# ==========================================================
# Sort Jobs
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
# Apply Limits
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

    # NEW
    SECTIONS["AUTO_MARQUEE"] = \
        SECTIONS["AUTO_MARQUEE"][:MAX_MARQUEE]

    # NEW
    SECTIONS["AUTO_BREAKING"] = \
        SECTIONS["AUTO_BREAKING"][:MAX_BREAKING]


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
    "Homepage Generator V5 Part 5 Loaded Successfully"
)
# ==========================================================
# Homepage Generator V5
# Part 6 : Header Update Engine (NEW)
# ==========================================================

HEADER_FILE = ROOT_DIR / "header.html"


def update_header():

    if not HEADER_FILE.exists():

        logger.warning(
            "header.html not found."
        )

        return False

    with open(
        HEADER_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        html = file.read()

    # Top Header Marquee

    html = replace_auto_section(
        html,
        "AUTO_MARQUEE",
        SECTIONS["AUTO_MARQUEE"][:MAX_MARQUEE]
    )

    # Breaking News

    html = replace_auto_section(
        html,
        "AUTO_BREAKING",
        SECTIONS["AUTO_BREAKING"][:MAX_BREAKING]
    )

    with open(
        HEADER_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(html)

    logger.info(
        "Header Updated Successfully."
    )

    return True


# ==========================================================
# Build Homepage + Header
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

    # NEW
    update_header()

    validate_sections()

    homepage_statistics()

    logger.info(
        "Homepage + Header Build Completed Successfully."
    )

    return True


logger.info(
    "Homepage Generator V5 Part 6 Loaded Successfully"
)
# ==========================================================
# Homepage Generator V5
# Part 7 : Search + Homepage Synchronization
# ==========================================================

def synchronize_sections():

    logger.info(
        "=" * 60
    )

    logger.info(
        "Synchronizing Homepage Sections..."
    )

    apply_limits()

    update_homepage()

    update_header()

    validate_sections()

    homepage_statistics()

    logger.info(
        "Synchronization Completed Successfully."
    )

    logger.info(
        "=" * 60
    )


# ==========================================================
# Homepage Refresh
# ==========================================================

def refresh_homepage(jobs):

    logger.info(
        "Refreshing Homepage..."
    )

    jobs = unique_jobs(jobs)

    jobs = sort_jobs(jobs)

    clear_sections()

    register_jobs(jobs)

    synchronize_sections()

    return True


# ==========================================================
# Search Statistics
# ==========================================================

def homepage_search_statistics():

    logger.info(
        "=" * 60
    )

    logger.info(
        "Homepage Search Statistics"
    )

    logger.info(
        "Latest Grid      : %d",
        len(SECTIONS["AUTO_LATEST_GRID"])
    )

    logger.info(
        "Latest Posts     : %d",
        len(SECTIONS["AUTO_LATEST_POSTS"])
    )

    logger.info(
        "Marquee          : %d",
        len(SECTIONS["AUTO_MARQUEE"])
    )

    logger.info(
        "Breaking         : %d",
        len(SECTIONS["AUTO_BREAKING"])
    )

    logger.info(
        "UK Jobs          : %d",
        len(SECTIONS["AUTO_UK_JOBS"])
    )

    logger.info(
        "Central Jobs     : %d",
        len(SECTIONS["AUTO_CENTRAL_JOBS"])
    )

    logger.info(
        "Other State Jobs : %d",
        len(SECTIONS["AUTO_STATE_JOBS"])
    )

    logger.info(
        "=" * 60
    )


logger.info(
    "Homepage Generator V5 Part 7 Loaded Successfully"
)
# ==========================================================
# Homepage Generator V5
# Part 8 : Validation + Statistics
# ==========================================================

def validate_sections():

    total = 0

    logger.info("=" * 60)
    logger.info("Homepage Validation")
    logger.info("=" * 60)

    for section, items in SECTIONS.items():

        count = len(items)

        total += count

        logger.info(
            "%-25s : %d",
            section,
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
        "Homepage Size : %.2f KB",
        size
    )

    logger.info(
        "Generated Time : %s",
        datetime.now().strftime(
            "%d-%m-%Y %H:%M:%S"
        )
    )

    logger.info(
        "Latest Grid : %d",
        len(SECTIONS["AUTO_LATEST_GRID"])
    )

    logger.info(
        "Latest Posts : %d",
        len(SECTIONS["AUTO_LATEST_POSTS"])
    )

    logger.info(
        "Marquee : %d",
        len(SECTIONS["AUTO_MARQUEE"])
    )

    logger.info(
        "Breaking : %d",
        len(SECTIONS["AUTO_BREAKING"])
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

    logger.info("=" * 60)


logger.info(
    "Homepage Generator V5 Part 8 Loaded Successfully"
)
# ==========================================================
# Homepage Generator V5
# Part 9 : Final Build Flow
# ==========================================================

def build_homepage(jobs):

    logger.info("=" * 60)
    logger.info("Starting Homepage Build...")
    logger.info("=" * 60)

    # Sort Latest Jobs

    jobs = unique_jobs(jobs)

    jobs = sort_jobs(jobs)

    # Register

    clear_sections()

    register_jobs(jobs)

    # Apply Limits

    apply_limits()

    # Update Homepage

    update_homepage()

    # Update Header

    update_header()

    # Validation

    validate_sections()

    # Statistics

    homepage_statistics()

    homepage_search_statistics()

    logger.info("=" * 60)
    logger.info("Homepage Build Completed Successfully")
    logger.info("=" * 60)

    return True


# ==========================================================
# Production Build
# ==========================================================

def production_build(jobs):

    try:

        return build_homepage(jobs)

    except Exception as e:

        logger.exception(

            "Homepage Production Build Failed : %s",

            e

        )

        return False


logger.info(
    "Homepage Generator V5 Part 9 Loaded Successfully"
)
# ==========================================================
# Homepage Generator V5
# Part 10 : Main Entry + Production
# ==========================================================

def run(jobs):

    logger.info("=" * 60)
    logger.info("Homepage Generator V5 Started")
    logger.info("=" * 60)

    try:

        result = production_build(jobs)

        if result:

            logger.info(
                "Homepage Generator Completed Successfully."
            )

        else:

            logger.error(
                "Homepage Generator Failed."
            )

        return result

    except Exception as e:

        logger.exception(
            "Homepage Generator Fatal Error : %s",
            e
        )

        return False


# ==========================================================
# Standalone Execution
# ==========================================================

if __name__ == "__main__":

    logger.info("=" * 60)
    logger.info("Homepage Generator V5")
    logger.info("=" * 60)

    logger.info(
        "Run this module through html_generator.py"
    )

logger.info("=" * 60)
logger.info("Homepage Generator V5 Loaded Successfully")
logger.info("=" * 60)
