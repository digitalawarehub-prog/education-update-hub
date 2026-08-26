# ==========================================================
# HTML Generator V5.0 - Production Fixed
# Part 1 : Imports + Configuration + Helpers
# ==========================================================

import os
import re
import html
import json
import logging
from pathlib import Path
from datetime import datetime
try:
    from quality_gate import is_publishable, clean_optional_value
except Exception:
    def is_publishable(job): return True
    def clean_optional_value(v): return str(v or "").strip()

logger = logging.getLogger("HTMLGeneratorV4")
logger.setLevel(logging.INFO)

import homepage
import category_generator

# ==========================================================
# Project Paths
# ==========================================================

BASE_URL = "https://educationupdatehub.in"

ROOT_DIR = Path(__file__).resolve().parent.parent

OUTPUT_DIR = ROOT_DIR / "generated" / "posts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_IMAGE = "images/default-job.png"

# Homepage
INDEX_FILE = ROOT_DIR / "index.html"

# Category Pages
CATEGORY_PAGES = {
    "Latest Jobs": "latest-jobs.html",
    "Result": "result.html",
    "Results": "result.html",
    "Admit Card": "admit-card.html",
    "Answer Key": "answer-key.html",
    "Scholarship": "scholarship.html",
    "Syllabus": "syllabus.html",
    "Central Jobs": "central-government-jobs.html",
    "Uttarakhand Jobs": "uttarakhand-jobs.html",
    "Other State Jobs": "other-state-jobs.html",
}

# ==========================================================
# Slug Generator
# ==========================================================

def generate_slug(title):
    """Create a safe, short, deterministic filename slug.

    Long scraper titles can exceed the OS filename/path limit. Keep the
    readable beginning and append a deterministic hash so every post gets
    a unique, stable filename while staying well below the limit.
    """
    if not title:
        return "post"

    raw = str(title).strip().lower()
    raw = re.sub(r"\{\{.*?\}\}", "", raw).strip()

    slug = re.sub(r"[^a-z0-9]+", "-", raw)
    slug = re.sub(r"-+", "-", slug).strip("-")

    if not slug:
        import hashlib
        return "post-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]

    # Keep the final filename comfortably below filesystem/path limits.
    # 72 chars + 13-char hash = max ~86 chars including .html.
    import hashlib
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    max_readable = 72

    if len(slug) > max_readable:
        slug = slug[:max_readable].rstrip("-")
        slug = f"{slug}-{digest}"

    return slug

# ==========================================================
# HTML Escape
# ==========================================================

def escape_html(text):

    if text is None:
        return ""

    return html.escape(str(text))

# ==========================================================
# Image Helper
# ==========================================================

def get_image(job):

    return (
        job.get("featured_image")
        or job.get("thumbnail")
        or job.get("image")
        or DEFAULT_IMAGE
    )

def _clean_detail(value):
    value = str(value or "").strip()
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip(" -:|;,.\n\t")


def _plain_text(text):
    text = str(text or "")
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;?", " ", text, flags=re.I)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_detail_from_text(text, patterns):
    text = _plain_text(text)
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = _clean_detail(match.group(1))
            if value:
                return value[:300]
    return ""


