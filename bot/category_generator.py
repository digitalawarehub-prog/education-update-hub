# ==========================================================
# Category Generator V4
# Part 1 : Imports + Configuration + Helpers
# ==========================================================

import re
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("CategoryGeneratorV4")

ROOT_DIR = Path(__file__).resolve().parent.parent

# ==========================================================
# Category Pages
# ==========================================================

CATEGORY_FILES = {

    "banking":
        ROOT_DIR / "banking.html",

    "railway":
        ROOT_DIR / "railway.html",

    "upsc":
        ROOT_DIR / "upsc.html",

    "ssc":
        ROOT_DIR / "ssc.html",

    "teacher-recruitment":
        ROOT_DIR / "teacher-recruitment.html",

    "ctet":
        ROOT_DIR / "ctet.html",

    "utet":
        ROOT_DIR / "utet.html",

    "deled":
        ROOT_DIR / "deled.html",

    "admit-card":
        ROOT_DIR / "admit-card.html",

    "result":
        ROOT_DIR / "result.html",

    "answer-key":
        ROOT_DIR / "answer-key.html",

    "scholarship":
        ROOT_DIR / "scholarship.html",

    "uttarakhand-jobs":
        ROOT_DIR / "uttarakhand-jobs.html",

    "central-government-jobs":
        ROOT_DIR / "central-government-jobs.html",

    "other-state-jobs":
        ROOT_DIR / "other-state-jobs.html"

}

# ==========================================================
# Category Markers
# ==========================================================

START_MARKER = "<!-- AUTO_CATEGORY_START -->"

END_MARKER = "<!-- AUTO_CATEGORY_END -->"

# ==========================================================
# Helpers
# ==========================================================

def safe(value, default=""):

    if value is None:
        return default

    return str(value).strip()


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


def get_image(job):

    return (

        job.get("featured_image")

        or job.get("thumbnail")

        or job.get("image")

        or "images/default-job.png"

    )


def category(job):

    return safe(

        job.get("category"),

        "latest-jobs"

    ).lower()


logger.info(
    "Category Generator V4 Part 1 Loaded Successfully"
)
# ==========================================================
# Category Generator V4
# Part 2 : Category Card Builder
# ==========================================================

def build_category_card(job):

    title = safe(job.get("title"))

    image = get_image(job)

    slug = safe(job.get("slug"))

    if not slug:
        slug = slugify(title)
    description = safe(
        job.get("description"),
        "Click to read complete details."
    )

    last_date = safe(
        job.get("last_date"),
        "Check Notification"
    )

    return f"""
<div class="card">

    <a href="{safe(job.get('html_file', f'generated/posts/{slug}.html'))}">

        <img
            src="{image}"
            alt="{title}"
            loading="lazy">

    </a>

    <div class="post-content">

        <span class="category-tag">

            {safe(job.get("category"))}

        </span>

        <h3>

            <a href="{safe(job.get('html_file', f'generated/posts/{slug}.html'))}">
                {title}

            </a>

        </h3>

        <p>

            {description}

        </p>

        <div class="post-meta">

            <span>

                📅 {last_date}

            </span>

        </div>

        <a
            class="read-more-btn"
            <a href="{safe(job.get('html_file', f'generated/posts/{slug}.html'))}">

            Read More →

        </a>

    </div>

</div>
"""


# ==========================================================
# Sidebar List Item
# ==========================================================

def build_sidebar_item(job):

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
# Featured Card
# ==========================================================

def build_featured_card(job):

    title = safe(job.get("title"))

    slug = slugify(title)

    image = get_image(job)

    return f"""
<div class="featured-post">

    <a href="generated/posts/{slug}.html">

        <img
            src="{image}"
            alt="{title}"
            loading="lazy">

        <h2>

            {title}

        </h2>

    </a>

</div>
"""


# ==========================================================
# Register Category Item
# ==========================================================

