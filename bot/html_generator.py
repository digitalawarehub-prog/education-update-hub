# ==========================================================
# HTML Generator V4.1
# Part 1 : Imports + Configuration + Helpers
# ==========================================================

import re
import html
import json
import logging

from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import homepage
import category_generator

logger = logging.getLogger("HTMLGeneratorV4")
logger.setLevel(logging.INFO)

# ==========================================================
# Configuration
# ==========================================================

BASE_URL = "https://educationupdatehub.in"

GA4_ID = "G-XRESX2YP1N"

TIMEZONE = ZoneInfo("Asia/Kolkata")

ROOT_DIR = Path(__file__).resolve().parent.parent

OUTPUT_DIR = ROOT_DIR / "generated" / "posts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_IMAGE = "images/default-job.png"

INDEX_FILE = ROOT_DIR / "index.html"

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
# Helpers
# ==========================================================

def escape_html(text):
    if text is None:
        return ""
    return html.escape(str(text))


def generate_slug(title):
    if not title:
        return "post"

    title = str(title).lower().strip()

    title = re.sub(r"\{\{.*?\}\}", "", title)
    title = re.sub(r"&", " and ", title)

    slug = re.sub(r"[^a-z0-9]+", "-", title)
    slug = re.sub(r"-+", "-", slug).strip("-")

    if slug:
        return slug

    return f"post-{abs(hash(title))}"


def get_image(job):
    return (
        job.get("featured_image")
        or job.get("thumbnail")
        or job.get("image")
        or DEFAULT_IMAGE
    )


def generate_meta_description(job):

    title = escape_html(job.get("title", ""))

    category = escape_html(
        job.get("category", "Latest Jobs")
    )

    department = escape_html(
        job.get("department", "")
    )

    desc = (
        f"{title}. "
        f"Latest {category} update from {department}. "
        f"Check eligibility, important dates, "
        f"official notification and apply online."
    )

    return desc[:160]


def canonical_url(slug):
    return f"{BASE_URL}/generated/posts/{slug}.html"


def published_date():
    return datetime.now(TIMEZONE).strftime("%Y-%m-%d")


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


logger.info("HTML Generator V4.1 Part 1 Loaded Successfully")
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

    # Relative image ko absolute bana do
    if not image.startswith("http"):
        image = f"{BASE_URL}/{image.lstrip('/')}"

    canonical = canonical_url(slug)

    publish_date = published_date()

    breadcrumb_items = breadcrumb(job)

    breadcrumb_schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": []
    }

    for index, item in enumerate(
        breadcrumb_items,
        start=1
    ):

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
        "image": [image],
        "datePublished": publish_date,
        "dateModified": publish_date,
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": canonical
        },
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
content="index,follow,max-image-preview:large">

<meta name="author"
content="Education Update Hub">

<link rel="canonical"
href="{canonical}">

<link rel="icon"
href="{BASE_URL}/favicon.ico">

<link rel="stylesheet"
href="../../style.css">

<!-- Google Analytics -->

<script async
src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}">
</script>

<script>
window.dataLayer = window.dataLayer || [];
function gtag(){{dataLayer.push(arguments);}}
gtag('js', new Date());
gtag('config', '{GA4_ID}');
</script>

<!-- Google Adsense -->

<meta name="google-adsense-account"
content="ca-pub-4508009805424675">

<!-- Open Graph -->

<meta property="og:type"
content="article">

<meta property="og:title"
content="{title}">

<meta property="og:description"
content="{description}">

<meta property="og:url"
content="{canonical}">

<meta property="og:image"
content="{image}">

<meta property="og:site_name"
content="Education Update Hub">

<meta property="og:locale"
content="en_IN">

<!-- Twitter -->

<meta name="twitter:card"
content="summary_large_image">

<meta name="twitter:title"
content="{title}">

<meta name="twitter:description"
content="{description}">

<meta name="twitter:image"
content="{image}">

<!-- NewsArticle Schema -->

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

