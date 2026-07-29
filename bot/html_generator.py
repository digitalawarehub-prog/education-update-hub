# ==========================================================
# HTML Generator Utilities
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

# ==========================================================
# Create SEO Slug
# ==========================================================

def generate_slug(title):

    if not title:
        return "post"

    title = str(title).strip().lower()

    slug = re.sub(r"[^a-z0-9]+", "-", title)

    slug = re.sub(r"-+", "-", slug).strip("-")

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
        f"Latest {category} recruitment from "
        f"{department}. "
        f"Check eligibility, salary, last date "
        f"and apply online."
    )

    return description[:160]


# ==========================================================
# Canonical URL
# ==========================================================

def canonical_url(base_url, slug):

    return (
        f"{base_url.rstrip('/')}/{slug}.html"
    )


# ==========================================================
# Publish Date
# ==========================================================

def published_date():

    return datetime.utcnow().strftime(
        "%d %B %Y"
    )


logger.info(
    "HTML Utilities Loaded"
)
# ==========================================================
# HTML Head Template
# ==========================================================

def build_html_head(job, base_url=BASE_URL):

    title = escape_html(
        job.get("title", "Latest Job")
    )

    slug = generate_slug(title)

    canonical = canonical_url(
        base_url,
        slug
    )

    description = generate_meta_description(
        job
    )

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
content="{title}, Latest Jobs, Government Jobs, Education Update Hub">

<meta name="robots"
content="index,follow">

<meta name="author"
content="Education Update Hub">

<link rel="canonical"
href="{canonical}">

<meta property="og:type"
content="article">

<meta property="og:title"
content="{title}">

<meta property="og:description"
content="{description}">

<meta property="og:url"
content="{canonical}">

<meta property="og:site_name"
content="Education Update Hub">

<meta name="twitter:card"
content="summary_large_image">

<meta name="twitter:title"
content="{title}">

<meta name="twitter:description"
content="{description}">

<script type="application/ld+json">
{{
"@context":"https://schema.org",
"@type":"NewsArticle",
"headline":"{title}",
"datePublished":"{publish_date}",
"dateModified":"{publish_date}",
"mainEntityOfPage":"{canonical}",
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

    title = escape_html(
        job.get("title", "")
    )

    category = escape_html(
        job.get("category", "Latest Jobs")
    )

    department = escape_html(
        job.get("department", "Not Mentioned")
    )

    vacancy = escape_html(
        job.get("vacancy", "Not Mentioned")
    )

    last_date = escape_html(
        job.get("last_date", "Not Available")
    )

    salary = escape_html(
        job.get("salary", "Not Mentioned")
    )

    qualification = escape_html(
        job.get(
            "qualification",
            "Check Official Notification"
        )
    )

    location = escape_html(
        job.get("location", "India")
    )

    apply_link = escape_html(
        job.get(
            "apply_link",
            job.get("url", "#")
        )
    )

    pdf = escape_html(
        job.get(
            "notification_pdf",
            "#"
        )
    )

    return f"""
<body>

<div class="container">

<header>

<h1>{title}</h1>

<p>

<strong>Category:</strong> {category}<br>

<strong>Department:</strong> {department}

</p>

</header>

<hr>

<h2>Recruitment Details</h2>

<table border="1" cellpadding="8" cellspacing="0">

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
<th>Job Location</th>
<td>{location}</td>
</tr>

<tr>
<th>Last Date</th>
<td>{last_date}</td>
</tr>

</table>

<br>

<p>

<a href="{apply_link}"
target="_blank"
rel="noopener">

Apply Online

</a>

</p>

<p>

<a href="{pdf}"
target="_blank"
rel="noopener">

Download Official Notification

</a>

</p>

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
# Complete HTML Builder
# ==========================================================

def build_html(job, base_url=BASE_URL):

    html_page = []

    html_page.append(

        build_html_head(
            job,
            base_url
        )

    )

    html_page.append(

        build_html_body(job)

    )

    return "".join(html_page)


logger.info(
    "Production HTML Template Ready"
)
# ==========================================================
# Output Directory
# ==========================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

OUTPUT_DIR = ROOT_DIR / "generated" / "posts"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

logger.info(
    "Output Directory : %s",
    OUTPUT_DIR
)


# ==========================================================
# Write HTML File
# ==========================================================

def write_html_file(filename, html_content):

    filename = str(filename).strip()

    if not filename.endswith(".html"):
        filename += ".html"

    filepath = OUTPUT_DIR / filename

    filepath.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        filepath,
        "w",
        encoding="utf-8",
        newline="\n"
    ) as f:

        f.write(html_content)

    logger.info(
        "Saved HTML : %s",
        filepath.name
    )

    return filepath
    # ==========================================================
# Generate Single Post
# ==========================================================

def generate_post(job, base_url=BASE_URL):

    title = str(
        job.get("title", "")
    ).strip()

    if not title:

        logger.warning(
            "Skipped Empty Title"
        )

        return None

    slug = generate_slug(title)

    if slug == "post":
        slug = f"post-{abs(hash(title))}"

    filename = f"{slug}.html"

    html_content = build_html(
        job,
        base_url
    )

    filepath = write_html_file(
        filename,
        html_content
    )

    job["html_file"] = f"generated/posts/{filename}"

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

            logger.warning(
                "Skipped Empty Title"
            )

            failed += 1

            continue

        slug = generate_slug(title)

        if slug == "post":

            slug = f"post-{abs(hash(title))}"

        if slug in seen:

            logger.info(
                "Duplicate Skipped : %s",
                title
            )

            continue

        seen.add(slug)

        try:

            filepath = generate_post(
                job,
                base_url
            )

            if filepath:

                generated.append(
                    filepath
                )

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
# HTML Statistics
# ==========================================================

def html_statistics(files):

    total_files = len(files)

    total_size = 0

    for file in files:

        try:

            total_size += Path(file).stat().st_size

        except Exception:

            pass

    return {

        "total_files": total_files,

        "total_size": total_size,

        "output_directory": str(OUTPUT_DIR)

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

    return True


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

        "Deleted %d old HTML files",

        deleted

    )


# ==========================================================
# Module Ready
# ==========================================================

logger.info(
    "HTML Generation Engine Ready"
)
