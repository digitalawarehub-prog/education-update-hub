import re
import os
import re
import html
import logging
from url_utils import slugify as canonical_slug

INDEX_FILE = "index.html"

LATEST_START = "<!-- AUTO_LATEST_GRID_START -->"
LATEST_END = "<!-- AUTO_LATEST_GRID_END -->"

POSTS_START = "<!-- AUTO_POSTS_START -->"
POSTS_END = "<!-- AUTO_POSTS_END -->"

UK_START = "<!-- AUTO_UK_JOBS_START -->"
UK_END = "<!-- AUTO_UK_JOBS_END -->"

CENTRAL_START = "<!-- AUTO_CENTRAL_JOBS_START -->"
CENTRAL_END = "<!-- AUTO_CENTRAL_JOBS_END -->"

STATE_START = "<!-- AUTO_STATE_JOBS_START -->"
STATE_END = "<!-- AUTO_STATE_JOBS_END -->"

MAX_POSTS = 30

logger = logging.getLogger("HomepageUpdater")

if not logger.handlers:

    handler = logging.StreamHandler()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    handler.setFormatter(formatter)

    logger.addHandler(handler)

logger.setLevel(logging.INFO)


def slugify(text, job=None):
    return canonical_slug(text, job)


def safe(job, key, default=""):

    value = job.get(key)

    if value is None:
        return default

    return html.escape(str(value).strip())


def create_latest_card(job):

    slug = slugify(
        safe(job, "title", "government-job")
    )

    title = safe(
        job,
        "title",
        "Government Recruitment"
    )

    date = safe(job, "date", safe(job, "publish_date", ""))
    m = re.search(r"(20\d{2})[-/](\d{1,2})[-/](\d{1,2})", date)
    if m:
        date = f"{int(m.group(3)):02d}-{int(m.group(2)):02d}-{int(m.group(1)):04d}"

    return f"""
<div class="latest-card">

<img
src="images/default-job.png"
alt="{title}">

<h3>

{title}

<span class="new-badge">
NEW
</span>

</h3>

<p>{date}</p>

<a href="generated/posts/{slug}.html">

Read More →

</a>

</div>
"""
def create_post_list(job):

    slug = slugify(
        safe(job, "title", "government-job")
    )

    title = safe(
        job,
        "title",
        "Government Recruitment"
    )

    category = safe(
        job,
        "category",
        "Latest Jobs"
    )

    date = safe(job, "date", safe(job, "publish_date", ""))
    m = re.search(r"(20\d{2})[-/](\d{1,2})[-/](\d{1,2})", date)
    if m:
        date = f"{int(m.group(3)):02d}-{int(m.group(2)):02d}-{int(m.group(1)):04d}"

    return f"""
<li>

<a href="generated/posts/{slug}.html">

<strong>{title}</strong>

<br>

<small>{category}</small>

{'<br><small>📅 ' + date + '</small>' if date else ''}

</a>

</li>
"""


def create_job_card(job):

    slug = slugify(
        safe(job, "title", "government-job")
    )

    title = safe(
        job,
        "title",
        "Government Recruitment"
    )

    return f"""
<li>

<a href="generated/posts/{slug}.html">

{title}

</a>

</li>
"""


def create_uk_job(job):

    return create_job_card(job)


def create_central_job(job):

    return create_job_card(job)


def create_state_job(job):

    return create_job_card(job)
# =====================================================
# Replace Any AUTO Section
# =====================================================

def replace_section(
    html_content,
    start_marker,
    end_marker,
    items
):

    start = html_content.find(start_marker)
    end = html_content.find(end_marker)

    if start == -1 or end == -1:

        logger.warning(
            "Marker not found : %s",
            start_marker
        )

        return html_content

    return (

        html_content[
            :start + len(start_marker)
        ]

        + "\n"

        + "\n".join(items)

        + "\n"

        + html_content[end:]

    )


# =====================================================
# Remove Duplicate Posts
# =====================================================