def create_category_item(job):

    return {

        "card": build_category_card(job),

        "sidebar": build_sidebar_item(job),

        "featured": build_featured_card(job)

    }


logger.info(
    "Category Generator V4 Part 2 Loaded Successfully"
)
# ==========================================================
# Category Generator V4
# Part 3 : Category Detection Engine
# ==========================================================

CATEGORY_RULES = {

    "banking": [
        "bank",
        "ibps",
        "sbi",
        "rbi",
        "pnb",
        "canara",
        "boi",
        "union bank",
        "bank of baroda"
    ],

    "railway": [
        "railway",
        "rrb",
        "rrc",
        "metro rail"
    ],

    "upsc": [
        "upsc",
        "nda",
        "cds",
        "civil services",
        "ies",
        "ifs"
    ],

    "ssc": [
        "ssc",
        "cgl",
        "chsl",
        "mts",
        "gd",
        "stenographer",
        "selection post"
    ],

    "teacher-recruitment": [
        "teacher",
        "lecturer",
        "assistant professor",
        "principal",
        "tgt",
        "pgt",
        "education department"
    ],

    "ctet": [
        "ctet"
    ],

    "utet": [
        "utet",
        "uktet"
    ],

    "deled": [
        "d.el.ed",
        "deled",
        "btc"
    ],

    "admit-card": [
        "admit card",
        "hall ticket",
        "call letter"
    ],

    "result": [
        "result",
        "merit list",
        "score card",
        "scorecard"
    ],

    "answer-key": [
        "answer key",
        "provisional answer key",
        "final answer key"
    ],

    "scholarship": [
        "scholarship",
        "nsp",
        "fellowship",
        "financial assistance"
    ],

    "uttarakhand-jobs": [
        "ukpsc",
        "uttarakhand",
        "ubse",
        "uksssc",
        "ukmssb"
    ],

    "central-government-jobs": [
        "central government",
        "ministry",
        "government of india",
        "psu"
    ],
    "latest-jobs": [
        "recruitment",
        "vacancy",
        "notification",
        "apply online",
        "job"
    ],

    "syllabus": [
        "syllabus",
        "exam pattern"
    ],

    "government-schemes": [
        "scheme",
        "yojana",
        "government scheme"
    ],

    "teaching-exams": [
        "ctet",
        "utet",
        "tet",
        "teacher eligibility"
    ],

    "entrance-exams": [
        "neet",
        "jee",
        "cuet",
        "gate",
        "cat"
    ],
    }


# ==========================================================
# Detect Category
# ==========================================================

def detect_categories(job):

    matched = set()

    # ------------------------------------------
    # 1. Scraper Category (Highest Priority)
    # ------------------------------------------

    category = safe(job.get("category")).lower().strip()

    category_map = {

        "latest jobs": "latest-jobs",
        "recruitment": "latest-jobs",

        "result": "result",
        "results": "result",

        "admit card": "admit-card",

        "answer key": "answer-key",

        "scholarship": "scholarship",

        "syllabus": "syllabus",

        "teaching exams": "teaching-exams",

        "entrance exams": "entrance-exams",

        "government schemes": "government-schemes",

        "banking jobs": "banking-jobs",

        "railway jobs": "railway-jobs",

        "uttarakhand jobs": "uttarakhand-jobs",

        "central jobs": "central-government-jobs",

        "other state jobs": "other-state-jobs",

        "upsc": "upsc",
        "ssc": "ssc",
        "ctet": "ctet",
        "utet": "utet",
        "deled": "deled"

    }

    if category in category_map:
        matched.add(category_map[category])

    # ------------------------------------------
    # 2. Keyword Detection (Backup)
    # ------------------------------------------

    text = " ".join([

        safe(job.get("title")),
        safe(job.get("department")),
        safe(job.get("description"))

    ]).lower()

    for page, keywords in CATEGORY_RULES.items():

        for keyword in keywords:

            if keyword.lower() in text:
                matched.add(page)
                break

    if not matched:
        matched.add("other-state-jobs")

    return list(matched)