def _extract_last_date(job):
    # Prefer an explicitly supplied field.
    explicit = _clean_detail(
        job.get("last_date")
        or job.get("closing_date")
        or job.get("application_last_date")
    )
    if explicit:
        return explicit

    text = " ".join([
        str(job.get("title") or ""),
        str(job.get("description") or ""),
        str(job.get("content") or ""),
    ])

    patterns = [
        r"(?:last\s*date|closing\s*date|application\s*last\s*date|apply\s*online\s*last\s*date)"
        r"\s*(?:[:\-]|is|are)?\s*([0-3]?\d[/-][01]?\d[/-](?:20)?\d{2})",
        r"(?:अंतिम\s*तिथि|आवेदन\s*की\s*अंतिम\s*तिथि|अंतिम\s*दिन)"
        r"\s*(?:[:\-]|है|होगी)?\s*([0-3]?\d[/-][01]?\d[/-](?:20)?\d{2})",
        r"\[\s*(?:अंतिम\s*तिथि|last\s*date)\s*:\s*([0-3]?\d[/-][01]?\d[/-](?:20)?\d{2})\s*\]",
        r"\[\s*(?:अंतिम\s*तिथि|last\s*date)\s*[:\-]\s*([0-3]?\d[/-][01]?\d[/-](?:20)?\d{2})\s*\]",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return _clean_detail(match.group(1))

    return ""


def detail_value(job, key, default=""):
    aliases = {
        "vacancy": (
            "vacancy", "posts", "no_of_posts",
            "number_of_posts", "total_posts", "post_count"
        ),
        "qualification": (
            "qualification", "eligibility",
            "educational_qualification", "education"
        ),
        "salary": (
            "salary", "pay_scale", "pay",
            "pay_level", "remuneration", "emoluments"
        ),
        "last_date": (
            "last_date", "closing_date",
            "application_last_date", "apply_last_date"
        ),
    }

    # 1. Direct structured field.
    for field in aliases.get(key, (key,)):
        value = _clean_detail(job.get(field))
        if value:
            return value

    # 2. Last date can frequently be recovered from the title.
    if key == "last_date":
        value = _extract_last_date(job)
        if value:
            return value

    # 3. Extract from the combined scraped text.
    text = " ".join([
        str(job.get("title") or ""),
        str(job.get("description") or ""),
        str(job.get("content") or ""),
        " ".join(str(x) for x in (job.get("keywords") or [])),
    ])

    patterns = {
        "vacancy": [
            r"(?:no\.?\s*of\s*(?:posts|vacancies)|number\s*of\s*(?:posts|vacancies)|total\s*(?:posts|vacancies))"
            r"\s*(?:[:\-]|is|are)?\s*(\d+(?:\s*[-–]\s*\d+)?)",
            r"(\d+)\s+(?:vacancies|vacancy|posts?)\b",
            r"(?:vacancy|posts?)\s*(?:[:\-]|is|are)\s*(\d+(?:\s*[-–]\s*\d+)?)",
        ],
        "qualification": [
            r"(?:educational\s+qualification|essential\s+qualification|qualification|eligibility)"
            r"\s*(?:[:\-]|is|are)?\s*([^\n|.;]{5,250})",
            r"(?:शैक्षणिक\s+योग्यता|योग्यता|पात्रता)"
            r"\s*(?:[:\-]|है|हैं)?\s*([^\n|.;]{5,250})",
        ],
        "salary": [
            r"(?:salary|pay\s+scale|pay\s+level|remuneration|emoluments?)"
            r"\s*(?:[:\-]|is|are)?\s*([^\n|.;]{2,180})",
            r"(?:वेतन|वेतनमान|मानदेय|पारिश्रमिक)"
            r"\s*(?:[:\-]|है|हैं)?\s*([^\n|.;]{2,180})",
        ],
        "last_date": [
            r"(?:last\s*date|closing\s*date|application\s*last\s*date|apply\s*online\s*last\s*date)"
            r"\s*(?:[:\-]|is|are)?\s*([^\n|]{3,120})",
            r"(?:अंतिम\s*तिथि|आवेदन\s*की\s*अंतिम\s*तिथि|अंतिम\s*दिन)"
            r"\s*(?:[:\-]|है|होगी)?\s*([^\n|]{3,120})",
        ],
    }

    value = _extract_detail_from_text(text, patterns.get(key, []))
    if value:
        return value

    return ""


def is_recruitment_post(job):
    text = " ".join(
        str(job.get(k) or "")
        for k in ("title", "category", "content", "description")
    ).lower()

    keywords = (
        "recruitment", "vacancy", "vacancies", "apply online",
        "job", "jobs", "advertisement", "walk-in",
        "भर्ती", "रिक्त", "नियुक्ति", "पद", "भरती", "विज्ञापन",
        "जाहिरात"
    )

    return any(k in text for k in keywords)


# ==========================================================
# Meta Description
# ==========================================================

def generate_meta_description(job):

    title = escape_html(job.get("title", ""))

    category = escape_html(job.get("category", "Latest Jobs"))

    department = escape_html(job.get("department", ""))

    parts = [title]
    if category: parts.append(category)
    if department: parts.append(f"from {department}")
    for label, key in (("Vacancy", "vacancy"), ("Qualification", "qualification"), ("Last Date", "last_date")):
        value = detail_value(job, key, "")
        if value: parts.append(f"{label}: {value}")
    return escape_html(". ".join(parts))[:160]

# ==========================================================
# Canonical URL
# ==========================================================

def canonical_url(slug):

    return f"{BASE_URL}/generated/posts/{slug}.html"

# ==========================================================
# Published Date
# ==========================================================

def published_date():

    return datetime.utcnow().strftime("%Y-%m-%d")

# ==========================================================
# Breadcrumb
# ==========================================================

def breadcrumb(job):

    category = job.get("category", "Latest Jobs")

    page = CATEGORY_PAGES.get(
        category,
        "latest-jobs.html"
    )

    return [
        {
            "name": "Home",
            "url": BASE_URL
        },
        {
            "name": category,
            "url": f"{BASE_URL}/{page}"
        },
        {
            "name": job.get("title", ""),
            "url": canonical_url(
                generate_slug(job.get("title", ""))
            )
        }
    ]

logger.info("HTML Generator V4 Part 1 Loaded Successfully")
# ==========================================================
# Part 2 : HTML Head + SEO + Schema
# ==========================================================

def build_html_head(job):

    title = escape_html(
        job.get("title", "Latest Update")
    )

    slug = generate_slug(title)

    description = generate_meta_description(job)

    image = get_image(job)

    canonical = canonical_url(slug)

    publish_date = published_date()

    breadcrumb_items = breadcrumb(job)

    breadcrumb_schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": []
    }

    for index, item in enumerate(breadcrumb_items, start=1):

        breadcrumb_schema["itemListElement"].append({
            "@type": "ListItem",
            "position": index,
            "name": item["name"],
            "item": item["url"]
        })

    article_schema = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": title,
        "description": description,
        "image": image,
        "datePublished": publish_date,
        "dateModified": publish_date,
        "mainEntityOfPage": canonical,
        "author": {
            "@type": "Organization",
            "name": "Education Update Hub"
        },
        "publisher": {
            "@type": "Organization",
            "name": "Education Update Hub",
            "logo": {
                "@type": "ImageObject",
                "url": f"{BASE_URL}/images/logo.png"
            }
        }
    }

    return f"""<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>{title} | Education Update Hub</title>

<meta name="description"
content="{description}">

<meta name="keywords"
content="{title}, Government Jobs, Sarkari Result, Admit Card, Results, Answer Key, Scholarship">

<meta name="robots"
content="index,follow">

<meta name="author"
content="Education Update Hub">

<link rel="canonical"
href="{canonical}">

<link rel="stylesheet"
href="../../style.css">

<link rel="icon"
href="../../favicon.ico">

<!-- Open Graph -->

<meta property="og:type"
content="article">

<meta property="og:title"
content="{title}">

<meta property="og:description"
content="{description}">

<meta property="og:image"
content="{image}">

<meta property="og:url"
content="{canonical}">

<meta property="og:site_name"
content="Education Update Hub">

<!-- Twitter -->

<meta name="twitter:card"
content="summary_large_image">

<meta name="twitter:title"
content="{title}">

<meta name="twitter:description"
content="{description}">

<meta name="twitter:image"
content="{image}">

<!-- Google Adsense -->

<meta name="google-adsense-account"
content="ca-pub-4508009805424675">

<!-- Article Schema -->

<script type="application/ld+json">

{json.dumps(article_schema, indent=2)}

</script>

<!-- Breadcrumb Schema -->

<script type="application/ld+json">

{json.dumps(breadcrumb_schema, indent=2)}

</script>

</head>
"""
# ==========================================================
# Part 3 : HTML Body Template
# ==========================================================

