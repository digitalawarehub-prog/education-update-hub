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

    # Latest Updates
    # यहाँ केवल title-only clickable items आएंगे
    "AUTO_LATEST_GRID": [],

    # Latest Posts
    "AUTO_LATEST_POSTS": [],

    # Uttarakhand Jobs
    "AUTO_UK_JOBS": [],

    # Central Government Jobs
    "AUTO_CENTRAL_JOBS": [],

    # Other State Jobs
    "AUTO_STATE_JOBS": [],

    # Header Marquee
    "AUTO_MARQUEE": [],

    # Breaking News
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

MAX_MARQUEE = 10

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

    title = re.sub(
        r"[^a-z0-9]+",
        "-",
        title
    )

    title = re.sub(
        r"-+",
        "-",
        title
    )

    return title.strip("-")


# ==========================================================
# Image Helper
# ==========================================================
# यह बाकी Homepage sections के लिए रखा गया है।
# Latest Updates में इसका उपयोग नहीं होगा।

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


# ==========================================================
# Homepage Title Helper
# ==========================================================

def homepage_title(job):

    return safe(
        job.get("title"),
        "Latest Government Job Update"
    )


# ==========================================================
# Homepage Post URL
# ==========================================================

def homepage_post_url(job):

    title = homepage_title(job)

    slug = slugify(title)

    return f"generated/posts/{slug}.html"


# ==========================================================
# Logger
# ==========================================================

logger.info(
    "Homepage Generator V5 Part 1 Loaded Successfully"
)
# ==========================================================
# Homepage Generator V5
# Part 2 : Title-Only Latest Updates
# ==========================================================


def build_homepage_card(job):

    title = safe(
        job.get("title"),
        "Latest Government Job Update"
    )

    slug = slugify(title)

    # Latest Updates में केवल clickable title
    return f"""
<div class="homepage-title-item">
    <a href="generated/posts/{slug}.html">
        {title}
    </a>
</div>
"""


# ==========================================================
# Sidebar Job Item
# ==========================================================

def build_job_item(job):

    title = safe(
        job.get("title"),
        "Latest Government Job Update"
    )

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
# यह Latest Posts section के लिए पुराना card structure
# सुरक्षित रखा गया है।

def build_latest_post(job):

    title = safe(
        job.get("title"),
        "Latest Government Job Update"
    )

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
# Top Header Marquee
# ==========================================================

def build_marquee_item(job):

    title = safe(
        job.get("title"),
        "Latest Government Job Update"
    )

    slug = slugify(title)

    return f'''
<a href="generated/posts/{slug}.html">
    🔥 {title}
</a>
'''


# ==========================================================
# Breaking News
# ==========================================================

def build_breaking_item(job):

    title = safe(
        job.get("title"),
        "Latest Government Job Update"
    )

    slug = slugify(title)

    return f'''
🔴 <a href="generated/posts/{slug}.html">
    {title}
</a>
'''


# ==========================================================
# Logger
# ==========================================================

logger.info(
    "Homepage Generator V5 Part 2 Loaded Successfully"
)
# ==========================================================
# Homepage Generator V5
# Part 3 : Auto Section Registration
# ==========================================================


# ==========================================================
# Clear All Auto Sections
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
# Register One Job
# ==========================================================