def remove_duplicates(posts):

    seen = set()

    final = []

    for post in posts:

        match = re.search(

            r'generated/posts/(.*?)\.html',

            post

        )

        slug = (

            match.group(1)

            if match

            else post

        )

        if slug not in seen:

            seen.add(slug)

            final.append(post)

    return final


# =====================================================
# Sort Jobs
# =====================================================

def sort_jobs(jobs):

    def key(x):
        return str(x.get("publish_date") or x.get("date") or "")

    return sorted(jobs, key=key, reverse=True)
# =====================================================
# Homepage Updater
# =====================================================

def update_homepage(jobs):

    if not jobs:

        logger.info(
            "No new jobs found."
        )

        return False

    if not os.path.exists(INDEX_FILE):

        logger.error(
            "index.html not found."
        )

        return False

    with open(
        INDEX_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        html_content = f.read()

    jobs = sort_jobs(jobs)

    latest_cards = []

    latest_posts = []

    uk_jobs = []

    central_jobs = []

    state_jobs = []

    for job in jobs[:MAX_POSTS]:

        latest_cards.append(
            create_latest_card(job)
        )

        latest_posts.append(
            create_post_list(job)
        )

        category = str(
            job.get(
                "category",
                ""
            )
        ).lower()

        if "uttarakhand" in category:

            uk_jobs.append(
                create_uk_job(job)
            )

        elif (
            "central" in category
            or
            "upsc" in category
            or
            "ssc" in category
            or
            "railway" in category
            or
            "bank" in category
        ):

            central_jobs.append(
                create_central_job(job)
            )

        else:

            state_jobs.append(
                create_state_job(job)
            )

    latest_cards = remove_duplicates(
        latest_cards
    )[:10]

    latest_posts = remove_duplicates(
        latest_posts
    )[:30]

    uk_jobs = remove_duplicates(
        uk_jobs
    )[:10]

    central_jobs = remove_duplicates(
        central_jobs
    )[:10]

    state_jobs = remove_duplicates(
        state_jobs
    )[:10]

    html_content = replace_section(

        html_content,

        LATEST_START,

        LATEST_END,

        latest_cards

    )

    html_content = replace_section(

        html_content,

        POSTS_START,

        POSTS_END,

        latest_posts

    )

    html_content = replace_section(

        html_content,

        UK_START,

        UK_END,

        uk_jobs

    )

    html_content = replace_section(

        html_content,

        CENTRAL_START,

        CENTRAL_END,

        central_jobs

    )

    html_content = replace_section(

        html_content,

        STATE_START,

        STATE_END,

        state_jobs

    )
    with open(
        INDEX_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(html_content)

    logger.info(
        "Homepage updated successfully."
    )

    return True


# =====================================================
# Homepage Validator
# =====================================================

def validate_homepage():

    if not os.path.exists(INDEX_FILE):

        logger.error(
            "index.html not found."
        )

        return False

    with open(
        INDEX_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        html_content = f.read()

    required_markers = [

        LATEST_START,
        LATEST_END,

        POSTS_START,
        POSTS_END,

        UK_START,
        UK_END,

        CENTRAL_START,
        CENTRAL_END,

        STATE_START,
        STATE_END

    ]

    for marker in required_markers:

        if marker not in html_content:

            logger.error(
                "Missing marker: %s",
                marker
            )

            return False

    logger.info(
        "Homepage validation successful."
    )

    return True


# =====================================================
# Production Runner
# =====================================================

def run_homepage_update(jobs):

    jobs = sort_jobs(jobs)

    if not validate_homepage():

        return False

    return update_homepage(jobs)


# =====================================================
# Standalone Testing
# =====================================================

if __name__ == "__main__":

    sample_jobs = [

        {

            "title":
            "SSC CGL Recruitment 2026",

            "date":
            "28 July 2026",

            "category":
            "Central"

        },

        {

            "title":
            "UKPSC Recruitment 2026",

            "date":
            "27 July 2026",

            "category":
            "Uttarakhand"

        }

    ]

    if run_homepage_update(sample_jobs):

        logger.info(
            "Homepage updater completed successfully."
        )

    else:

        logger.error(
            "Homepage updater failed."
        )
