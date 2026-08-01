# ==========================================================
# HTML Generator Utilities
# Version 3.0
# Part 1
# ==========================================================

import os
import re
import html
import json
import logging

from pathlib import Path
from datetime import datetime

logger = logging.getLogger("HTMLGenerator")

BASE_URL = "https://educationupdatehub.in"

ROOT_DIR = Path(__file__).resolve().parent.parent

OUTPUT_DIR = ROOT_DIR / "generated" / "posts"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

DEFAULT_IMAGE = "images/default-job.png"

# ==========================================================
# Create SEO Slug
# ==========================================================

def generate_slug(title):

    if not title:
        return "post"

    title = str(title).strip().lower()

    title = re.sub(
        r"\{\{.*?\}\}",
        "",
        title
    )

    slug = re.sub(
        r"[^a-z0-9]+",
        "-",
        title
    )

    slug = re.sub(
        r"-+",
        "-",
        slug
    ).strip("-")

    if slug:
        return slug

    return f"post-{abs(hash(title))}"


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


# ==========================================================
# Meta Description
# ==========================================================

def generate_meta_description(job):

    title = escape_html(
        job.get("title", "")
    )

    category = escape_html(
        job.get("category", "Latest Jobs")
    )

    department = escape_html(
        job.get("department", "")
    )

    description = (
        f"{title}. "
        f"Latest {category} update from "
        f"{department}. "
        f"Check eligibility, important dates, "
        f"official notification and apply online."
    )

    return description[:160]


# ==========================================================
# Canonical URL
# ==========================================================

def canonical_url(
    base_url,
    slug
):

    return (
        f"{base_url.rstrip('/')}/generated/posts/{slug}.html"
    )


# ==========================================================
# Publish Date
# ==========================================================

def published_date():

    return datetime.utcnow().strftime(
        "%d %B %Y"
    )


logger.info(
    "HTML Generator Part 1 Loaded"
)
# ==========================================================
# HTML Head Template
# ==========================================================

def build_html_head(job, base_url=BASE_URL):

    title = escape_html(
        job.get("title", "Latest Update")
    )

    slug = generate_slug(title)

    canonical = canonical_url(
        base_url,
        slug
    )

    description = generate_meta_description(
        job
    )

    image = get_image(job)

    publish_date = published_date()

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
content="{title}, Government Jobs, Results, Admit Card, Answer Key, Scholarship, Education Update Hub">

<meta name="robots"
content="index,follow">

<meta name="author"
content="Education Update Hub">

<link rel="canonical"
href="{canonical}">

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

<!-- Twitter -->

<meta name="twitter:card"
content="summary_large_image">

<meta name="twitter:title"
content="{title}">

<meta name="twitter:description"
content="{description}">

<meta name="twitter:image"
content="{image}">

<!-- Schema -->

<script type="application/ld+json">
{{
"@context":"https://schema.org",
"@type":"NewsArticle",
"headline":"{title}",
"datePublished":"{publish_date}",
"dateModified":"{publish_date}",
"mainEntityOfPage":"{canonical}",
"image":"{image}",
"publisher":{{
"@type":"Organization",
"name":"Education Update Hub",
"url":"{base_url}"
}}
}}
</script>

</head>
"""
# ==========================================================
# HTML Body Template
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

    content = escape_html(
        job.get("content", "")
    )

    image = get_image(job)

    apply_link = job.get("apply_link") or job.get("url") or "#"

    notification_pdf = (
        job.get("notification_pdf")
        or job.get("url")
        or "#"
    )

    official = (
        job.get("official_website")
        or job.get("url")
        or "#"
    )

    return f"""
<body>

<div class="container">

<h1>{title}</h1>

<img src="{image}"
alt="{title}"
style="width:100%;max-width:900px;border-radius:8px;margin:20px 0;">

<p>{description}</p>

<div class="article-content">

{content.replace(chr(10), "<br>")}

</div>

<h2>Recruitment Details</h2>

<table border="1" cellpadding="8" cellspacing="0" width="100%">

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

<br>

<div style="display:flex;gap:10px;flex-wrap:wrap;">

<a href="{apply_link}"
target="_blank"
style="padding:12px 18px;background:#0b7a24;color:#fff;text-decoration:none;border-radius:6px;">

Apply Online

</a>

<a href="{notification_pdf}"
target="_blank"
style="padding:12px 18px;background:#d32f2f;color:#fff;text-decoration:none;border-radius:6px;">

Download Notification

</a>

<a href="{official}"
target="_blank"
style="padding:12px 18px;background:#1565c0;color:#fff;text-decoration:none;border-radius:6px;">

Official Website

</a>

</div>