def is_recruitment_post(job):
    text = " ".join(str(job.get(k) or "") for k in ("title", "category", "content", "description")).lower()
    keywords = (
        "recruitment", "vacancy", "vacancies", "apply online", "job", "jobs",
        "भर्ती", "रिक्त", "नियुक्ति", "पद", "भरती", "जाहिरात"
    )
    return any(k in text for k in keywords)


def _valid_link(value):
    value = str(value or "").strip()
    return value.startswith(("http://", "https://", "/", "../", "../../")) and value not in {"#", "javascript:void(0)"}


def _clean_content(value):
    text = str(value or "")
    text = text.replace("\\n", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def build_html_body(job):
    title = escape_html(job.get("title", ""))
    category = escape_html(job.get("category", "Latest Jobs"))
    department = escape_html(job.get("department", ""))
    description = escape_html(job.get("description", ""))
    content = _clean_content(job.get("content", ""))

    rows = []
    values = [
        ("Vacancy", detail_value(job, "vacancy", "")),
        ("Qualification", detail_value(job, "qualification", "")),
        ("Salary / Pay Scale", detail_value(job, "salary", "")),
        ("Age Limit", detail_value(job, "age_limit", "")),
        ("Application Fee", detail_value(job, "application_fee", "")),
        ("Selection Process", detail_value(job, "selection_process", "")),
        ("Exam Date", detail_value(job, "exam_date", "")),
        ("Application Start", detail_value(job, "application_start", "")),
        ("Last Date", detail_value(job, "last_date", "")),
    ]
    for label, value in values:
        value = _clean_detail(value)
        if value and value.lower() not in {"not available", "not mentioned", "check official notification", "as per rules", "n/a", "na"}:
            rows.append(f"<tr><th>{escape_html(label)}</th><td>{escape_html(value)}</td></tr>")

    apply_link = job.get("apply_link") or ""
    notification = job.get("notification_pdf") or ""
    official = job.get("official_website") or ""
    source_url = job.get("url") or ""

    buttons = []
    if _valid_link(apply_link):
        buttons.append(f'<a class="apply-btn" href="{escape_html(apply_link)}" target="_blank" rel="noopener">🚀 Apply Online</a>')
    if _valid_link(notification):
        buttons.append(f'<a class="notification-btn" href="{escape_html(notification)}" target="_blank" rel="noopener">📄 Official Notification</a>')
    if _valid_link(official):
        buttons.append(f'<a class="official-btn" href="{escape_html(official)}" target="_blank" rel="noopener">🌐 Official Website</a>')
    elif _valid_link(source_url) and not buttons:
        buttons.append(f'<a class="official-btn" href="{escape_html(source_url)}" target="_blank" rel="noopener">🌐 Official Source</a>')

    detail_section = ""
    if rows:
        detail_section = '<h2>📋 Details</h2><table class="job-table">' + ''.join(rows) + '</table>'

    content_section = ""
    if content:
        content_section = f'<div class="post-content">{escape_html(content).replace(chr(10), "<br>")}</div>'
    elif description:
        content_section = f'<div class="post-content"><p>{description}</p></div>'

    button_section = f'<div class="post-buttons">{"".join(buttons)}</div>' if buttons else ""

    return f"""
<body>
<div id="header"></div>
<main class="post-wrapper"><div class="post-container">
<nav class="breadcrumb"><a href="../../index.html">Home</a><span>›</span><a href="{CATEGORY_PAGES.get(category, 'latest-jobs.html')}">{category}</a><span>›</span><span>{title}</span></nav>
<h1 class="post-title">{title}</h1>
<p class="post-meta">📅 Published : {published_date()}" + (f" &nbsp;&nbsp;|&nbsp;&nbsp; 🏛 {department}" if department else "") + f"</p>
{f'<p class="post-description">{description}</p>' if description else ''}
{content_section}
{detail_section}
{button_section}
</div></main>
"""
# ==========================================================
# Part 4 : Share + Navigation (no generic FAQ/content)
# ==========================================================
def build_extra_sections(job):
    title = escape_html(job.get("title", ""))
    canonical = canonical_url(generate_slug(title))
    return f"""
<section class="share-section"><h2>📤 Share This Update</h2>
<div class="share-buttons">
<a target="_blank" rel="noopener" href="https://wa.me/?text={canonical}">WhatsApp</a>
<a target="_blank" rel="noopener" href="https://t.me/share/url?url={canonical}">Telegram</a>
</div></section>
<section class="next-action"><a class="home-btn" href="../../index.html">🏠 Back to Home</a></section>
"""
# ==========================================================
# Part 5 : Core HTML Generation Engine
# ==========================================================

def build_html(job):

    # Correct production order:
    # Head -> Post -> Share -> FAQ -> Related -> Actions -> Footer -> Scripts.
    return (
        build_html_head(job)
        + build_html_body(job)
        + build_extra_sections(job)
        + """
<div id="footer"></div>

<script src="../../search.js"></script>
<script src="../../load.js"></script>
<script src="../../menu.js"></script>
<script src="../../script.js"></script>

</body>
</html>
"""
    )


# ==========================================================
# Write HTML File
# ==========================================================

def write_html_file(filename, html_content):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    filepath = OUTPUT_DIR / filename

    with open(
        filepath,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(html_content)

    return filepath


# ==========================================================
# Generate Single Post
# ==========================================================

def generate_post(job):

    title = str(
        job.get("title", "")
    ).strip()

    if not title:
        return None

    slug = generate_slug(title)
    filename = f"{slug}.html"

    if not is_publishable(job):
        logger.info("QUALITY GATE SKIP/NOINDEX : %s", title)
        job["publishable"] = False
        filepath = OUTPUT_DIR / filename
        noindex = f"<!doctype html><html><head><meta charset=\"utf-8\"><meta name=\"robots\" content=\"noindex,nofollow\"><link rel=\"canonical\" href=\"{canonical_url(slug)}\"><title>{escape_html(title)}</title></head><body></body></html>"
        write_html_file(filename, noindex)
        job["html_file"] = f"generated/posts/{filename}"
        return None

    job["publishable"] = True

    filename = f"{slug}.html"

    html_content = build_html(job)

    filepath = write_html_file(
        filename,
        html_content
    )

    job["html_file"] = (
        f"generated/posts/{filename}"
    )

    logger.info(
        "Generated : %s",
        filename
    )

    return filepath


# ==========================================================
# Generate All Posts
# ==========================================================

def generate_all(jobs):

    generated = []

    failed = 0

    seen = set()

    for job in jobs:

        title = str(
            job.get("title", "")
        ).strip()

        if not title:
            failed += 1
            continue

        slug = generate_slug(title)

        if slug in seen:
            continue

        seen.add(slug)

        try:

            filepath = generate_post(job)

            if filepath:
                generated.append(filepath)

        except Exception:

            logger.exception(
                "Generation Failed : %s",
                title
            )

            failed += 1

    logger.info(
        "Generated %d Files",
        len(generated)
    )

    return {
        "success": len(generated),
        "failed": failed,
        "total": len(jobs),
        "results": [
            str(file)
            for file in generated
        ]
    }


# ==========================================================
# Homepage Auto Sections
# ==========================================================

AUTO_SECTIONS = {

    "AUTO_LATEST_GRID":
        [],

    "AUTO_UK_JOBS":
        [],

    "AUTO_CENTRAL_JOBS":
        [],

    "AUTO_STATE_JOBS":
        [],

    "AUTO_LATEST_POSTS":
        []

}


# ==========================================================
# Homepage Data Safety
# ==========================================================

JUNK_TITLE_PATTERNS = (
    "support_agent",
    "academic courses",
    "event student",
    "event key dates",
    "more...",
    "vacancy/nia",
    "vacancy position",
)

def is_valid_homepage_job(job):
    title = str(job.get("title", "")).strip()

    if not title:
        return False

    low = title.lower()

    if low in {"notification", "results", "more", "more..."}:
        return False

    if any(pattern in low for pattern in JUNK_TITLE_PATTERNS):
        return False

    return True


def job_datetime(job):
    values = [
        job.get("publish_date"),
        job.get("date"),
        job.get("scraped_at"),
    ]

    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d %B %Y",
        "%d %b %Y",
        "%B %d, %Y",
        "%b %d, %Y",
    ]

    for value in values:
        value = str(value or "").strip()

        if not value:
            continue

        try:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            ).replace(tzinfo=None)
        except Exception:
            pass

        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except Exception:
                continue

    return datetime.min


