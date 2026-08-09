# ==========================================================
# Education Update Hub
# Category Generator V5
# Part 1 : Imports + Configuration + Helpers
# ==========================================================

import re
import logging
from pathlib import Path
from datetime import datetime


logger = logging.getLogger("CategoryGeneratorV5")


# ==========================================================
# Project Root
# ==========================================================

# category_generator.py -> bot/
# parent.parent -> repository root

ROOT_DIR = Path(__file__).resolve().parent.parent


# ==========================================================
# Category Pages
# ==========================================================

CATEGORY_FILES = {

    # Main Jobs
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

    # Teaching / Education
    "ctet":
        ROOT_DIR / "ctet.html",

    "utet":
        ROOT_DIR / "utet.html",

    "deled":
        ROOT_DIR / "deled.html",

    "teaching-exams":
        ROOT_DIR / "teaching-exams.html",

    "syllabus":
        ROOT_DIR / "syllabus.html",

    "entrance-exams":
        ROOT_DIR / "entrance-exams.html",

    # Other Updates
    "admit-card":
        ROOT_DIR / "admit-card.html",

    "result":
        ROOT_DIR / "result.html",

    "answer-key":
        ROOT_DIR / "answer-key.html",

    "scholarship":
        ROOT_DIR / "scholarship.html",

    "government-schemes":
        ROOT_DIR / "government-schemes.html",

    # State / Government Jobs
    "uttarakhand-jobs":
        ROOT_DIR / "uttarakhand-jobs.html",

    "central-government-jobs":
        ROOT_DIR / "central-government-jobs.html",

    "other-state-jobs":
        ROOT_DIR / "other-state-jobs.html",
}


# ==========================================================
# Category Markers
# ==========================================================

START_MARKER = "<!-- AUTO_CATEGORY_START -->"

END_MARKER = "<!-- AUTO_CATEGORY_END -->"


# ==========================================================
# Limits
# ==========================================================

MAX_POSTS_PER_CATEGORY = 50

MAX_LATEST_JOBS = 50


# ==========================================================
# Safe Value Helper
# ==========================================================

def safe(value, default=""):

    if value is None:
        return default

    value = str(value).strip()

    if not value:
        return default

    return value


# ==========================================================
# Slug Generator
# ==========================================================

def slugify(title):

    title = safe(title).lower()

    # Remove template placeholders
    title = re.sub(
        r"\{\{.*?\}\}",
        "",
        title
    )

    # Replace &
    title = title.replace("&", " and ")

    # Keep only URL-safe English characters
    title = re.sub(
        r"[^a-z0-9]+",
        "-",
        title
    )

    # Remove duplicate hyphens
    title = re.sub(
        r"-+",
        "-",
        title
    )

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

def get_job_category(job):

    return safe(
        job.get("category"),
        "Latest Jobs"
    )


# ==========================================================
# Publish Date Helper
# ==========================================================

def get_publish_date(job):

    return safe(
        job.get("publish_date")
        or job.get("date"),
        datetime.today().strftime("%Y-%m-%d")
    )


# ==========================================================
# HTML File Helper
# ==========================================================

def get_html_file(job):

    title = safe(
        job.get("title")
    )

    slug = safe(
        job.get("slug")
    )

    if not slug:
        slug = slugify(title)

    html_file = safe(
        job.get("html_file")
    )

    if html_file:
        return html_file

    return f"generated/posts/{slug}.html"


# ==========================================================
# Category Page Validation
# ==========================================================

def category_page_exists(page_name):

    page = CATEGORY_FILES.get(page_name)

    if page is None:
        return False

    return page.exists()


# ==========================================================
# Logging
# ==========================================================

logger.info("=" * 60)
logger.info("Category Generator V5")
logger.info("Project Root : %s", ROOT_DIR)
logger.info("Category Pages : %d", len(CATEGORY_FILES))
logger.info("=" * 60)
# ==========================================================
# Category Generator V5
# Part 2 : Category Card Builder
# ==========================================================


# ==========================================================
# Category Card
# ==========================================================