def build_html_body(job):

    title = escape_html(job.get("title", ""))

    category = escape_html(
        job.get("category", "Latest Jobs")
    )

    department = escape_html(
        job.get("department", "Government")
    )

    vacancy = escape_html(
        job.get("vacancy", "Not Mentioned")
    )

    qualification = escape_html(
        job.get(
            "qualification",
            "Check Official Notification"
        )
    )

    salary = escape_html(
        job.get("salary", "Not Mentioned")
    )

    last_date = escape_html(
        job.get("last_date", "Not Available")
    )

    description = escape_html(
        job.get("description", "")
    )

    content = job.get("content", "")

    image = get_image(job)

    if not image.startswith("http"):
        image = f"../../{image.lstrip('/')}"

    apply_link = (
        job.get("apply_link")
        or job.get("url")
        or "#"
    )

    notification = (
        job.get("notification_pdf")
        or job.get("url")
        or "#"
    )

    official = (
        job.get("official_website")
        or job.get("url")
        or "#"
    )

    body = f"""
<body>

<div id="header"></div>

<main class="post-wrapper">

<div class="post-container">

<nav class="breadcrumb">

<a href="../../index.html">Home</a>

<span>›</span>

<a href="../../{CATEGORY_PAGES.get(category,'latest-jobs.html')}">

{category}

</a>

<span>›</span>

<span>{title}</span>

</nav>

<h1 class="post-title">

{title}

</h1>

<p class="post-meta">

📅 Published :
{published_date()}

&nbsp;&nbsp;|&nbsp;&nbsp;

🏛 {department}

</p>

<img
src="{image}"
alt="{title}"
class="featured-image"
loading="lazy">

<p class="post-description">

{description}

</p>

<div class="post-content">

{content.replace(chr(10), "<br>")}

</div>

<h2>📋 Recruitment Details</h2>

<table class="job-table">

<tr>
<th>Category</th>
<td>{category}</td>
</tr>

<tr>
<th>Department</th>
<td>{department}</td>
</tr>

<tr>
<th>Vacancy</th>
<td>{vacancy}</td>
</tr>

<tr>
<th>Qualification</th>
<td>{qualification}</td>
</tr>

<tr>
<th>Salary</th>
<td>{salary}</td>
</tr>

<tr>
<th>Last Date</th>
<td>{last_date}</td>
</tr>

</table>

<div class="post-buttons">

<a
class="apply-btn"
href="{apply_link}"
target="_blank"
rel="noopener">

🚀 Apply Online

</a>

<a
class="notification-btn"
href="{notification}"
target="_blank"
rel="noopener">

📄 Download Notification

</a>

<a
class="official-btn"
href="{official}"
target="_blank"
rel="noopener">

🌐 Official Website

</a>

</div>

"""

return body


# ==========================================================
# Part 4 : FAQ + Share + Related Posts + Footer
# ==========================================================

def build_extra_sections(job):

    title = escape_html(job.get("title", ""))

    apply_link = (
        job.get("apply_link")
        or job.get("url")
        or "#"
    )

    slug = generate_slug(title)

    canonical = canonical_url(slug)

    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": f"What is {title}?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": f"{title} official recruitment/update. Check eligibility, important dates and official notification."
                }
            },
            {
                "@type": "Question",
                "name": "How to Apply?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Click Apply Online button and complete the application from the official website."
                }
            },
            {
                "@type": "Question",
                "name": "Where can I download the notification?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Click Download Notification button available on this page."
                }
            }
        ]
    }

    return f"""

</div>

</main>
<!-- ================= SHARE ================= -->

<section class="share-section">

<h2>📤 Share This Update</h2>

<div class="share-buttons">

<a target="_blank"
rel="noopener"
href="https://wa.me/?text={canonical}">
WhatsApp
</a>

<a target="_blank"
rel="noopener"
href="https://t.me/share/url?url={canonical}">
Telegram
</a>

<a target="_blank"
rel="noopener"
href="https://twitter.com/intent/tweet?url={canonical}">
Twitter
</a>

<a target="_blank"
rel="noopener"
href="https://www.facebook.com/sharer/sharer.php?u={canonical}">
Facebook
</a>

</div>

</section>

<!-- ================= FAQ ================= -->

<section class="faq-section">

<h2>Frequently Asked Questions</h2>

<div class="faq-item">

<h3>What is {title}?</h3>

<p>
This page provides complete official information,
eligibility, vacancy, salary,
important dates and application process.
</p>

</div>

<div class="faq-item">

<h3>How can I apply?</h3>

<p>
Click the Apply Online button above
and complete your application from
the official website.
</p>

</div>

<div class="faq-item">

<h3>Where can I download the notification?</h3>

<p>
Use the Download Notification button
available above.
</p>

</div>

</section>

<!-- ================= RELATED POSTS ================= -->

<section class="related-posts">

<h2>🔥 Related Updates</h2>

<div class="related-grid">

<!-- AUTO_RELATED_POSTS_START -->

<!-- homepage.py inserts related posts automatically -->

<!-- AUTO_RELATED_POSTS_END -->

</div>

</section>

<!-- ================= ACTION BUTTONS ================= -->

<section class="next-action">

<a class="apply-btn"
href="{apply_link}"
target="_blank"
rel="noopener">

🚀 Apply Now

</a>

<a class="home-btn"
href="../../index.html">

🏠 Back to Home

</a>

</section>

<div id="footer"></div>

<script src="../../load.js"></script>
<script src="../../menu.js"></script>
<script src="../../script.js"></script>

<script type="application/ld+json">
{json.dumps(faq_schema, indent=2)}
</script>

</body>

</html>
"""
# ==========================================================
# Part 5 : Core HTML Generation Engine
# ==========================================================