def add_homepage_card(
    section,
    html
):

    if section in AUTO_SECTIONS:

        AUTO_SECTIONS[
            section
        ].append(html)


# ==========================================================
# Build Homepage Card
# ==========================================================

def build_latest_title_item(job):
    """Latest Updates: title only, no image/card/date/button."""
    title = escape_html(job.get("title", ""))
    slug = generate_slug(title)

    return f"""
<div class="homepage-title-item">
    <a href="generated/posts/{slug}.html">
        {title}
    </a>
</div>
"""


def build_category_card(job):
    """Category sections keep their normal compact cards."""
    title = escape_html(job.get("title", ""))
    image = get_image(job)
    slug = generate_slug(title)

    return f"""
<div class="post-card">
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
# Register Card Automatically
# ==========================================================

def register_homepage_card(job):

    if not is_valid_homepage_job(job):
        return

    latest_item = build_latest_title_item(job)
    category_card = build_category_card(job)

    # Latest Updates: title-only
    add_homepage_card(
        "AUTO_LATEST_GRID",
        latest_item
    )

    add_homepage_card(
        "AUTO_LATEST_POSTS",
        latest_item
    )

    category = str(
        job.get(
            "category",
            ""
        )
    ).lower()

    # Category sections: normal cards
    if "uttarakhand" in category:
        add_homepage_card(
            "AUTO_UK_JOBS",
            category_card
        )

    elif "central" in category:
        add_homepage_card(
            "AUTO_CENTRAL_JOBS",
            category_card
        )

    elif "state" in category:
        add_homepage_card(
            "AUTO_STATE_JOBS",
            category_card
        )

logger.info(
    "HTML Generator V4 Core Engine Loaded"
)
# ==========================================================
# Part 6 : Homepage Updater + Utilities
# ==========================================================

def replace_auto_section(content, marker, html_items):

    start = f"<!-- {marker}_START -->"
    end = f"<!-- {marker}_END -->"

    if start not in content or end not in content:
        return content

    before = content.split(start)[0]

    after = content.split(end)[1]

    middle = (
        start +
        "\n\n" +
        "\n".join(html_items) +
        "\n\n" +
        end
    )

    return before + middle + after


# ==========================================================
# Update Homepage
# ==========================================================

def update_homepage():

    if not INDEX_FILE.exists():

        logger.warning(
            "Homepage not found."
        )

        return False

    with open(
        INDEX_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        content = f.read()

    for section, items in AUTO_SECTIONS.items():

        content = replace_auto_section(
            content,
            section,
            items
        )

    with open(
        INDEX_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(content)

    logger.info(
        "Homepage Updated Successfully."
    )

    return True


# ==========================================================
# Verify Generated HTML
# ==========================================================

def verify_generated_files():

    html_files = list(
        OUTPUT_DIR.glob("*.html")
    )

    logger.info(
        "Verified %d HTML Files",
        len(html_files)
    )

    return len(html_files) > 0


# ==========================================================
# Clean Output Folder
# ==========================================================

def clean_output_directory():
    """Do not delete historical post files; preserving them prevents stale 404s."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    existing = len(list(OUTPUT_DIR.glob("*.html")))
    logger.info("Preserving %d historical HTML files", existing)


