"""
Category Page Generator

Responsibilities:
- Load jobs
- Filter by category
- Generate category HTML
- Replace markers in category pages
- Update all category pages
"""
import logging
from pathlib import Path

logger = logging.getLogger("CategoryGenerator")

ROOT_DIR = Path(__file__).resolve().parent.parent

CATEGORY_PAGES = {
    "Latest Jobs": ROOT_DIR / "latest-jobs.html",
    "Results": ROOT_DIR / "result.html",
    "Admit Card": ROOT_DIR / "admit-card.html",
    "Answer Key": ROOT_DIR / "answer-key.html",
    "Scholarship": ROOT_DIR / "scholarship.html",
    "Syllabus": ROOT_DIR / "syllabus.html",
    "Government Schemes": ROOT_DIR / "government-schemes.html",
    "Uttarakhand Jobs": ROOT_DIR / "uttarakhand-jobs.html",
    "Central Government Jobs": ROOT_DIR / "central-government-jobs.html",
    "Other State Jobs": ROOT_DIR / "other-state-jobs.html",
}
from pathlib import Path

CATEGORY_PAGES = {
    "Latest Jobs": "latest-jobs.html",
    "Results": "result.html",
    "Admit Card": "admit-card.html",
    "Answer Key": "answer-key.html",
    "Scholarship": "scholarship.html",
    "Syllabus": "syllabus.html",
    "Government Schemes": "government-schemes.html",
    "Uttarakhand Jobs": "uttarakhand-jobs.html",
    "Central Government Jobs": "central-government-jobs.html",
    "Other State Jobs": "other-state-jobs.html",
}
# =====================================================
# FILE HELPERS
# =====================================================

def read_text(path):

    try:
        return path.read_text(
            encoding="utf-8"
        )

    except Exception as e:

        logger.exception(e)

        return ""


def write_text(path, text):

    try:

        path.write_text(
            text,
            encoding="utf-8"
        )

        return True

    except Exception as e:

        logger.exception(e)

        return False


# =====================================================
# MARKER REPLACER
# =====================================================

def replace_between_markers(

    html,

    start_marker,

    end_marker,

    new_content

):

    start = html.find(start_marker)

    end = html.find(end_marker)

    if start == -1 or end == -1:

        logger.warning(
            "Marker Not Found"
        )

        return html

    start += len(start_marker)

    return (

        html[:start]

        + "\n"

        + new_content

        + "\n"

        + html[end:]

    )
# =====================================================
# CATEGORY FILTER
# =====================================================

CATEGORY_LIMIT = 30


def filter_jobs_by_category(
    jobs,
    category,
    limit=CATEGORY_LIMIT
):

    filtered = []

    seen = set()

    for job in jobs:

        job_category = str(
            job.get("category", "")
        ).strip()

        if job_category != category:
            continue

        title = str(
            job.get("title", "")
        ).strip()

        if not title:
            continue

        if title.lower() in seen:
            continue

        seen.add(title.lower())

        filtered.append(job)

        if len(filtered) >= limit:
            break

    logger.info(
        "%s : %d Posts",
        category,
        len(filtered)
    )

    return filtered
  # =====================================================
# CATEGORY CARD HTML
# =====================================================

def generate_category_cards(jobs):

    html = []

    for job in jobs:

        title = str(
            job.get("title", "Latest Update")
        ).strip()

        url = job.get("html_file") or job.get("url", "#")

        image = (
            job.get("featured_image")
            or job.get("thumbnail")
            or job.get("image")
            or "images/default-job.png"
        )

        category = job.get(
            "category",
            "Latest Jobs"
        )

        html.append(f"""
<div class="post-card">

    <img src="{image}"
         alt="{title}"
         loading="lazy">

    <div class="post-content">

        <span class="post-category">
            {category}
        </span>

        <h3>
            <a href="{url}">
                {title}
            </a>
        </h3>

        <a class="read-more-btn"
           href="{url}">
           Read More →
        </a>

    </div>

</div>
""")

    return "\n".join(html)
  