def build_html(job):
    return (
        build_html_head(job)
        + build_html_body(job)
        + build_extra_sections(job)
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

INVALID_TITLES = {
    "",
    "support",
    "student",
    "results",
    "more",
    "more...",
    "support_agent support",
    "event student",
    "event key dates"
}


def generate_post(job):

    title = str(
        job.get("title", "")
    ).strip()

    category = str(
        job.get("category", "")
    ).strip()

    if (
        not title
        or len(title) < 5
        or title.lower() in INVALID_TITLES
        or category.lower() == "unknown"
    ):
        return None

    slug = generate_slug(title)

    filename = f"{slug}.html"

    html_content = build_html(job)

    filepath = write_html_file(
        filename,
        html_content
    )

    job["slug"] = slug
    job["html_file"] = f"generated/posts/{filename}"

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

        try:

            title = str(
                job.get("title", "")
            ).strip()

            slug = generate_slug(title)

            if (
                not title
                or slug in seen
            ):
                failed += 1
                continue

            seen.add(slug)

            filepath = generate_post(job)

            if filepath:
                generated.append(filepath)
            else:
                failed += 1

        except Exception:

            logger.exception(
                "Generation Failed : %s",
                job.get("title", "")
            )

            failed += 1

    logger.info("=" * 60)
    logger.info("Generated : %d", len(generated))
    logger.info("Failed    : %d", failed)
    logger.info("Total     : %d", len(jobs))
    logger.info("=" * 60)

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
# Verify Generated Files
# ==========================================================

def verify_generated_files():

    html_files = list(
        OUTPUT_DIR.glob("*.html")
    )

    logger.info(
        "Verified %d HTML Files",
        len(html_files)
    )

    return len(html_files)


# ==========================================================
# Clean Output Folder
# ==========================================================

def clean_output_directory():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    deleted = 0

    for file in OUTPUT_DIR.glob("*.html"):

        try:
            file.unlink()
            deleted += 1

        except Exception:

            logger.exception(
                "Unable to delete %s",
                file.name
            )

    logger.info(
        "Deleted %d HTML Files",
        deleted
    )


# ==========================================================
# Statistics
# ==========================================================

def html_statistics():

    total = len(
        list(
            OUTPUT_DIR.glob("*.html")
        )
    )

    logger.info("=" * 50)
    logger.info("HTML Generator V4.1")
    logger.info("=" * 50)
    logger.info("Generated HTML : %d", total)
    logger.info("Output Folder  : %s", OUTPUT_DIR)
    logger.info("=" * 50)


# ==========================================================
# Build Complete Website
# ==========================================================

def build_site(jobs):

    clean_output_directory()

    result = generate_all(jobs)

    verify_generated_files()

    homepage.run(jobs)

    category_generator.run(jobs)

    html_statistics()

    logger.info(
        "Website Generated Successfully."
    )

    return result


logger.info(
    "HTML Generator V4.1 Loaded Successfully."
)