def register_job(job):

    # ------------------------------------------------------
    # Latest Updates
    # ------------------------------------------------------
    # अब यहाँ केवल title-only item बनेगा।
    # build_homepage_card() को Part 2 में बदल चुके हैं।

    latest_item = build_homepage_card(job)


    # ------------------------------------------------------
    # Latest Posts
    # ------------------------------------------------------

    latest_post = build_latest_post(job)


    # ------------------------------------------------------
    # Sidebar / Category Item
    # ------------------------------------------------------

    job_item = build_job_item(job)


    # ------------------------------------------------------
    # Header Marquee
    # ------------------------------------------------------

    marquee = build_marquee_item(job)


    # ------------------------------------------------------
    # Breaking News
    # ------------------------------------------------------

    breaking = build_breaking_item(job)


    # ======================================================
    # Homepage Latest Updates
    # ======================================================

    add_to_section(
        "AUTO_LATEST_GRID",
        latest_item
    )


    # ======================================================
    # Latest Posts
    # ======================================================

    add_to_section(
        "AUTO_LATEST_POSTS",
        latest_post
    )


    # ======================================================
    # Header Marquee
    # ======================================================

    add_to_section(
        "AUTO_MARQUEE",
        marquee
    )


    # ======================================================
    # Breaking News
    # ======================================================

    add_to_section(
        "AUTO_BREAKING",
        breaking
    )


    # ======================================================
    # Category Detection
    # ======================================================

    category_name = category(job).lower()

    department = safe(
        job.get("department")
    ).lower()


    # ======================================================
    # Uttarakhand Jobs
    # ======================================================

    if (
        "uttarakhand" in category_name
        or "ukpsc" in category_name
        or "uksssc" in category_name
        or "uttarakhand" in department
    ):

        add_to_section(
            "AUTO_UK_JOBS",
            job_item
        )


    # ======================================================
    # Central Government Jobs
    # ======================================================

    elif (
        "central" in category_name
        or "upsc" in category_name
        or "ssc" in category_name
        or "bank" in department
        or "banking" in department
        or "railway" in department
        or "defence" in department
        or "government" in department
    ):

        add_to_section(
            "AUTO_CENTRAL_JOBS",
            job_item
        )


    # ======================================================
    # Other State Jobs
    # ======================================================

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


        # --------------------------------------------------
        # Title missing
        # --------------------------------------------------

        if not title:

            continue


        # --------------------------------------------------
        # Create unique slug
        # --------------------------------------------------

        slug = slugify(title)


        # --------------------------------------------------
        # Invalid slug
        # --------------------------------------------------

        if not slug:

            continue


        # --------------------------------------------------
        # Duplicate title
        # --------------------------------------------------

        if slug in seen:

            continue


        seen.add(slug)


        # --------------------------------------------------
        # Register job
        # --------------------------------------------------

        register_job(job)


    logger.info(
        "Registered %d unique jobs.",
        len(seen)
    )


logger.info(
    "Homepage Generator V5 Part 3 Loaded Successfully"
)
# ==========================================================
# Homepage Generator V5
# Part 4 : Homepage Update Engine
# ==========================================================


# ==========================================================
# Replace Automatic Section
# ==========================================================

def replace_auto_section(content, marker, items):

    start_marker = f"<!-- {marker}_START -->"
    end_marker = f"<!-- {marker}_END -->"


    # ------------------------------------------------------
    # Marker check
    # ------------------------------------------------------

    if start_marker not in content:

        logger.warning(
            "%s start marker not found.",
            marker
        )

        return content


    if end_marker not in content:

        logger.warning(
            "%s end marker not found.",
            marker
        )

        return content


    # ------------------------------------------------------
    # Locate markers
    # ------------------------------------------------------

    start = content.find(start_marker)

    end = content.find(
        end_marker,
        start
    )


    if start == -1 or end == -1:

        return content


    end += len(end_marker)


    # ------------------------------------------------------
    # Build new section
    # ------------------------------------------------------

    new_section = (
        start_marker
        + "\n\n"
        + "\n".join(items)
        + "\n\n"
        + end_marker
    )


    # ------------------------------------------------------
    # Replace only the selected section
    # ------------------------------------------------------

    return (
        content[:start]
        + new_section
        + content[end:]
    )


# ==========================================================
# Update Homepage
# ==========================================================