def build_category_card(job):

    title = safe(
        job.get("title"),
        "Latest Government Update"
    )

    slug = safe(
        job.get("slug")
    )

    if not slug:
        slug = slugify(title)

    description = safe(
        job.get("description"),
        "Click below to read the complete recruitment and government update."
    )

    last_date = safe(
        job.get("last_date"),
        "Check Official Notification"
    )

    category_name = get_job_category(job)

    html_file = get_html_file(job)

    image = get_image(job)

    return f"""
<div class="card">

    <div class="post-content">

        <span class="category-tag">
            {category_name}
        </span>

        <h3>
            <a href="{html_file}">
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
            href="{html_file}">
            Read More →
        </a>

    </div>

</div>
"""


# ==========================================================
# Category Card With Image
# ==========================================================

def build_category_card_with_image(job):

    title = safe(
        job.get("title"),
        "Latest Government Update"
    )

    slug = safe(
        job.get("slug")
    )

    if not slug:
        slug = slugify(title)

    category_name = get_job_category(job)

    last_date = safe(
        job.get("last_date"),
        "Check Notification"
    )

    html_file = get_html_file(job)

    image = get_image(job)

    return f"""
<div class="card">

    <a href="{html_file}">

        <img
            src="{image}"
            alt="{title}"
            loading="lazy">

    </a>

    <div class="post-content">

        <span class="category-tag">
            {category_name}
        </span>

        <h3>
            <a href="{html_file}">
                {title}
            </a>
        </h3>

        <div class="post-meta">

            <span>
                📅 {last_date}
            </span>

        </div>

        <a
            class="read-more-btn"
            href="{html_file}">
            Read More →
        </a>

    </div>

</div>
"""


# ==========================================================
# Sidebar List Item
# ==========================================================

def build_sidebar_item(job):

    title = safe(
        job.get("title"),
        "Latest Update"
    )

    html_file = get_html_file(job)

    return f"""
<li>
    <a href="{html_file}">
        {title}
    </a>
</li>
"""


# ==========================================================
# Featured Card
# ==========================================================

def build_featured_card(job):

    title = safe(
        job.get("title"),
        "Latest Government Update"
    )

    html_file = get_html_file(job)

    image = get_image(job)

    return f"""
<div class="featured-post">

    <a href="{html_file}">

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
# Empty Category Card
# ==========================================================

def build_empty_category():

    return """
<div class="empty-category">

    <h3>
        No Posts Available
    </h3>

    <p>
        New government jobs and recruitment updates
        will appear here automatically.
    </p>