<hr>

<p>

<a href="{BASE_URL}">

← Back to Homepage

</a>

</p>

</div>

</body>

</html>
"""
# ==========================================================
# Generate Single Post
# ==========================================================

def generate_post(job, base_url=BASE_URL):

    title = self_title = str(
        job.get("title", "")
    ).strip()

    url = str(
        job.get("url", "")
    ).strip()

    if not title:
        logger.warning("Skipped Empty Title")
        return None

    title_lower = title.lower()

    # Skip template posts
    if (
        "{{" in title
        or "}}" in title
        or "translate" in title_lower
    ):
        return None

    # Skip unwanted pages
    if any(x in title_lower for x in [
        "gallery",
        "photo",
        "video",
        "chairman",
        "member",
        "contact",
        "privacy",
        "policy",
        "feedback",
        "help",
        "login",
        "notification board",
        "notifications notices",
        "work recruitments",
        "watch this video"
    ]):
        return None

    slug = generate_slug(title)

    filename = f"{slug}.html"

    html_content = build_html(
        job,
        base_url
    )

    filepath = write_html_file(
        filename,
        html_content
    )

    # Save generated path
    job["html_file"] = (
        f"generated/posts/{filename}"
    )

    logger.info(
        "Generated HTML : %s",
        filename
    )

    return filepath
# ==========================================================
# Generate Single Post
# ==========================================================

def generate_post(job, base_url=BASE_URL):

    title = self_title = str(
        job.get("title", "")
    ).strip()

    url = str(
        job.get("url", "")
    ).strip()

    if not title:
        logger.warning("Skipped Empty Title")
        return None

    title_lower = title.lower()

    # Skip template posts
    if (
        "{{" in title
        or "}}" in title
        or "translate" in title_lower
    ):
        return None

    # Skip unwanted pages
    if any(x in title_lower for x in [
        "gallery",
        "photo",
        "video",
        "chairman",
        "member",
        "contact",
        "privacy",
        "policy",
        "feedback",
        "help",
        "login",
        "notification board",
        "notifications notices",
        "work recruitments",
        "watch this video"
    ]):
        return None

    slug = generate_slug(title)

    filename = f"{slug}.html"

    html_content = build_html(
        job,
        base_url
    )

    filepath = write_html_file(
        filename,
        html_content
    )

    # Save generated path
    job["html_file"] = (
        f"generated/posts/{filename}"
    )

    logger.info(
        "Generated HTML : %s",
        filename
    )

    return filepath
# ==========================================================
# Generate All Posts
# ==========================================================

def generate_all(jobs, base_url=BASE_URL):

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

        title_lower = title.lower()

        # Skip template posts
        if (
            "{{" in title
            or "}}" in title
            or "translate" in title_lower
        ):
            continue

        # Skip junk pages
        if any(x in title_lower for x in [
            "gallery",
            "photo",
            "video",
            "chairman",
            "member",
            "contact",
            "privacy",
            "policy",
            "feedback",
            "help",
            "login",
            "notification board",
            "notifications notices",
            "work recruitments",
            "watch this video"
        ]):
            continue

        slug = generate_slug(title)

        if slug in seen:
            continue

        seen.add(slug)

        try:

            filepath = generate_post(
                job,
                base_url
            )

            if filepath:
                generated.append(filepath)
            else:
                failed += 1

        except Exception as e:

            logger.exception(
                "Failed : %s",
                title
            )

            failed += 1

    logger.info(
        "Generated %d HTML Files",
        len(generated)
    )

    return {
        "success": len(generated),
        "failed": failed,
        "total": len(jobs),
        "results": [
            {
                "success": True,
                "file": str(file),
                "title": Path(file).stem
            }
            for file in generated
        ]
    }


# ==========================================================
# Verify Generated Files
# ==========================================================

def verify_generated_files():

    if not OUTPUT_DIR.exists():
        return False

    html_files = list(
        OUTPUT_DIR.glob("*.html")
    )

    logger.info(
        "Verified %d HTML Files",
        len(html_files)
    )

    return len(html_files) > 0


# ==========================================================
# Clean Output Directory
# ==========================================================

def clean_output_directory():

    if not OUTPUT_DIR.exists():
        return

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
# HTML Statistics
# ==========================================================

def html_statistics():

    html_files = list(
        OUTPUT_DIR.glob("*.html")
    )

    logger.info("=" * 50)
    logger.info("HTML Statistics")
    logger.info("Total HTML Files : %d", len(html_files))
    logger.info("Output Directory : %s", OUTPUT_DIR)
    logger.info("=" * 50)


logger.info(
    "HTML Generation Engine v3 Loaded Successfully"
)
