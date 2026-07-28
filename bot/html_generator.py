import re
import html
import logging
from pathlib import Path
from datetime import datetime

BASE_URL = "https://educationupdatehub.in"

logger = logging.getLogger("HTMLGenerator")


# ==========================================================
# SLUG GENERATOR
# ==========================================================

def generate_slug(title):

    if not title:
        return "post"

    title = str(title).strip().lower()

    slug = re.sub(r"\s+", "-", title)

    slug = re.sub(r"[^\w-]", "-", slug, flags=re.UNICODE)

    slug = re.sub(r"-{2,}", "-", slug)

    slug = slug.strip("-")

    if not slug:
        slug = "post"

    return slug


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

    return (
        escape_html(job.get("title", ""))
        + " Latest Government Job Update."
    )[:160]


# ==========================================================
# Canonical URL
# ==========================================================

def canonical_url(slug):

    return f"{BASE_URL}/{slug}.html"


# ==========================================================
# Publish Date
# ==========================================================

def published_date():

    return datetime.utcnow().strftime("%Y-%m-%d")
# ==========================================================
# Generate Single Post
# ==========================================================

def generate_post(job, base_url=BASE_URL):

    title = str(job.get("title", "")).strip()

    if not title:
        logger.warning("Skipped Empty Title")
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

    logger.info(
        "Generated : %s",
        filename
    )

    return filepath
    # ==========================================================
# Generate All Posts
# ==========================================================

BASE_URL = "https://educationupdatehub.in"

def generate_all(jobs, base_url=BASE_URL):

    generated = []
    seen = set()

    for job in jobs:

        title = str(job.get("title", "")).strip()

        if not title:
            continue

        slug = generate_slug(title)

        if slug == "post":
            slug = f"post-{abs(hash(title))}"

        if slug in seen:
            continue

        seen.add(slug)

        file = generate_post(
            job,
            base_url
        )

        if file is not None:
            generated.append(file)

    logger.info(
        "Generated %d HTML Files",
        len(generated)
    )

    return {
        "success": len(generated),
        "failed": 0,
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