</div>
"""


# ==========================================================
# Create Category Item
# ==========================================================

def create_category_item(job):

    return {

        "card":
            build_category_card(job),

        "card_with_image":
            build_category_card_with_image(job),

        "sidebar":
            build_sidebar_item(job),

        "featured":
            build_featured_card(job)

    }


# ==========================================================
# Part 2 Loaded
# ==========================================================

logger.info(
    "Category Generator V5 Part 2 Loaded Successfully"
)
# ==========================================================
# Education Update Hub
# Category Generator V5
# Part 3 : Category Detection Engine
# ==========================================================


# ==========================================================
# Category Rules
# ==========================================================

CATEGORY_RULES = {

    # ------------------------------------------------------
    # Banking
    # ------------------------------------------------------
    "banking-jobs": [
        "bank",
        "banking",
        "ibps",
        "sbi",
        "rbi",
        "pnb",
        "canara bank",
        "bank of india",
        "bank of baroda",
        "union bank",
        "uco bank",
        "indian bank",
        "sidbi",
        "nabard",
        "lic"
    ],


    # ------------------------------------------------------
    # Railway
    # ------------------------------------------------------
    "railway-jobs": [
        "railway",
        "railways",
        "rrb",
        "rrc",
        "ntpc",
        "group d",
        "alp",
        "technician",
        "metro rail"
    ],


    # ------------------------------------------------------
    # UPSC
    # ------------------------------------------------------
    "upsc": [
        "upsc",
        "union public service commission",
        "civil services",
        "nda",
        "cds",
        "ies",
        "ifs",
        "cms",
        "epfo"
    ],


    # ------------------------------------------------------
    # SSC
    # ------------------------------------------------------
    "ssc": [
        "ssc",
        "staff selection commission",
        "cgl",
        "chsl",
        "mts",
        "gd constable",
        "stenographer",
        "selection post",
        "je"
    ],


    # ------------------------------------------------------
    # Teacher Recruitment
    # ------------------------------------------------------
    "teacher-recruitment": [
        "teacher recruitment",
        "teacher vacancy",
        "school teacher",
        "lecturer",
        "assistant professor",
        "professor",
        "principal",
        "tgt",
        "pgt",
        "prt",
        "primary teacher",
        "assistant teacher",
        "education department"
    ],


    # ------------------------------------------------------
    # CTET
    # ------------------------------------------------------
    "ctet": [
        "ctet",
        "central teacher eligibility test"
    ],


    # ------------------------------------------------------
    # UTET
    # ------------------------------------------------------
    "utet": [
        "utet",
        "uktet",
        "uttarakhand teacher eligibility test"
    ],


    # ------------------------------------------------------
    # D.El.Ed
    # ------------------------------------------------------
    "deled": [
        "d.el.ed",
        "d.el.ed.",
        "deled",
        "d el ed",
        "btc",
        "diploma in elementary education"
    ],


    # ------------------------------------------------------
    # Admit Card
    # ------------------------------------------------------
    "admit-card": [
        "admit card",
        "admit-card",
        "hall ticket",
        "call letter"
    ],


    # ------------------------------------------------------
    # Result
    # ------------------------------------------------------
    "result": [
        "result",
        "results",
        "merit list",
        "score card",
        "scorecard",
        "final result"
    ],


    # ------------------------------------------------------
    # Answer Key
    # ------------------------------------------------------
    "answer-key": [
        "answer key",
        "answer-key",
        "provisional answer key",
        "final answer key"
    ],


    # ------------------------------------------------------
    # Scholarship
    # ------------------------------------------------------
    "scholarship": [
        "scholarship",
        "nsp",
        "national scholarship",
        "fellowship",
        "financial assistance"
    ],


    # ------------------------------------------------------
    # Uttarakhand Jobs
    # ------------------------------------------------------
    "uttarakhand-jobs": [
        "uttarakhand",
        "ukpsc",
        "uksssc",
        "ukmssb",
        "ubse",
        "ubter",
        "uttarakhand government",
        "uttarakhand govt"
    ],


    # ------------------------------------------------------
    # Central Government
    # ------------------------------------------------------
    "central-government-jobs": [
        "central government",
        "government of india",
        "govt of india",
        "ministry",
        "department of india",
        "psu",
        "central govt"
    ],


    # ------------------------------------------------------
    # Other State Jobs
    # ------------------------------------------------------
    "other-state-jobs": [
        "bpsc",
        "mppsc",
        "uppsc",
        "rpsc",
        "hpsc",
        "gpsc",
        "state government",
        "state govt",
        "government job"
    ],


    # ------------------------------------------------------
    # Syllabus
    # ------------------------------------------------------
    "syllabus": [
        "syllabus",
        "exam pattern",
        "exam scheme"
    ],


    # ------------------------------------------------------
    # Government Schemes
    # ------------------------------------------------------
    "government-schemes": [
        "government scheme",
        "government schemes",
        "yojana",
        "scheme",
        "प्रधानमंत्री योजना",
        "सरकारी योजना"
    ],


    # ------------------------------------------------------
    # Teaching Exams
    # ------------------------------------------------------
    "teaching-exams": [
        "ctet",
        "utet",
        "tet",
        "teacher eligibility test",
        "teacher eligibility"
    ],


    # ------------------------------------------------------
    # Entrance Exams
    # ------------------------------------------------------
    "entrance-exams": [
        "neet",
        "jee",
        "cuet",
        "gate",
        "cat",
        "entrance exam",
        "entrance examination"
    ]

}


# ==========================================================
# Explicit Category Map
# ==========================================================

CATEGORY_MAP = {

    "latest jobs":
        "latest-jobs",

    "latest job":
        "latest-jobs",

    "jobs":
        "latest-jobs",

    "recruitment":
        "latest-jobs",

    "recruitment jobs":
        "latest-jobs",

    "banking jobs":
        "banking-jobs",

    "banking":
        "banking-jobs",

    "railway jobs":
        "railway-jobs",

    "railway":
        "railway-jobs",

    "upsc":
        "upsc",

    "ssc":
        "ssc",

    "teacher recruitment":
        "teacher-recruitment",

    "ctet":
        "ctet",

    "utet":
        "utet",

    "deled":
        "deled",

    "d.el.ed":
        "deled",

    "admit card":
        "admit-card",

    "admit-card":
        "admit-card",

    "result":
        "result",

    "results":
        "result",

    "answer key":
        "answer-key",

    "answer-key":
        "answer-key",

    "scholarship":
        "scholarship",

    "syllabus":
        "syllabus",

    "teaching exams":
        "teaching-exams",

    "entrance exams":
        "entrance-exams",

    "government schemes":
        "government-schemes",

    "uttarakhand jobs":
        "uttarakhand-jobs",

    "uttarakhand":
        "uttarakhand-jobs",

    "central jobs":
        "central-government-jobs",

    "central government jobs":
        "central-government-jobs",

    "other state jobs":
        "other-state-jobs"
}


# ==========================================================
# Job-Type Detection
# ==========================================================

JOB_KEYWORDS = [

    "recruitment",
    "recruitments",
    "vacancy",
    "vacancies",
    "job",
    "jobs",
    "apply online",
    "online application",
    "application form",
    "posts",
    "post",
    "notification for recruitment",
    "employment",
    "hiring",
    "career",
    "career opportunity"
]


# ==========================================================
# Non-Job Content
# ==========================================================

NON_JOB_KEYWORDS = [

    "admit card",
    "admit-card",
    "hall ticket",

    "result",
    "results",
    "merit list",
    "scorecard",
    "score card",

    "answer key",
    "answer-key",

    "syllabus",

    "scholarship",

    "yojana",
    "government scheme",
    "scheme"
]


# ==========================================================
# Normalize Text
# ==========================================================

def normalize_text(value):

    value = safe(value)

    if not value:
        return ""

    value = value.lower()

    value = value.replace(
        "&",
        " and "
    )

    value = value.replace(
        "-",
        " "
    )

    value = value.replace(
        "_",
        " "
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


# ==========================================================
# Build Search Text
# ==========================================================

def build_job_text(job):

    parts = [

        job.get("title"),

        job.get("category"),

        job.get("department"),

        job.get("organization"),

        job.get("description"),

        job.get("qualification"),

        job.get("url")

    ]

    text = " ".join(
        safe(part)
        for part in parts
        if safe(part)
    )

    return normalize_text(text)


# ==========================================================
# Check Keyword
# ==========================================================

def contains_keyword(text, keyword):

    keyword = normalize_text(keyword)

    if not keyword:
        return False

    return keyword in text


# ==========================================================
# Detect Job Type
# ==========================================================

def is_job_post(job):

    text = build_job_text(job)

    if not text:
        return False

    # ------------------------------------------------------
    # Explicit scraper category
    # ------------------------------------------------------

    category = normalize_text(
        job.get("category")
    )

    if category in {

        "result",
        "results",
        "admit card",
        "answer key",
        "scholarship",
        "syllabus",
        "government schemes",
        "teaching exams",
        "entrance exams"

    }:

        return False


    # ------------------------------------------------------
    # Strong non-job signals
    # ------------------------------------------------------

    strong_non_job = [

        "admit card",
        "hall ticket",
        "answer key",
        "final answer key",
        "provisional answer key",
        "result",
        "final result",
        "merit list",
        "scorecard",
        "syllabus",
        "scholarship",
        "yojana",
        "government scheme"

    ]

    for keyword in strong_non_job:

        if contains_keyword(
            text,
            keyword
        ):
            return False


    # ------------------------------------------------------
    # Job keywords
    # ------------------------------------------------------

    for keyword in JOB_KEYWORDS:

        if contains_keyword(
            text,
            keyword
        ):
            return True


    return False


# ==========================================================
# Detect Categories
# ==========================================================

def detect_categories(job):

    matched = set()

    text = build_job_text(job)

    category = normalize_text(
        job.get("category")
    )


    # ------------------------------------------------------
    # 1. Explicit Category
    # ------------------------------------------------------

    if category in CATEGORY_MAP:

        matched.add(
            CATEGORY_MAP[category]
        )


    # ------------------------------------------------------
    # 2. Keyword Detection
    # ------------------------------------------------------

    for page, keywords in CATEGORY_RULES.items():

        for keyword in keywords:

            if contains_keyword(
                text,
                keyword
            ):

                matched.add(page)

                break


    # ------------------------------------------------------
    # 3. Latest Jobs
    #
    # IMPORTANT:
    # Only actual job/recruitment posts are added here.
    # ------------------------------------------------------

    if is_job_post(job):

        matched.add(
            "latest-jobs"
        )


    # ------------------------------------------------------
    # 4. Fallback
    # ------------------------------------------------------

    if not matched:

        matched.add(
            "other-state-jobs"
        )


    return list(
        matched
    )


# ==========================================================
# Group Jobs
# ==========================================================

def group_jobs(jobs):

    grouped = {

        page: []

        for page in CATEGORY_FILES

    }


    if not jobs:

        logger.warning(
            "No jobs received for category grouping."
        )

        return grouped


    seen = {

        page: set()

        for page in CATEGORY_FILES

    }


    for job in jobs:

        if not isinstance(
            job,
            dict
        ):
            continue


        title = safe(
            job.get("title")
        )

        url = safe(
            job.get("url")
        )


        if not title and not url:

            continue


        pages = detect_categories(
            job
        )


        for page in pages:

            if page not in grouped:

                continue


            # ------------------------------------------------
            # Duplicate Protection
            # ------------------------------------------------

            unique_key = (

                url.lower()

                if url

                else slugify(title)

            )


            if unique_key in seen[page]:

                continue


            seen[page].add(
                unique_key
            )

            grouped[page].append(
                job
            )


    # ======================================================
    # Latest Jobs Sorting
    # ======================================================

    for page in grouped:

        grouped[page].sort(

            key=lambda job: (
                safe(
                    job.get("publish_date")
                    or job.get("date")
                ),
                safe(
                    job.get("title")
                ).lower()
            ),

            reverse=True

        )


    # ======================================================
    # Apply Category Limits
    # ======================================================

    for page in grouped:

        if page == "latest-jobs":

            grouped[page] = grouped[page][
                :MAX_LATEST_JOBS
            ]

        else:

            grouped[page] = grouped[page][
                :MAX_POSTS_PER_CATEGORY
            ]


    logger.info(
        "Category Grouping Completed | Jobs=%d | Latest=%d",
        len(jobs),
        len(grouped.get("latest-jobs", []))
    )


    return grouped


# ==========================================================
# Part 3 Loaded
# ==========================================================

logger.info(
    "Category Generator V5 Part 3 Loaded Successfully"
)
# ==========================================================
# Education Update Hub
# Category Generator V5
# Part 4 : Category Page Update Engine
# ==========================================================


# ==========================================================
# Replace Auto Category Section
# ==========================================================

def replace_category_section(content, items):

    if not content:
        return content

    start = content.find(
        START_MARKER
    )

    end = content.find(
        END_MARKER
    )


    # ------------------------------------------------------
    # Markers Missing
    # ------------------------------------------------------

    if start == -1 or end == -1:

        logger.warning(
            "Category markers not found in HTML."
        )

        return content


    # ------------------------------------------------------
    # Invalid Marker Order
    # ------------------------------------------------------

    if end < start:

        logger.warning(
            "Invalid category marker order."
        )

        return content


    end += len(
        END_MARKER
    )


    # ------------------------------------------------------
    # Empty Category
    # ------------------------------------------------------

    if not items:

        items = [
            build_empty_category()
        ]


    # ------------------------------------------------------
    # Build Automatic Section
    # ------------------------------------------------------

    auto_section = (

        START_MARKER

        + "\n\n"

        + "\n".join(items)

        + "\n\n"

        + END_MARKER

    )


    # ------------------------------------------------------
    # Replace Existing Section
    # ------------------------------------------------------

    return (

        content[:start]

        + auto_section

        + content[end:]

    )


# ==========================================================
# Read Category HTML
# ==========================================================

def read_category_page(
    page,
    file_path
):

    if not file_path.exists():

        logger.warning(
            "Category page not found: %s",
            file_path
        )

        return None


    try:

        content = file_path.read_text(
            encoding="utf-8"
        )

        return content


    except Exception as error:

        logger.exception(
            "Failed reading category page %s: %s",
            page,
            error
        )

        return None


# ==========================================================
# Write Category HTML
# ==========================================================

def write_category_page(
    page,
    file_path,
    content
):

    if not content:

        logger.warning(
            "Empty content. Skipping write: %s",
            page
        )

        return False


    try:

        file_path.write_text(
            content,
            encoding="utf-8"
        )

        logger.info(
            "Category Updated: %s | %s",
            page,
            file_path
        )

        return True


    except Exception as error:

        logger.exception(
            "Failed writing category page %s: %s",
            page,
            error
        )

        return False


# ==========================================================
# Build Category Cards
# ==========================================================

def build_category_items(
    jobs
):

    items = []


    if not jobs:

        return [
            build_empty_category()
        ]


    for job in jobs:

        if not isinstance(
            job,
            dict
        ):

            continue


        try:

            items.append(
                build_category_card(job)
            )

        except Exception as error:

            logger.exception(
                "Card generation failed: %s | %s",
                job.get("title"),
                error
            )


    if not items:

        return [
            build_empty_category()
        ]


    return items


# ==========================================================
# Update One Category
# ==========================================================

def update_category(
    page,
    jobs
):

    file_path = CATEGORY_FILES.get(
        page
    )


    if file_path is None:

        logger.warning(
            "Unknown category page: %s",
            page
        )

        return False


    content = read_category_page(
        page,
        file_path
    )


    if content is None:

        return False


    items = build_category_items(
        jobs
    )


    updated_content = replace_category_section(
        content,
        items
    )


    if updated_content == content:

        logger.warning(
            "No changes made to category: %s",
            page
        )

        return False


    return write_category_page(
        page,
        file_path,
        updated_content
    )


# ==========================================================
# Update All Category Pages
# ==========================================================

def update_all_categories(
    grouped
):

    updated = 0


    for page in CATEGORY_FILES:

        jobs = grouped.get(
            page,
            []
        )


        logger.info(
            "Updating category: %s | Jobs: %d",
            page,
            len(jobs)
        )


        if update_category(
            page,
            jobs
        ):

            updated += 1


    logger.info(
        "Category Pages Updated: %d/%d",
        updated,
        len(CATEGORY_FILES)
    )


    return updated


# ==========================================================
# Validate Category Files
# ==========================================================

def validate_category_files():

    missing = []

    marker_missing = []


    for page, file_path in CATEGORY_FILES.items():

        if not file_path.exists():

            missing.append(
                page
            )

            continue


        try:

            content = file_path.read_text(
                encoding="utf-8"
            )


            if (
                START_MARKER not in content
                or
                END_MARKER not in content
            ):

                marker_missing.append(
                    page
                )


        except Exception:

            marker_missing.append(
                page
            )


    if missing:

        logger.warning(
            "Missing category pages: %s",
            ", ".join(missing)
        )


    if marker_missing:

        logger.warning(
            "Category markers missing: %s",
            ", ".join(marker_missing)
        )


    if not missing and not marker_missing:

        logger.info(
            "All category pages and markers validated."
        )


    return (
        missing,
        marker_missing
    )


# ==========================================================
# Part 4 Loaded
# ==========================================================

logger.info(
    "Category Generator V5 Part 4 Loaded Successfully"
)
# ==========================================================
# Education Update Hub
# Category Generator V5
# Part 5 : Complete Category Build Pipeline
# ==========================================================


# ==========================================================
# Category Statistics
# ==========================================================

def category_statistics(grouped):

    logger.info("=" * 60)
    logger.info("CATEGORY STATISTICS")
    logger.info("=" * 60)

    for page in CATEGORY_FILES:

        count = len(
            grouped.get(
                page,
                []
            )
        )

        logger.info(
            "%-28s : %d jobs",
            page,
            count
        )

    logger.info("=" * 60)


# ==========================================================
# Optimize Category Jobs
# ==========================================================

def optimize_categories(grouped):

    optimized = {}

    for page, jobs in grouped.items():

        unique_jobs = []
        seen = set()

        for job in jobs:

            if not isinstance(
                job,
                dict
            ):
                continue

            title = safe(
                job.get("title")
            )

            url = safe(
                job.get("url")
            )

            unique_key = (
                url.lower()
                if url
                else slugify(title)
            )

            if not unique_key:
                continue

            if unique_key in seen:
                continue

            seen.add(
                unique_key
            )

            unique_jobs.append(
                job
            )

        # --------------------------------------------------
        # Newest posts first
        # --------------------------------------------------

        unique_jobs.sort(

            key=lambda job: (
                safe(
                    job.get("publish_date")
                    or job.get("date")
                ),
                safe(
                    job.get("title")
                ).lower()
            ),

            reverse=True

        )

        # --------------------------------------------------
        # Category Limit
        # --------------------------------------------------

        if page == "latest-jobs":

            optimized[page] = (
                unique_jobs[
                    :MAX_LATEST_JOBS
                ]
            )

        else:

            optimized[page] = (
                unique_jobs[
                    :MAX_POSTS_PER_CATEGORY
                ]
            )

    return optimized


# ==========================================================
# Build Categories
# ==========================================================

def build_categories(jobs):

    logger.info("=" * 60)
    logger.info("Starting Category Generation V5")
    logger.info("=" * 60)


    # ------------------------------------------------------
    # Safety Check
    # ------------------------------------------------------

    if jobs is None:

        logger.warning(
            "Jobs is None. Category generation skipped."
        )

        return 0


    if not isinstance(
        jobs,
        list
    ):

        logger.warning(
            "Invalid jobs data type: %s",
            type(jobs).__name__
        )

        return 0


    logger.info(
        "Input Jobs: %d",
        len(jobs)
    )


    # ------------------------------------------------------
    # Validate HTML Pages
    # ------------------------------------------------------

    validate_category_files()


    # ------------------------------------------------------
    # Detect + Group
    # ------------------------------------------------------

    grouped = group_jobs(
        jobs
    )


    # ------------------------------------------------------
    # Optimize
    # ------------------------------------------------------

    grouped = optimize_categories(
        grouped
    )


    # ------------------------------------------------------
    # Statistics
    # ------------------------------------------------------

    category_statistics(
        grouped
    )


    # ------------------------------------------------------
    # Update HTML Pages
    # ------------------------------------------------------

    updated = update_all_categories(
        grouped
    )


    logger.info(
        "Updated Category Pages: %d",
        updated
    )


    logger.info("=" * 60)
    logger.info("Category Generation V5 Completed")
    logger.info("=" * 60)


    return updated


# ==========================================================
# Complete Build
# ==========================================================

def build(jobs):

    try:

        return build_categories(
            jobs
        )

    except Exception as error:

        logger.exception(
            "Category Build Failed: %s",
            error
        )

        return 0


# ==========================================================
# Main Runner
# ==========================================================

def run(jobs):

    logger.info(
        "Category Generator V5 Run Started"
    )


    try:

        result = build(
            jobs
        )


        logger.info(
            "Category Generator V5 Run Finished | Updated: %d",
            result
        )


        return result


    except Exception as error:

        logger.exception(
            "Category Generator V5 Error: %s",
            error
        )

        return 0


# ==========================================================
# Final Status
# ==========================================================

logger.info("=" * 60)
logger.info(
    "Education Update Hub Category Generator V5 Loaded"
)
logger.info("=" * 60)
# ==========================================================
# Education Update Hub
# Category Generator V5
# Part 6 : Final Validation + Safe Entry Point
# ==========================================================


# ==========================================================
# Validate Jobs Before Generation
# ==========================================================

def validate_jobs(jobs):

    if jobs is None:

        logger.warning(
            "Validation Failed: jobs is None"
        )

        return []


    if not isinstance(
        jobs,
        list
    ):

        logger.warning(
            "Validation Failed: jobs must be a list"
        )

        return []


    valid_jobs = []

    seen = set()


    for job in jobs:

        if not isinstance(
            job,
            dict
        ):

            continue


        title = safe(
            job.get("title")
        )

        url = safe(
            job.get("url")
        )


        if not title and not url:

            continue


        unique_key = (

            url.lower()

            if url

            else slugify(title)

        )


        if not unique_key:

            continue


        if unique_key in seen:

            continue


        seen.add(
            unique_key
        )


        valid_jobs.append(
            job
        )


    logger.info(
        "Job Validation: %d/%d valid",
        len(valid_jobs),
        len(jobs)
    )


    return valid_jobs


# ==========================================================
# Final Category Validation
# ==========================================================

def validate_generated_categories():

    results = {}


    for page, file_path in CATEGORY_FILES.items():

        result = {

            "exists": False,
            "markers": False,
            "file": str(file_path)

        }


        if not file_path.exists():

            results[page] = result

            continue


        result["exists"] = True


        try:

            content = file_path.read_text(
                encoding="utf-8"
            )


            result["markers"] = (

                START_MARKER in content

                and

                END_MARKER in content

            )


        except Exception as error:

            logger.exception(
                "Validation failed: %s | %s",
                page,
                error
            )


        results[page] = result


    return results


# ==========================================================
# Final Report
# ==========================================================

def generation_report(
    jobs,
    updated_pages
):

    logger.info("=" * 60)
    logger.info("CATEGORY GENERATION REPORT")
    logger.info("=" * 60)

    logger.info(
        "Valid Jobs        : %d",
        len(jobs)
    )

    logger.info(
        "Updated Pages     : %d",
        updated_pages
    )

    validation = (
        validate_generated_categories()
    )


    valid_pages = 0

    for page, info in validation.items():

        if (
            info["exists"]
            and
            info["markers"]
        ):

            valid_pages += 1


    logger.info(
        "Valid Category Pages : %d/%d",
        valid_pages,
        len(CATEGORY_FILES)
    )

    logger.info("=" * 60)


    return validation


# ==========================================================
# FINAL PUBLIC RUNNER
# ==========================================================

def generate_categories(jobs):

    logger.info(
        "Starting Final Category Generator V5"
    )


    valid_jobs = validate_jobs(
        jobs
    )


    if not valid_jobs:

        logger.warning(
            "No valid jobs available."
        )

        return 0


    updated_pages = build_categories(
        valid_jobs
    )


    generation_report(
        valid_jobs,
        updated_pages
    )


    logger.info(
        "Final Category Generator V5 Completed"
    )


    return updated_pages


# ==========================================================
# Public API
# ==========================================================

def run(jobs):

    try:

        return generate_categories(
            jobs
        )

    except Exception as error:

        logger.exception(
            "Category Generator V5 Fatal Error: %s",
            error
        )

        return 0


# ==========================================================
# Module Ready
# ==========================================================

logger.info("=" * 60)
logger.info(
    "Education Update Hub - Category Generator V5 READY"
)
logger.info("=" * 60)
