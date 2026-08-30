# ==========================================================
# Homepage Generator V5 Professional
# Part 1 : Imports + Configuration + Helpers
# ==========================================================

import re
import hashlib
import logging
import json
from filters import classify_post
from url_utils import post_relative_url

from pathlib import Path
from datetime import datetime, timedelta

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
# Robust File / URL Helpers
# ==========================================================

def write_text(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def html_link(job):
    """Return the same canonical generated-post URL used by html_generator."""
    return "/" + post_relative_url(job).lstrip("/")


# ==========================================================
# Noise / Navigation Item Filter
# ==========================================================

NOISE_TITLE_PATTERNS = (
    r"^view\s*all$",
    r"^view\s*more$",
    r"^more\.{0,3}$",
    r"^support$",
    r"^academic\s+courses?$",
    r"^student$",
    r"^key\s+dates?$",
    r"^vacancy\s*/\s*nia$",
    r"^varieties$",
)


def is_noise_job(job):
    title = re.sub(r"\s+", " ", safe(job.get("title"))).strip().lower()
    if not title:
        return True

    for pattern in NOISE_TITLE_PATTERNS:
        if re.search(pattern, title, re.I):
            return True

    # Common scraper navigation leakage.
    if title in {"view all results", "view all recruitment", "view results"}:
        return True

    return False


# ==========================================================
# Application Deadline Extraction
# ==========================================================

def _parse_any_date(raw):
    if not raw:
        return None

    s = re.sub(r"\s+", " ", str(raw).strip())

    patterns = [
        (r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b", ("%Y-%m-%d", "%Y/%m/%d")),
        (r"\b\d{1,2}[-/.]\d{1,2}[-/.]\d{4}\b", ("%d-%m-%Y",)),
        (
            r"\b\d{1,2}\s+"
            r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
            r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|"
            r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
            r"\s+\d{4}\b",
            ("%d %B %Y", "%d %b %Y"),
        ),
    ]

    for pattern, formats in patterns:
        m = re.search(pattern, s, re.I)
        if not m:
            continue
        raw_date = m.group(0).replace("/", "-").replace(".", "-")
        for fmt in formats:
            try:
                return datetime.strptime(raw_date, fmt)
            except ValueError:
                pass

    return None


def extract_application_deadline(job):
    """
    Read only dates that are explicitly associated with application/
    registration deadlines. This prevents exam dates and publish dates
    from incorrectly expiring a post.
    """
    deadline_keys = (
        "last_date",
        "deadline",
        "application_last_date",
        "last_date_to_apply",
        "application_deadline",
        "closing_date",
    )

    for key in deadline_keys:
        value = job.get(key)
        if value:
            dt = _parse_any_date(value)
            if dt:
                return dt

    # Fall back to explicit deadline phrases in title/description/content.
    text = " ".join(
        safe(job.get(k))
        for k in ("title", "description", "content", "summary", "last_date")
    )

    explicit_patterns = [
        r"(?:last\s*date|last\s*date\s*to\s*apply|application\s*(?:last\s*)?date|"
        r"deadline|closing\s*date|apply\s*(?:online\s*)?(?:till|by|before))"
        r"\s*[:\-]?\s*(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})",
        r"(?:अंतिम\s*तिथि|आवेदन\s*की\s*अंतिम\s*तिथि|अंतिम\s*तारीख)"
        r"\s*[:\-]?\s*(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})",
    ]

    for pattern in explicit_patterns:
        m = re.search(pattern, text, re.I)
        if m:
            dt = _parse_any_date(m.group(1))
            if dt:
                return dt

    return None


def is_expired_job(job):
    combined = " ".join(
        safe(job.get(k))
        for k in (
            "last_date",
            "deadline",
            "application_last_date",
            "last_date_to_apply",
            "application_deadline",
            "closing_date",
        )
    )

    if re.search(
        r"\b(?:application|applications|registration)\s+(?:is\s+|are\s+)?"
        r"(?:closed|over)\b|"
        r"\b(?:application|registration)\s+closed\b|"
        r"\bexpired\b|"
        r"\bआवेदन\s*(?:बंद|समाप्त)\b",
        combined,
        re.I
    ):
        return True

    dt = extract_application_deadline(job)
    return bool(dt and dt.date() < datetime.now().date())


def active_jobs(jobs):
    today = datetime.today().date()
    active = []
    for job in jobs:
        if not safe(job.get("title")) or not effective_category(job):
            continue
        # Expired applications never appear in homepage sections.
        if is_expired_job(job):
            continue
        raw = safe(job.get("publish_date") or job.get("published_date") or job.get("date") or job.get("last_seen_at") or job.get("scraped_at"))
        m = re.match(r"(20\d{2}-\d{2}-\d{2})", raw)
        if not m:
            continue
        try:
            pub = datetime.strptime(m.group(1), "%Y-%m-%d").date()
        except ValueError:
            continue
        if pub < today - timedelta(days=30):
            continue
        active.append(job)
    return active


# ==========================================================
# Effective Category
# ==========================================================

def effective_category(job):
    title = safe(job.get("title"))
    url = safe(job.get("url"))
    category = classify_post(title, url, safe(job.get("description")), safe(job.get("source")))
    if category:
        return category
    return ""

# ==========================================================
# Slug Helper
# ==========================================================

ENGLISH_SLUG_MAP = {"सरकारी":"government","नौकरी":"job","नौकरियां":"jobs","भर्ती":"recruitment","भर्तियां":"recruitments","रिक्ति":"vacancy","रिक्तियां":"vacancies","अधिसूचना":"notification","प्रवेश":"admit","पत्र":"card","परिणाम":"result","उत्तर":"answer","कुंजी":"key","छात्रवृत्ति":"scholarship","परीक्षा":"exam","पाठ्यक्रम":"syllabus","शिक्षक":"teacher","पुलिस":"police","वन":"forest","विभाग":"department","केंद्र":"central","राज्य":"state","उत्तराखंड":"uttarakhand","ऑनलाइन":"online","आवेदन":"application","अंतिम":"last","तिथि":"date"}

def slugify(title):
    raw = safe(title).strip().lower()
    raw = re.sub(r"\{\{.*?\}\}", "", raw)
    raw = raw.replace("&", " and ")
    for src, dst in sorted(ENGLISH_SLUG_MAP.items(), key=lambda x: len(x[0]), reverse=True):
        raw = raw.replace(src, dst)
    slug = re.sub(r"[^a-z0-9]+", "-", raw)
    slug = re.sub(r"-+", "-", slug).strip("-")
    if slug:
        return slug
    return "post-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12] if raw else "post"

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

    category_name = effective_category(job)

    last_date = safe(
        job.get("last_date")
        or job.get("date"),
        "Check Notification"
    )

    return f"""
<div class="post-card">

    <a href="{html_link(job)}">

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

            <a href="{html_link(job)}">

                {title}

            </a>

        </h3>

        <p class="post-date">

            📅 Last Date : {last_date}

        </p>

        <a
            class="read-more-btn"
            href="{html_link(job)}">

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

<a href="{html_link(job)}">

{title}

</a>

</li>
"""


# ==========================================================
# Latest Post Card
# ==========================================================

def build_latest_post(job):
    """
    Latest Updates: title-only clickable item.
    No image, description or card layout.
    """
    title = safe(job.get("title"), "Latest Update")
    slug = slugify(title)

    return f"""
<div class="latest-title-item">
    <a href="{html_link(job)}">
        🔹 {title}
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
<a href="{html_link(job)}">

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
🔴 <a href="{html_link(job)}">

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

    # Homepage Latest Updates — TITLE ONLY.
    # Never put build_homepage_card() output here.
    add_to_section(
        "AUTO_LATEST_GRID",
        latest
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

    category_name = effective_category(job).lower()

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
        raw = safe(
            job.get("publish_date")
            or job.get("date")
        )
        dt = _parse_any_date(raw)
        if dt:
            return dt
        return datetime.min

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
    jobs = active_jobs(jobs)

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


# ==========================================================
# SEARCH INDEX GENERATOR
# ==========================================================

SEARCH_INDEX_FILE = ROOT_DIR / "search-index.json"
SEARCH_DATA_FILE = ROOT_DIR / "search-data.js"


def generate_search_index(jobs):
    """
    Generate the JSON file consumed by the existing Search V5 frontend.
    Uses the same active job list as the homepage, so expired applications
    are not searchable from the dynamic index.
    """
    records = []

    for job in jobs:
        title = safe(job.get("title"))
        if not title:
            continue

        records.append({
            "title": title,
            "url": html_link(job),
            "category": effective_category(job),
            "department": safe(job.get("department")),
            "description": safe(job.get("description")),
            "keywords": job.get("tags", []) if isinstance(job.get("tags", []), list) else [],
        })

    write_text(
        SEARCH_INDEX_FILE,
        json.dumps(records, ensure_ascii=False, indent=2)
    )

    # Keep the old JS data file too, for backward compatibility with any
    # older search code still present in the site.
    write_text(
        SEARCH_DATA_FILE,
        "const searchData = " +
        json.dumps(records, ensure_ascii=False, indent=2) +
        ";"
    )

    logger.info("Search index generated: %d records", len(records))
    return records


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
    jobs = active_jobs(jobs)
    jobs = active_jobs(jobs)

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
    jobs = active_jobs(jobs)

    jobs = sort_jobs(jobs)

    # Generate the search database from the same active jobs.
    generate_search_index(jobs)

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
