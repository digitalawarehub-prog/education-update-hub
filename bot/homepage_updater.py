import os
import re
import html
import logging

INDEX_FILE = "index.html"

START_MARKER = "<!-- AUTO_POSTS_START -->"
END_MARKER = "<!-- AUTO_POSTS_END -->"

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


def slugify(text):

    if not text:
        return "post"

    text = str(text).strip().lower()

    slug = re.sub(r"\s+", "-", text)

    slug = re.sub(
        r"[^\w\-]",
        "-",
        slug,
        flags=re.UNICODE
    )

    slug = re.sub(r"-+", "-", slug)

    slug = slug.strip("-")

    if not slug:
        slug = f"post-{abs(hash(text))}"

    if len(slug) > 80:
        slug = slug[:80].rstrip("-")

    return slug


def safe(job, key, default=""):

    value = job.get(key)

    if value is None:

        return default

    return html.escape(str(value).strip())


def create_post(job):

    slug = slugify(
        safe(job, "title", "government-job")
    )

    title = safe(
        job,
        "title",
        "Government Recruitment"
    )

    date = safe(
        job,
        "date",
        ""
    )

    category = safe(
        job,
        "category",
        "Latest Jobs"
    )

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
# =====================================================
# Homepage Updater
# =====================================================

def update_homepage(jobs):

    if not jobs:

        logger.info("No new jobs. Homepage skipped.")

        return False

    if not os.path.exists(INDEX_FILE):

        logger.error("index.html not found.")

        return False

    try:

        with open(
            INDEX_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            html_content = f.read()

        start = html_content.find(START_MARKER)

        end = html_content.find(END_MARKER)

        if start == -1 or end == -1:

            logger.error(
                "AUTO markers not found."
            )

            return False

        old_section = html_content[
            start + len(START_MARKER):end
        ]

        old_posts = re.findall(

            r"<li>.*?</li>",

            old_section,

            flags=re.DOTALL

        )

        new_posts = []

        for job in jobs:

            try:

                new_posts.append(
                    create_post(job)
                )

            except Exception:

                logger.exception(
                    "Unable to create homepage card."
                )

        merged = new_posts + old_posts

        seen = set()

        final_posts = []

        for post in merged:

            match = re.search(

                r'generated/(.*?)\.html',

                post

            )

            slug = match.group(1) if match else post

            if slug not in seen:

                seen.add(slug)

                final_posts.append(post)

        final_posts = final_posts[:MAX_POSTS]

        updated_html = (

            html_content[
                :start + len(START_MARKER)
            ]

            + "\n"

            + "\n".join(final_posts)

            + "\n"

            + html_content[end:]

        )

        with open(

            INDEX_FILE,

            "w",

            encoding="utf-8"

        ) as f:

            f.write(updated_html)

        logger.info(

            "Homepage updated successfully (%d posts)",

            len(final_posts)

        )

        return True

    except Exception:

        logger.exception(

            "Homepage update failed."

        )

        return False
        # =====================================================
# Homepage Validator
# =====================================================

def validate_homepage():

    if not os.path.exists(INDEX_FILE):

        logger.error("Homepage file not found.")

        return False

    with open(
        INDEX_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        html_content = f.read()

    if START_MARKER not in html_content:

        logger.error(
            "START marker missing."
        )

        return False

    if END_MARKER not in html_content:

        logger.error(
            "END marker missing."
        )

        return False

    logger.info(
        "Homepage validation successful."
    )

    return True


# =====================================================
# Sort Jobs
# =====================================================

def sort_jobs(jobs):

    def sort_key(job):

        return job.get(
            "date",
            ""
        )

    return sorted(

        jobs,

        key=sort_key,

        reverse=True

    )


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
            "2026-07-24",

            "category":
            "Latest Jobs"

        },

        {

            "title":
            "IBPS PO Recruitment 2026",

            "date":
            "2026-07-23",

            "category":
            "Bank Jobs"

        }

    ]

    success = run_homepage_update(
        sample_jobs
    )

    if success:

        logger.info(
            "Homepage updater completed successfully."
        )

    else:

        logger.error(
            "Homepage updater failed."
        )
    