def update_homepage():

    if not INDEX_FILE.exists():

        logger.error(
            "index.html not found."
        )

        return False


    # ------------------------------------------------------
    # Read Homepage
    # ------------------------------------------------------

    with open(
        INDEX_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        html = file.read()


    # ======================================================
    # Latest Updates
    # ======================================================
    # यहाँ Part 2 में बनाए गए
    # title-only clickable items जाएंगे।

    latest_items = SECTIONS[
        "AUTO_LATEST_GRID"
    ][:MAX_LATEST_GRID]


    html = replace_auto_section(
        html,
        "AUTO_LATEST_GRID",
        latest_items
    )


    # ======================================================
    # Latest Posts
    # ======================================================

    latest_posts = SECTIONS[
        "AUTO_LATEST_POSTS"
    ][:MAX_LATEST_POSTS]


    html = replace_auto_section(
        html,
        "AUTO_LATEST_POSTS",
        latest_posts
    )


    # ======================================================
    # Header Marquee
    # ======================================================

    marquee_items = SECTIONS[
        "AUTO_MARQUEE"
    ][:MAX_MARQUEE]


    html = replace_auto_section(
        html,
        "AUTO_MARQUEE",
        marquee_items
    )


    # ======================================================
    # Breaking News
    # ======================================================

    breaking_items = SECTIONS[
        "AUTO_BREAKING"
    ][:MAX_BREAKING]


    html = replace_auto_section(
        html,
        "AUTO_BREAKING",
        breaking_items
    )


    # ======================================================
    # Uttarakhand Jobs
    # ======================================================

    uk_items = SECTIONS[
        "AUTO_UK_JOBS"
    ][:MAX_UK_JOBS]


    html = replace_auto_section(
        html,
        "AUTO_UK_JOBS",
        uk_items
    )


    # ======================================================
    # Central Government Jobs
    # ======================================================

    central_items = SECTIONS[
        "AUTO_CENTRAL_JOBS"
    ][:MAX_CENTRAL_JOBS]


    html = replace_auto_section(
        html,
        "AUTO_CENTRAL_JOBS",
        central_items
    )


    # ======================================================
    # Other State Jobs
    # ======================================================

    state_items = SECTIONS[
        "AUTO_STATE_JOBS"
    ][:MAX_STATE_JOBS]


    html = replace_auto_section(
        html,
        "AUTO_STATE_JOBS",
        state_items
    )


    # ======================================================
    # Write Homepage
    # ======================================================

    with open(
        INDEX_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(html)


    logger.info(
        "Homepage Updated Successfully."
    )


    logger.info(
        "Latest Updates Titles : %d",
        len(latest_items)
    )


    return True


logger.info(
    "Homepage Generator V5 Part 4 Loaded Successfully"
)
# ==========================================================
# Homepage Generator V5
# Part 5 : Sorting + Limits + Homepage Generation
# ==========================================================


# ==========================================================
# Maximum Items
# ==========================================================

MAX_LATEST_GRID = 24

MAX_LATEST_POSTS = 12

MAX_UK_JOBS = 15

MAX_CENTRAL_JOBS = 15

MAX_STATE_JOBS = 15

MAX_MARQUEE = 10

MAX_BREAKING = 10


# ==========================================================
# Parse Publish Date
# ==========================================================

def parse_publish_date(value):

    value = safe(value)

    if not value:

        return datetime.min


    formats = [

        "%Y-%m-%d",

        "%Y-%m-%d %H:%M:%S",

        "%Y-%m-%dT%H:%M:%S",

        "%Y-%m-%dT%H:%M:%S.%f",

        "%d-%m-%Y",

        "%d/%m/%Y",

        "%d %B %Y",

        "%d %b %Y",

        "%B %d, %Y",

        "%b %d, %Y",

    ]


    for fmt in formats:

        try:

            return datetime.strptime(
                value,
                fmt
            )

        except ValueError:

            continue


    return datetime.min


# ==========================================================
# Sort Jobs
# ==========================================================

def sort_jobs(jobs):

    return sorted(
        jobs,
        key=lambda job: parse_publish_date(
            job.get("publish_date")
            or job.get("date")
        ),
        reverse=True
    )


# ==========================================================
# Remove Duplicate Jobs
# ==========================================================

def unique_jobs(jobs):

    unique = []

    seen = set()


    for job in jobs:

        title = safe(
            job.get("title")
        )


        if not title:

            continue


        slug = slugify(title)


        if not slug:

            continue


        if slug in seen:

            continue


        seen.add(slug)

        unique.append(job)


    return unique


# ==========================================================
# Apply Limits
# ==========================================================

def apply_limits():

    SECTIONS["AUTO_LATEST_GRID"] = (
        SECTIONS["AUTO_LATEST_GRID"]
        [:MAX_LATEST_GRID]
    )


    SECTIONS["AUTO_LATEST_POSTS"] = (
        SECTIONS["AUTO_LATEST_POSTS"]
        [:MAX_LATEST_POSTS]
    )


    SECTIONS["AUTO_UK_JOBS"] = (
        SECTIONS["AUTO_UK_JOBS"]
        [:MAX_UK_JOBS]
    )


    SECTIONS["AUTO_CENTRAL_JOBS"] = (
        SECTIONS["AUTO_CENTRAL_JOBS"]
        [:MAX_CENTRAL_JOBS]
    )


    SECTIONS["AUTO_STATE_JOBS"] = (
        SECTIONS["AUTO_STATE_JOBS"]
        [:MAX_STATE_JOBS]
    )


    SECTIONS["AUTO_MARQUEE"] = (
        SECTIONS["AUTO_MARQUEE"]
        [:MAX_MARQUEE]
    )


    SECTIONS["AUTO_BREAKING"] = (
        SECTIONS["AUTO_BREAKING"]
        [:MAX_BREAKING]
    )


# ==========================================================
# Generate Homepage
# ==========================================================

def generate_homepage(jobs):

    logger.info(
        "Preparing homepage jobs..."
    )


    # ------------------------------------------------------
    # Remove duplicates
    # ------------------------------------------------------

    jobs = unique_jobs(
        jobs
    )


    # ------------------------------------------------------
    # Latest first
    # ------------------------------------------------------

    jobs = sort_jobs(
        jobs
    )


    # ------------------------------------------------------
    # Register sections
    # ------------------------------------------------------

    register_jobs(
        jobs
    )


    # ------------------------------------------------------
    # Apply limits
    # ------------------------------------------------------

    apply_limits()


    # ------------------------------------------------------
    # Update index.html
    # ------------------------------------------------------

    success = update_homepage()


    if not success:

        logger.error(
            "Homepage update failed."
        )

        return False


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
# Part 6 : Header Update Engine
# ==========================================================


# ==========================================================
# Header File
# ==========================================================

HEADER_FILE = ROOT_DIR / "header.html"


# ==========================================================
# Update Header
# ==========================================================

def update_header():

    if not HEADER_FILE.exists():

        logger.warning(
            "header.html not found."
        )

        return False


    # ------------------------------------------------------
    # Read Header
    # ------------------------------------------------------

    with open(
        HEADER_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        html = file.read()


    # ======================================================
    # Top Header Marquee
    # ======================================================

    marquee_items = SECTIONS[
        "AUTO_MARQUEE"
    ][:MAX_MARQUEE]


    html = replace_auto_section(
        html,
        "AUTO_MARQUEE",
        marquee_items
    )


    # ======================================================
    # Breaking News
    # ======================================================

    breaking_items = SECTIONS[
        "AUTO_BREAKING"
    ][:MAX_BREAKING]


    html = replace_auto_section(
        html,
        "AUTO_BREAKING",
        breaking_items
    )


    # ======================================================
    # Write Header
    # ======================================================

    with open(
        HEADER_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(html)


    logger.info(
        "Header Updated Successfully."
    )


    logger.info(
        "Marquee Items : %d",
        len(marquee_items)
    )


    logger.info(
        "Breaking Items : %d",
        len(breaking_items)
    )


    return True


logger.info(
    "Homepage Generator V5 Part 6 Loaded Successfully"
)

# ==========================================================
# Homepage Generator V5
# Part 7 : Homepage Build + Synchronization
# ==========================================================


# ==========================================================
# Synchronize Homepage Sections
# ==========================================================

def synchronize_sections():

    logger.info(
        "=" * 60
    )

    logger.info(
        "Synchronizing Homepage Sections..."
    )


    # ------------------------------------------------------
    # Apply current limits
    # ------------------------------------------------------

    apply_limits()


    # ------------------------------------------------------
    # Update index.html
    # ------------------------------------------------------

    homepage_updated = update_homepage()


    if not homepage_updated:

        logger.error(
            "Homepage synchronization failed."
        )

        return False


    # ------------------------------------------------------
    # Update header.html
    # ------------------------------------------------------

    header_updated = update_header()


    if not header_updated:

        logger.warning(
            "Header synchronization failed."
        )


    # ------------------------------------------------------
    # Validation
    # ------------------------------------------------------

    validate_sections()


    # ------------------------------------------------------
    # Statistics
    # ------------------------------------------------------

    homepage_statistics()


    logger.info(
        "Synchronization Completed Successfully."
    )

    logger.info(
        "=" * 60
    )


    return True


# ==========================================================
# Homepage Refresh
# ==========================================================

def refresh_homepage(jobs):

    logger.info(
        "Refreshing Homepage..."
    )


    # ------------------------------------------------------
    # Remove duplicate jobs
    # ------------------------------------------------------

    jobs = unique_jobs(
        jobs
    )


    # ------------------------------------------------------
    # Sort latest first
    # ------------------------------------------------------

    jobs = sort_jobs(
        jobs
    )


    # ------------------------------------------------------
    # Clear old generated sections
    # ------------------------------------------------------

    clear_sections()


    # ------------------------------------------------------
    # Register fresh jobs
    # ------------------------------------------------------

    register_jobs(
        jobs
    )


    # ------------------------------------------------------
    # Synchronize homepage + header
    # ------------------------------------------------------

    return synchronize_sections()


logger.info(
    "Homepage Generator V5 Part 7 Loaded Successfully"
)

# ==========================================================
# Homepage Generator V5
# Part 8 : Validation + Statistics
# ==========================================================


# ==========================================================
# Validate Homepage Sections
# ==========================================================

def validate_sections():

    total = 0

    logger.info(
        "=" * 60
    )

    logger.info(
        "Homepage Validation"
    )

    logger.info(
        "=" * 60
    )


    for section, items in SECTIONS.items():

        count = len(items)

        total += count


        logger.info(
            "%-25s : %d",
            section,
            count
        )


    logger.info(
        "=" * 60
    )


    logger.info(
        "Total Homepage Items : %d",
        total
    )


    logger.info(
        "=" * 60
    )


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


    size = (
        INDEX_FILE.stat().st_size
        / 1024
    )


    logger.info(
        "=" * 60
    )

    logger.info(
        "Homepage Statistics"
    )

    logger.info(
        "=" * 60
    )


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


    # ======================================================
    # Latest Updates
    # ======================================================

    logger.info(
        "Latest Updates : %d",
        len(
            SECTIONS["AUTO_LATEST_GRID"]
        )
    )


    # ======================================================
    # Latest Posts
    # ======================================================

    logger.info(
        "Latest Posts : %d",
        len(
            SECTIONS["AUTO_LATEST_POSTS"]
        )
    )


    # ======================================================
    # Header Marquee
    # ======================================================

    logger.info(
        "Marquee : %d",
        len(
            SECTIONS["AUTO_MARQUEE"]
        )
    )


    # ======================================================
    # Breaking News
    # ======================================================

    logger.info(
        "Breaking : %d",
        len(
            SECTIONS["AUTO_BREAKING"]
        )
    )


    # ======================================================
    # Uttarakhand Jobs
    # ======================================================

    logger.info(
        "UK Jobs : %d",
        len(
            SECTIONS["AUTO_UK_JOBS"]
        )
    )


    # ======================================================
    # Central Jobs
    # ======================================================

    logger.info(
        "Central Jobs : %d",
        len(
            SECTIONS["AUTO_CENTRAL_JOBS"]
        )
    )


    # ======================================================
    # Other State Jobs
    # ======================================================

    logger.info(
        "Other State Jobs : %d",
        len(
            SECTIONS["AUTO_STATE_JOBS"]
        )
    )


    logger.info(
        "=" * 60
    )


logger.info(
    "Homepage Generator V5 Part 8 Loaded Successfully"
)
# ==========================================================
# Homepage Generator V5
# Part 9 : Final Build Flow
# ==========================================================


# ==========================================================
# Build Homepage
# ==========================================================

def build_homepage(jobs):

    logger.info(
        "=" * 60
    )

    logger.info(
        "Starting Homepage Build..."
    )

    logger.info(
        "=" * 60
    )


    try:

        # --------------------------------------------------
        # 1. Remove duplicate jobs
        # --------------------------------------------------

        jobs = unique_jobs(
            jobs
        )


        # --------------------------------------------------
        # 2. Sort latest jobs first
        # --------------------------------------------------

        jobs = sort_jobs(
            jobs
        )


        logger.info(
            "Jobs available for Homepage : %d",
            len(jobs)
        )


        # --------------------------------------------------
        # 3. Clear old automatic sections
        # --------------------------------------------------

        clear_sections()


        # --------------------------------------------------
        # 4. Register fresh jobs
        # --------------------------------------------------

        register_jobs(
            jobs
        )


        # --------------------------------------------------
        # 5. Apply section limits
        # --------------------------------------------------

        apply_limits()


        # --------------------------------------------------
        # 6. Update index.html
        # --------------------------------------------------

        homepage_result = update_homepage()


        if not homepage_result:

            logger.error(
                "Homepage update failed."
            )

            return False


        # --------------------------------------------------
        # 7. Update header.html
        # --------------------------------------------------

        header_result = update_header()


        if not header_result:

            logger.warning(
                "Header update failed."
            )


        # --------------------------------------------------
        # 8. Validate sections
        # --------------------------------------------------

        validate_sections()


        # --------------------------------------------------
        # 9. Homepage statistics
        # --------------------------------------------------

        homepage_statistics()


        logger.info(
            "=" * 60
        )

        logger.info(
            "Homepage Build Completed Successfully"
        )

        logger.info(
            "=" * 60
        )


        return True


    except Exception as e:

        logger.exception(
            "Homepage Build Failed : %s",
            e
        )

        return False


# ==========================================================
# Production Build
# ==========================================================

def production_build(jobs):

    try:

        return build_homepage(
            jobs
        )


    except Exception as e:

        logger.exception(
            "Homepage Production Build Failed : %s",
            e
        )

        return False


# ==========================================================
# Main Entry
# ==========================================================

def run(jobs):

    logger.info(
        "=" * 60
    )

    logger.info(
        "Homepage Generator V5 Started"
    )

    logger.info(
        "=" * 60
    )


    try:

        result = production_build(
            jobs
        )


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

    logger.info(
        "=" * 60
    )

    logger.info(
        "Homepage Generator V5"
    )

    logger.info(
        "Run this module through html_generator.py"
    )

    logger.info(
        "=" * 60
    )


# ==========================================================
# Final Logger
# ==========================================================

logger.info(
    "=" * 60
)

logger.info(
    "Homepage Generator V5 Loaded Successfully"
)

logger.info(
    "=" * 60
)
