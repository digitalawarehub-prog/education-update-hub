# ==========================================================
# HTML Generator Utilities
# ==========================================================

import re
import html
from datetime import datetime


# ==========================================================
# Create SEO Slug
# ==========================================================

def generate_slug(title):

    if not title:
        return "post"

    slug = title.lower().strip()

    slug = re.sub(r"[^a-z0-9]+", "-", slug)

    slug = re.sub(r"-+", "-", slug)

    return slug.strip("-")


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

    title = escape_html(job.get("title", ""))

    category = escape_html(job.get("category", ""))

    department = escape_html(job.get("department", ""))

    description = (
        f"{title}. "
        f"Latest {category} recruitment from "
        f"{department}. "
        f"Check eligibility, last date, salary "
        f"and apply online."
    )

    return description[:160]


# ==========================================================
# Canonical URL
# ==========================================================

def canonical_url(base_url, slug):

    return f"{base_url.rstrip('/')}/{slug}.html"


# ==========================================================
# Publish Date
# ==========================================================

def published_date():

    return datetime.utcnow().strftime(
        "%Y-%m-%d"
    )


logger.info(
    "HTML Utilities Loaded"
)
# ==========================================================
# HTML Head Template
# ==========================================================

def build_html_head(job, base_url):

    title = escape_html(job.get("title", ""))

    slug = generate_slug(title)

    canonical = canonical_url(base_url, slug)

    description = generate_meta_description(job)

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

<meta name="robots"
content="index,follow">

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
"name":"Education Update Hub"
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

    category = escape_html(job.get("category", ""))

    department = escape_html(job.get("department", ""))

    vacancy = escape_html(job.get("vacancy", "Not Mentioned"))

    last_date = escape_html(job.get("last_date", "Not Available"))

    salary = escape_html(job.get("salary", "Not Mentioned"))

    qualification = escape_html(
        job.get("qualification", "Check Notification")
    )

    apply_link = escape_html(job.get("apply_link", ""))

    pdf = escape_html(job.get("notification_pdf", ""))

    return f"""
<body>

<header>

<h1>{title}</h1>

<p>

Category : {category}<br>

Department : {department}

</p>

</header>

<hr>

<h2>Recruitment Details</h2>

<ul>

<li><strong>Vacancy :</strong> {vacancy}</li>

<li><strong>Last Date :</strong> {last_date}</li>

<li><strong>Salary :</strong> {salary}</li>

<li><strong>Qualification :</strong> {qualification}</li>

</ul>

<p>

<a href="{apply_link}" target="_blank">

Apply Online

</a>

</p>

<p>

<a href="{pdf}" target="_blank">

Download Notification

</a>

</p>

</body>

</html>
"""
# ==========================================================
# Complete HTML Builder
# ==========================================================

def build_html(job, base_url):

    return (

        build_html_head(

            job,

            base_url

        )

        +

        build_html_body(job)

    )


logger.info(
    "Production HTML Template Ready"
)
