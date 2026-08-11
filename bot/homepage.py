# ==========================================================
# Homepage Generator V5 Professional
# Part 1 : Imports + Configuration + Helpers
# ==========================================================

import re
import hashlib
import logging
import json

from pathlib import Path
from datetime import datetime

logger = logging.getLogger("HomepageGeneratorV5")

try:
    from category_generator import detect_categories
except Exception:
    detect_categories = None

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
    """Generate a stable URL slug shared with html_generator.py.

    English/Latin titles keep readable slugs. Hindi/other non-Latin
    titles get a deterministic SHA-1 fallback instead of an empty slug.
    """
    raw = safe(title).strip().lower()
    raw = re.sub(r"\{\{.*?\}\}", "", raw).strip()

    slug = re.sub(r"[^a-z0-9]+", "-", raw)
    slug = re.sub(r"-+", "-", slug).strip("-")

    if slug:
        return slug

    if not raw:
        return "post"

    return "post-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]

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


# ==========================================================
# Active Job / Deadline Filter
# ==========================================================

def _parse_deadline(value):
    """Parse common application deadline formats."""
    if not value:
        return None

    s = re.sub(r"\s+", " ", str(value).strip())

    # ISO: YYYY-MM-DD / YYYY/MM/DD
    m = re.search(r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b", s)
    if m:
        raw = m.group()
        for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                pass

    # DD-MM-YYYY / DD/MM/YYYY / DD.MM.YYYY
    m = re.search(r"\b\d{1,2}[-/.]\d{1,2}[-/.]\d{4}\b", s)
    if m:
        raw = m.group().replace("/", "-").replace(".", "-")
        try:
            return datetime.strptime(raw, "%d-%m-%Y")
        except ValueError:
            pass

    # 03 August 2026 / 03 Aug 2026
    m = re.search(
        r"\b\d{1,2}\s+"
        r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
        r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|"
        r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
        r"\s+\d{4}\b",
        s, re.I
    )
    if m:
        for fmt in ("%d %B %Y", "%d %b %Y"):
            try:
                return datetime.strptime(m.group(), fmt)
            except ValueError:
                pass

    return None


def is_expired_job(job):
    """Return True only when the application deadline is clearly over."""
    combined = " ".join(
        safe(job.get(k))
        for k in (
            "last_date",
            "deadline",
            "application_last_date",
            "last_date_to_apply",
        )
    )

    if re.search(
        r"\b(?:application|applications|registration)\s+(?:is\s+|are\s+)?"
        r"(?:closed|over)\b|\b(?:application|registration)\s+closed\b"
        r"|\bexpired\b",
        combined,
        re.I
    ):
        return True

    for key in (
        "last_date",
        "deadline",
        "application_last_date",
        "last_date_to_apply",
    ):
        dt = _parse_deadline(job.get(key))
        if dt:
            return dt.date() < datetime.now().date()

    return False


def active_jobs(jobs):
    """Keep only jobs whose application window is not clearly expired."""
    return [job for job in jobs if not is_expired_job(job)]

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

    <a href="/generated/posts/{slug}.html">

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

            <a href="/generated/posts/{slug}.html">

                {title}

            </a>

        </h3>

        <p class="post-date">

            📅 Last Date : {last_date}

        </p>

        <a
            class="read-more-btn"
            href="/generated/posts/{slug}.html">

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

<a href="/generated/posts/{slug}.html">

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
    <a href="/generated/posts/{slug}.html">
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
<a href="/generated/posts/{slug}.html">

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
🔴 <a href="/generated/posts/{slug}.html">

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
    department = safe(job.get("department")).lower()
    title = safe(job.get("title")).lower()
    state = safe(job.get("state")).lower()

    detected_pages = set()
    if detect_categories:
        try:
            detected_pages = set(detect_categories(job) or [])
        except Exception:
            detected_pages = set()

    # Same category engine as the category pages. This prevents
    # Uttarakhand/other-state jobs from being swallowed by the
    # generic Government department rule.
    if (
        "uttarakhand-jobs" in detected_pages
        or "uttarakhand" in category_name
        or "uttarakhand" in state
        or "uttarakhand" in title
        or "उत्तराखंड" in title
    ):
        add_to_section("AUTO_UK_JOBS", item)

    elif (
        "other-state-jobs" in detected_pages
        or any(page.endswith("-jobs") and page not in {
            "uttarakhand-jobs", "central-government-jobs"
        } for page in detected_pages)
        or state
    ):
        add_to_section("AUTO_STATE_JOBS", item)

    elif (
        "central-government-jobs" in detected_pages
        or "central" in category_name
        or "upsc" in category_name
        or "ssc" in category_name
        or "bank" in department
        or "railway" in department
        or "defence" in department
        or "central" in title
        or "upsc" in title
        or "ssc" in title
        or "ibps" in title
        or "rrb" in title
    ):
        add_to_section("AUTO_CENTRAL_JOBS", item)

    else:
        # Do not classify every Government job as Central.
        # Unknown state jobs go to Other State Jobs.
        add_to_section("AUTO_STATE_JOBS", item)


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
# Search Index Synchronization
# ==========================================================

SEARCH_INDEX_FILE = ROOT_DIR / "search-index.json"


def _merge_search_jobs(jobs):
    records = []
    if SEARCH_INDEX_FILE.exists():
        try:
            data = json.loads(SEARCH_INDEX_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                records.extend(data)
        except Exception:
            logger.warning("Existing search-index.json is invalid; rebuilding.")

    by_key = {}
    for record in records:
        if isinstance(record, dict):
            key = record.get("url") or record.get("slug") or record.get("title")
            if key:
                by_key[str(key)] = record

    for job in jobs:
        title = safe(job.get("title"))
        if not title:
            continue
        slug = slugify(title)
        url = f"/generated/posts/{slug}.html"
        by_key[url] = {
            "title": title,
            "slug": slug,
            "url": url,
            "category": safe(job.get("category"), "Latest Jobs"),
            "department": safe(job.get("department"), "Government"),
            "state": safe(job.get("state")),
            "publish_date": safe(job.get("publish_date") or job.get("date")),
            "last_date": safe(job.get("last_date") or job.get("deadline")),
            "description": safe(job.get("description"))[:300],
            "keywords": job.get("keywords", []) if isinstance(job.get("keywords", []), list) else []
        }

    SEARCH_INDEX_FILE.write_text(
        json.dumps(list(by_key.values()), ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    logger.info("Search Index Updated : %d", len(by_key))
    return True


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

    # Register

    clear_sections()

    register_jobs(jobs)

    # Apply Limits

    apply_limits()

    # Search Index

    _merge_search_jobs(jobs)

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