# ==========================================================
# Group Jobs
# ==========================================================

def group_jobs(jobs):

    grouped = {
        page: []
        for page in CATEGORY_FILES
    }

    for job in jobs:

        pages = detect_categories(job)

        for page in pages:

            grouped[page].append(job)

    return grouped
# ==========================================================
# Category Generator V4
# Part 4 : Category Page Update Engine
# ==========================================================

def replace_category_section(content, items):

    start = content.find(START_MARKER)
    end = content.find(END_MARKER)

    if start == -1 or end == -1:
        return content

    end += len(END_MARKER)

    auto_section = (
        START_MARKER
        + "\n\n"
        + "\n".join(items)
        + "\n\n"
        + END_MARKER
    )

    return (
        content[:start]
        + auto_section
        + content[end:]
    )

# ==========================================================
# Update Category Page
# ==========================================================

def update_category_page(page_name, jobs):

    page = CATEGORY_FILES.get(page_name)

    if not page:

        logger.warning(
            "Unknown Category : %s",
            page_name
        )

        return False

    if not page.exists():

        logger.warning(
            "Missing File : %s",
            page.name
        )

        return False

    with open(
        page,
        "r",
        encoding="utf-8"
    ) as file:

        html = file.read()

    # ======================================================
    # Auto Migration (Manual -> Automation)
    # ======================================================

    if START_MARKER not in html or END_MARKER not in html:

        # ======================================================
        # Force Automation Layout
        # ======================================================

        start = html.find('<div class="post-grid">')

        if start == -1:
            start = html.find('<div class="post-list">')

        end = html.find('<div id="footer">', start)

        if start != -1 and end != -1:

            html = (
                html[:start]
                +
        """
        <div class="post-grid">

        <!-- AUTO_CATEGORY_START -->

        <!-- AUTO_CATEGORY_END -->

        </div>

        """
                +
                html[end:]
            )

        else:

            logger.warning(
                "Unable to locate post section : %s",
                page.name
            )

            return False

    # ======================================================
    # Build Cards
    # ======================================================

    cards = []

    for job in jobs:
    cards.append(build_category_card(job))

    if not cards:
        cards.append("""
    <div class="empty-category">
        <h3>No Posts Available</h3>
        <p>New updates will appear here automatically.</p>
    </div>
    """)

    # ======================================================
    # Replace Automation Section
    # ======================================================

    html = replace_category_section(
        html,
        cards
    )

    with open(
        page,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(html)

    logger.info(
        "%s Updated (%d Posts)",
        page.name,
        len(cards)
    )

    return True

# ==========================================================
# Update All Categories
# ==========================================================

def update_all_categories(grouped_jobs):

    updated = 0
    skipped = 0

    for page_name, jobs in grouped_jobs.items():

        page = CATEGORY_FILES.get(page_name)

        if page is None:
            logger.warning("Unknown Category : %s", page_name)
            skipped += 1
            continue

        if not page.exists():
            logger.warning("Category Page Missing : %s", page)
            skipped += 1
            continue

        if update_category_page(page_name, jobs):
            updated += 1

    logger.info("=" * 60)
    logger.info("Updated : %d", updated)
    logger.info("Skipped : %d", skipped)
    logger.info("=" * 60)

    return updated
# ==========================================================
# Category Generator V4
# Part 5 : Sorting + Duplicate Removal + Statistics
# ==========================================================

MAX_POSTS_PER_CATEGORY = 50


# ==========================================================
# Remove Duplicate Jobs
# ==========================================================

def remove_duplicate_jobs(jobs):

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
# Sort Latest First
# ==========================================================

def sort_jobs(jobs):

    def sort_key(job):

        return safe(
            job.get(
                "publish_date",
                datetime.today().strftime("%Y-%m-%d")
            )
        )

    return sorted(
        jobs,
        key=sort_key,
        reverse=True
    )


# ==========================================================
# Optimize Category
# ==========================================================

def optimize_category_jobs(jobs):

    jobs = remove_duplicate_jobs(jobs)

    jobs = sort_jobs(jobs)

    return jobs[:MAX_POSTS_PER_CATEGORY]


# ==========================================================
# Optimize All Categories
# ==========================================================

def optimize_categories(grouped_jobs):

    optimized = {}

    for page_name, jobs in grouped_jobs.items():

        optimized[page_name] = optimize_category_jobs(jobs)

    return optimized


# ==========================================================
# Category Statistics
# ==========================================================

def category_statistics(grouped_jobs):

    logger.info("=" * 60)
    logger.info("Category Generator Statistics")
    logger.info("=" * 60)

    total = 0

    for page_name in sorted(grouped_jobs.keys()):

        count = len(grouped_jobs[page_name])

        total += count

        logger.info(
            "%-30s : %3d",
            page_name,
            count
        )

    logger.info("=" * 60)

    logger.info(
        "Total Categorized Posts : %d",
        total
    )

    logger.info("=" * 60)


logger.info(
    "Category Generator V4 Part 5 Loaded Successfully"
)
# ==========================================================
# Category Generator V4
# Part 6 : Final Build + Validation + Runner
# ==========================================================

# ==========================================================
# Validate Category Files
# ==========================================================

def validate_category_files():

    CATEGORY_FILES = {

    "latest-jobs":
        ROOT_DIR / "latest-jobs.html",

    "banking-jobs":
        ROOT_DIR / "banking-jobs.html",

    "railway-jobs":
        ROOT_DIR / "railway-jobs.html",

    "upsc":
        ROOT_DIR / "upsc.html",

    "ssc":
        ROOT_DIR / "ssc.html",

    "teacher-recruitment":
        ROOT_DIR / "teacher-recruitment.html",

    "ctet":
        ROOT_DIR / "ctet.html",

    "utet":
        ROOT_DIR / "utet.html",

    "deled":
        ROOT_DIR / "deled.html",

    "admit-card":
        ROOT_DIR / "admit-card.html",

    "result":
        ROOT_DIR / "result.html",

    "answer-key":
        ROOT_DIR / "answer-key.html",

    "scholarship":
        ROOT_DIR / "scholarship.html",

    "syllabus":
        ROOT_DIR / "syllabus.html",

    "teaching-exams":
        ROOT_DIR / "teaching-exams.html",

    "entrance-exams":
        ROOT_DIR / "entrance-exams.html",

    "government-schemes":
        ROOT_DIR / "government-schemes.html",

    "uttarakhand-jobs":
        ROOT_DIR / "uttarakhand-jobs.html",

    "central-government-jobs":
        ROOT_DIR / "central-government-jobs.html",

    "other-state-jobs":
        ROOT_DIR / "other-state-jobs.html"
}

# ==========================================================
# Build Categories
# ==========================================================

def build_categories(jobs):

    logger.info(
        "Starting Category Generation..."
    )

    grouped = group_jobs(jobs)

    grouped = optimize_categories(grouped)

    category_statistics(grouped)

    updated = update_all_categories(grouped)

    logger.info(
        "Updated %d Category Pages",
        updated
    )

    return updated


# ==========================================================
# Complete Build
# ==========================================================

def build(jobs):

    validate_category_files()

    result = build_categories(jobs)

    logger.info(
        "Category Generator Completed Successfully."
    )

    return result


# ==========================================================
# Main Runner
# ==========================================================

def run(jobs):

    try:

        return build(jobs)

    except Exception as error:

        logger.exception(
            "Category Generator Error : %s",
            error
        )

        return 0


logger.info("=" * 60)
logger.info("Category Generator V4 Loaded Successfully")
logger.info("=" * 60)