# ==========================================================
# Statistics
# ==========================================================

def html_statistics():

    html_files = list(
        OUTPUT_DIR.glob("*.html")
    )

    logger.info("=" * 50)
    logger.info("HTML Generator V4")
    logger.info("=" * 50)

    logger.info(
        "Total Generated : %d",
        len(html_files)
    )

    logger.info(
        "Output Folder : %s",
        OUTPUT_DIR
    )

    logger.info(
        "Homepage Cards : %d",
        len(AUTO_SECTIONS["AUTO_LATEST_GRID"])
    )

    logger.info(
        "Latest Posts : %d",
        len(AUTO_SECTIONS["AUTO_LATEST_POSTS"])
    )

    logger.info(
        "UK Jobs : %d",
        len(AUTO_SECTIONS["AUTO_UK_JOBS"])
    )

    logger.info(
        "Central Jobs : %d",
        len(AUTO_SECTIONS["AUTO_CENTRAL_JOBS"])
    )

    logger.info(
        "Other State Jobs : %d",
        len(AUTO_SECTIONS["AUTO_STATE_JOBS"])
    )

    logger.info("=" * 50)


# ==========================================================
# Final Build
# ==========================================================

def build_site(jobs):

    # Remove obvious scraper navigation records first.
    clean_jobs = [
        job for job in jobs
        if is_valid_homepage_job(job) and is_publishable(job)
    ]

    # Newest posts first.
    clean_jobs = sorted(
        clean_jobs,
        key=job_datetime,
        reverse=True
    )

    clean_output_directory()

    result = generate_all(clean_jobs)

    # IMPORTANT:
    # Do not let the old HTML generator card engine rebuild
    # Latest Updates after homepage.py has generated it.
    #
    # Homepage V5 is now the single authority for index.html.
    homepage.run(clean_jobs)

    category_generator.run(jobs)

    html_statistics()

    logger.info(
        "Website Generated Successfully."
    )

    return result


logger.info(
    "HTML Generator V4 Loaded Successfully."
)
