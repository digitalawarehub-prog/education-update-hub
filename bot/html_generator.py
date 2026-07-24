# =====================================================
# html_generator.py
# Part 1 - Imports, Config & Utility Functions
# =====================================================

import os
import re
import logging
from datetime import datetime

from seo_generator import generate_seo

# =====================================================
# Configuration
# =====================================================

OUTPUT_FOLDER = "generated"

SITE_NAME = "Education Update Hub"

SITE_URL = "https://educationupdatehub.in"

DEFAULT_IMAGE = "../images/default-job.png"

WHATSAPP_CHANNEL = "https://whatsapp.com/channel/YOUR_CHANNEL_LINK"

TELEGRAM_CHANNEL = "https://t.me/YOUR_TELEGRAM_LINK"

# =====================================================
# Logging
# =====================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

# =====================================================
# Utility Functions
# =====================================================

def slugify(text):

    if not text:
        return "government-job"

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9]+",
        "-",
        text
    )

    return text.strip("-")


def safe(job, key, default="N/A"):

    value = job.get(key)

    if value is None:
        return default

    value = str(value).strip()

    if value == "":
        return default

    return value


def get_post_url(job):

    url = job.get("post_url")

    if url:
        return url

    slug = slugify(
        safe(job, "title", "job")
    )

    return f"{SITE_URL}/generated/{slug}.html"


def get_image(job):

    image = job.get("image")

    if image:
        return image

    return DEFAULT_IMAGE


def get_today():

    return datetime.now().strftime(
        "%d %B %Y"
    )


def create_breadcrumb(job):

    category = safe(
        job,
        "category",
        "Latest Jobs"
    )

    return f"""
<a href="../index.html">Home</a>

>

<a href="../teacher-recruitment.html">
{category}
</a>

>

<span>{safe(job,"title")}</span>
"""


def default_summary(job):

    return (
        f"{safe(job,'title')} recruitment notification "
        f"has been released. Check vacancy, eligibility, "
        f"important dates, selection process, salary "
        f"and apply online details."
    )


def ensure_defaults(job):

    defaults = {

        "summary": default_summary(job),

        "date": get_today(),

        "source": SITE_NAME,

        "notification_date": "Available Soon",

        "start_date": "Check Notification",

        "last_date": "Check Notification",

        "exam_date": "To Be Announced",

        "post_name": safe(job, "title"),

        "vacancy": "As Per Notification",

        "qualification": "Refer Notification",

        "salary": "As Per Rules",

        "gen_fee": "Refer Notification",

        "sc_fee": "Refer Notification",

        "min_age": "18 Years",

        "max_age": "As Per Rules",

        "step1": "Visit the official website.",

        "step2": "Read the notification carefully.",

        "step3": "Fill the online application form.",

        "step4": "Submit the form before the last date.",

        "apply_link": "#",

        "notification_link": "#",

        "official_website": "#",

        "faq1_q": "What is the last date to apply?",

        "faq1_a": "Please check the official notification.",

        "faq2_q": "What is the qualification?",

        "faq2_a": "Refer to the official notification.",

        "faq3_q": "Where can I apply?",

        "faq3_a": "Use the Apply Online link given above."

    }

    for key, value in defaults.items():

        if not job.get(key):

            job[key] = value

    job["post_url"] = get_post_url(job)

    job["image"] = get_image(job)

    return job
    # =====================================================
# Part 2 - Professional HTML Template (Start)
# =====================================================

BODY_TEMPLATE = """<!DOCTYPE html>
<html lang="en">

<head>

{{SEO}}

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<meta name="robots"
content="index, follow">

<link rel="canonical"
href="{{POST_URL}}">

<link rel="stylesheet"
href="../style.css">

<link rel="preconnect"
href="https://fonts.googleapis.com">

<link rel="preconnect"
href="https://fonts.gstatic.com"
crossorigin>

<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap"
rel="stylesheet">

</head>

<body>

<header class="top-header">

<div class="container">

<a href="../index.html" class="logo">

<h1>Education Update Hub</h1>

</a>

</div>

</header>

<div class="container">

<nav class="breadcrumb">

{{BREADCRUMB}}

</nav>

<article class="job-post">

<h1 class="post-title">

{{TITLE}}

</h1>

<div class="post-meta">

<span>📅 Published :
{{DATE}}</span>

<span>|</span>

<span>🏢 Source :
{{SOURCE}}</span>

</div>

<img
src="{{IMAGE}}"
alt="{{TITLE}}"
class="featured-image"
loading="lazy">

<div class="content">

<p class="summary">

{{SUMMARY}}

</p>

<hr>

<h2>📅 Important Dates</h2>

<table class="job-table">

<tr>

<th>Notification Date</th>

<td>{{NOTIFICATION_DATE}}</td>

</tr>

<tr>

<th>Application Start</th>

<td>{{START_DATE}}</td>

</tr>

<tr>

<th>Last Date</th>

<td>{{LAST_DATE}}</td>

</tr>

<tr>

<th>Exam Date</th>

<td>{{EXAM_DATE}}</td>

</tr>

</table>

<hr>

<h2>📋 Vacancy Details</h2>

<table class="job-table">

<tr>

<th>Post Name</th>

<td>{{POST_NAME}}</td>

</tr>

<tr>

<th>Total Vacancy</th>

<td>{{VACANCY}}</td>

</tr>

<tr>

<th>Qualification</th>

<td>{{QUALIFICATION}}</td>

</tr>

<tr>

<th>Salary</th>

<td>{{SALARY}}</td>

</tr>

</table>

<hr>

<h2>💳 Application Fee</h2>

<table class="job-table">

<tr>

<th>General / OBC</th>

<td>{{GEN_FEE}}</td>

</tr>

<tr>

<th>SC / ST</th>

<td>{{SC_FEE}}</td>

</tr>

</table>

<hr>

<h2>🎂 Age Limit</h2>

<table class="job-table">

<tr>

<th>Minimum Age</th>

<td>{{MIN_AGE}}</td>

</tr>

<tr>

<th>Maximum Age</th>

<td>{{MAX_AGE}}</td>

</tr>

</table>

<hr>
<h2>📝 How to Apply</h2>

<ol class="apply-steps">

<li>{{STEP1}}</li>

<li>{{STEP2}}</li>

<li>{{STEP3}}</li>

<li>{{STEP4}}</li>

</ol>

<hr>

<h2>🔗 Important Links</h2>

<div class="important-links">

<p>

<a
class="apply-btn"
href="{{APPLY_LINK}}"
target="_blank"
rel="noopener">

🚀 Apply Online

</a>

</p>

<p>

<a
class="notification-btn"
href="{{NOTIFICATION_LINK}}"
target="_blank"
rel="noopener">

📄 Download Notification

</a>

</p>

<p>

<a
class="official-btn"
href="{{OFFICIAL_WEBSITE}}"
target="_blank"
rel="noopener">

🌐 Official Website

</a>

</p>

</div>

<hr>

<div class="join-box">

<h2>📢 Join Our WhatsApp Channel</h2>

<p>

Get instant updates about Government Jobs,
Admit Cards, Results, Answer Keys,
Scholarships and Education News.

</p>

<a

class="whatsapp-btn"

href="{{WHATSAPP_LINK}}"

target="_blank"

rel="noopener">

Join WhatsApp Channel

</a>

</div>

<br>

<div class="join-box">

<h2>📲 Join Telegram Channel</h2>

<p>

Get every recruitment notification
before everyone else.

</p>

<a

class="telegram-btn"

href="{{TELEGRAM_LINK}}"

target="_blank"

rel="noopener">

Join Telegram

</a>

</div>

<hr>

<h2>📤 Share This Job</h2>

<div class="share-buttons">

<a

target="_blank"

rel="noopener"

href="https://wa.me/?text={{POST_URL}}">

WhatsApp

</a>

<a

target="_blank"

rel="noopener"

href="https://t.me/share/url?url={{POST_URL}}">

Telegram

</a>

<a

target="_blank"

rel="noopener"

href="https://twitter.com/intent/tweet?url={{POST_URL}}">

X (Twitter)

</a>

<a

target="_blank"

rel="noopener"

href="https://www.facebook.com/sharer/sharer.php?u={{POST_URL}}">

Facebook

</a>

</div>

<hr>
<h2>❓ Frequently Asked Questions (FAQ)</h2>

<div class="faq">

<div class="faq-item">

<h3>{{FAQ1_Q}}</h3>

<p>{{FAQ1_A}}</p>

</div>

<div class="faq-item">

<h3>{{FAQ2_Q}}</h3>

<p>{{FAQ2_A}}</p>

</div>

<div class="faq-item">

<h3>{{FAQ3_Q}}</h3>

<p>{{FAQ3_A}}</p>

</div>

</div>

<hr>

<div class="author-box">

<h2>About Education Update Hub</h2>

<p>

Education Update Hub is a trusted education portal
that publishes the latest Government Jobs,
Admit Cards, Results, Answer Keys,
Scholarships, Entrance Exams and
Education News from official sources.

</p>

</div>

<hr>

<div class="related-posts">

<h2>Latest Government Jobs</h2>

<ul>

{{RELATED_POSTS}}

</ul>

</div>

<hr>

<div class="disclaimer">

<h3>Disclaimer</h3>

<p>

This article is prepared for informational purposes only.
Candidates are advised to verify all information from the
official notification before applying.
Education Update Hub is not responsible for any changes
made by the recruiting organization.

</p>

</div>

</div>

<footer class="footer">

<div class="container">

<p>

© {{YEAR}} Education Update Hub.
All Rights Reserved.

</p>

</div>

</footer>

</article>

</div>

</body>

</html>
"""
# =====================================================
# Part 5 - Dynamic Helpers
# =====================================================

def create_related_posts(job_list, current_job=None, limit=5):

    posts = []

    count = 0

    for job in job_list:

        if current_job:

            if job.get("title") == current_job.get("title"):
                continue

        slug = slugify(
            safe(job, "title")
        )

        posts.append(

            f'<li><a href="{slug}.html">'
            f'{safe(job,"title")}'
            f'</a></li>'

        )

        count += 1

        if count >= limit:
            break

    return "\n".join(posts)


# =====================================================
# FAQ Generator
# =====================================================

def build_faq(job):

    if not job.get("faq1_q"):

        job["faq1_q"] = "What is the last date to apply?"

        job["faq1_a"] = safe(
            job,
            "last_date",
            "Refer Notification"
        )

    if not job.get("faq2_q"):

        job["faq2_q"] = "What is the required qualification?"

        job["faq2_a"] = safe(
            job,
            "qualification",
            "Refer Notification"
        )

    if not job.get("faq3_q"):

        job["faq3_q"] = "Where can I apply?"

        job["faq3_a"] = "Use the Apply Online link provided above."

    return job


# =====================================================
# Placeholder Replacement
# =====================================================

def replace_placeholders(html, job, all_jobs=None):

    job = ensure_defaults(job)

    job = build_faq(job)

    related = ""

    if all_jobs:

        related = create_related_posts(
            all_jobs,
            current_job=job
        )

    replacements = {

        "{{SEO}}": generate_seo(job),

        "{{TITLE}}": safe(job, "title"),

        "{{SOURCE}}": safe(job, "source"),

        "{{DATE}}": safe(job, "date"),

        "{{SUMMARY}}": safe(job, "summary"),

        "{{NOTIFICATION_DATE}}": safe(job, "notification_date"),

        "{{START_DATE}}": safe(job, "start_date"),

        "{{LAST_DATE}}": safe(job, "last_date"),

        "{{EXAM_DATE}}": safe(job, "exam_date"),

        "{{POST_NAME}}": safe(job, "post_name"),

        "{{VACANCY}}": safe(job, "vacancy"),

        "{{QUALIFICATION}}": safe(job, "qualification"),

        "{{SALARY}}": safe(job, "salary"),

        "{{GEN_FEE}}": safe(job, "gen_fee"),

        "{{SC_FEE}}": safe(job, "sc_fee"),

        "{{MIN_AGE}}": safe(job, "min_age"),

        "{{MAX_AGE}}": safe(job, "max_age"),

        "{{STEP1}}": safe(job, "step1"),

        "{{STEP2}}": safe(job, "step2"),

        "{{STEP3}}": safe(job, "step3"),

        "{{STEP4}}": safe(job, "step4"),

        "{{APPLY_LINK}}": safe(job, "apply_link", "#"),

        "{{NOTIFICATION_LINK}}": safe(job, "notification_link", "#"),

        "{{OFFICIAL_WEBSITE}}": safe(job, "official_website", "#"),

        "{{POST_URL}}": get_post_url(job),

        "{{IMAGE}}": get_image(job),

        "{{BREADCRUMB}}": create_breadcrumb(job),

        "{{WHATSAPP_LINK}}": WHATSAPP_CHANNEL,

        "{{TELEGRAM_LINK}}": TELEGRAM_CHANNEL,

        "{{FAQ1_Q}}": safe(job, "faq1_q"),

        "{{FAQ1_A}}": safe(job, "faq1_a"),

        "{{FAQ2_Q}}": safe(job, "faq2_q"),

        "{{FAQ2_A}}": safe(job, "faq2_a"),

        "{{FAQ3_Q}}": safe(job, "faq3_q"),

        "{{FAQ3_A}}": safe(job, "faq3_a"),

        "{{RELATED_POSTS}}": related,

        "{{YEAR}}": str(datetime.now().year)

    }

    for key, value in replacements.items():

        html = html.replace(key, str(value))

    return html
    # =====================================================
# Part 6 - HTML Generator
# =====================================================

def validate_job(job):

    if not job.get("title"):

        raise ValueError("Job title is missing.")

    return ensure_defaults(job)


# =====================================================
# Generate Single HTML
# =====================================================

def generate_html(job, all_jobs=None):

    job = validate_job(job)

    html = replace_placeholders(
        BODY_TEMPLATE,
        job,
        all_jobs
    )

    filename = slugify(
        safe(job, "title")
    ) + ".html"

    os.makedirs(
        OUTPUT_FOLDER,
        exist_ok=True
    )

    filepath = os.path.join(
        OUTPUT_FOLDER,
        filename
    )

    try:

        with open(
            filepath,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(html)

        logger.info(
            f"Generated : {filepath}"
        )

        return filepath

    except Exception as e:

        logger.exception(
            f"Failed to generate {filename}"
        )

        raise e


# =====================================================
# Validate Generated HTML
# =====================================================

def validate_html(filepath):

    try:

        with open(
            filepath,
            "r",
            encoding="utf-8"
        ) as f:

            html = f.read()

        required = [

            "<html",

            "</html>",

            "<head",

            "</head>",

            "<body",

            "</body>",

            "<title"

        ]

        for tag in required:

            if tag.lower() not in html.lower():

                logger.warning(
                    f"{filepath} missing {tag}"
                )

                return False

        return True

    except Exception:

        return False


# =====================================================
# Generate and Verify
# =====================================================

def generate_verified_html(job, all_jobs=None):

    filepath = generate_html(
        job,
        all_jobs
    )

    if validate_html(filepath):

        logger.info(
            "HTML Validation Passed"
        )

    else:

        logger.warning(
            "HTML Validation Failed"
        )

    return filepath
    # =====================================================
# Part 7 - Bulk HTML Generator
# =====================================================

def generate_all(job_list):

    if not job_list:

        logger.info("No jobs available for HTML generation.")

        return []

    logger.info("=" * 60)
    logger.info("Starting HTML Generation")
    logger.info("=" * 60)

    generated_files = []

    failed_jobs = []

    total = len(job_list)

    for index, job in enumerate(job_list, start=1):

        try:

            logger.info(
                f"[{index}/{total}] {safe(job,'title')}"
            )

            filepath = generate_verified_html(
                job,
                job_list
            )

            generated_files.append(filepath)

        except Exception as e:

            logger.exception(
                f"Failed : {safe(job,'title')}"
            )

            failed_jobs.append({

                "title": safe(job, "title"),

                "error": str(e)

            })

    logger.info("=" * 60)
    logger.info("HTML Generation Completed")
    logger.info("=" * 60)

    logger.info(
        f"Generated : {len(generated_files)}"
    )

    logger.info(
        f"Failed : {len(failed_jobs)}"
    )

    if failed_jobs:

        logger.warning("Failed Jobs:")

        for item in failed_jobs:

            logger.warning(
                f"{item['title']} -> {item['error']}"
            )

    return generated_files


# =====================================================
# Statistics
# =====================================================

def print_generation_summary(files):

    logger.info("=" * 60)

    logger.info(
        f"Total HTML Files : {len(files)}"
    )

    for file in files:

        logger.info(file)

    logger.info("=" * 60)
    # =====================================================
# Part 8 - Internal Linking & Navigation
# =====================================================

def create_latest_jobs(job_list, limit=10):

    html = []

    for job in job_list[:limit]:

        slug = slugify(
            safe(job, "title")
        )

        html.append(
            f'<li><a href="{slug}.html">'
            f'{safe(job,"title")}'
            '</a></li>'
        )

    return "\n".join(html)


# =====================================================
# Previous / Next Navigation
# =====================================================

def create_navigation(job, job_list):

    previous_link = ""
    next_link = ""

    try:

        index = job_list.index(job)

        if index > 0:

            prev = job_list[index - 1]

            previous_link = f"""
<a class="prev-post"
href="{slugify(prev['title'])}.html">
← {prev['title']}
</a>
"""

        if index < len(job_list) - 1:

            nxt = job_list[index + 1]

            next_link = f"""
<a class="next-post"
href="{slugify(nxt['title'])}.html">
{nxt['title']} →
</a>
"""

    except Exception:

        pass

    return previous_link + next_link


# =====================================================
# Related Jobs (Same Category)
# =====================================================

def related_by_category(current_job, jobs, limit=6):

    category = current_job.get("category")

    html = []

    for job in jobs:

        if job == current_job:
            continue

        if job.get("category") != category:
            continue

        slug = slugify(job["title"])

        html.append(

            f'<li><a href="{slug}.html">'
            f'{job["title"]}</a></li>'

        )

        if len(html) >= limit:
            break

    return "\n".join(html)


# =====================================================
# Internal Link Injection
# =====================================================

def inject_internal_blocks(html, job, jobs):

    latest = create_latest_jobs(jobs)

    related = related_by_category(
        job,
        jobs
    )

    navigation = create_navigation(
        job,
        jobs
    )

    block = f"""

<hr>

<section class="latest-jobs">

<h2>Latest Government Jobs</h2>

<ul>

{latest}

</ul>

</section>

<hr>

<section class="related-jobs">

<h2>Related Jobs</h2>

<ul>

{related}

</ul>

</section>

<hr>

<div class="post-navigation">

{navigation}

</div>

"""

    html = html.replace(
        "</div>\n\n<footer",
        block + "\n</div>\n\n<footer"
    )

    return html


# =====================================================
# SEO Footer
# =====================================================

def create_seo_footer(job):

    return f"""

<section class="seo-footer">

<p>

<strong>{safe(job,'title')}</strong>
notification, eligibility,
salary, selection process,
important dates,
application fee,
official notification PDF
and apply online link
are available above.

Always verify every detail
from the official notification
before applying.

</p>

</section>

"""
# =====================================================
# Part 9 - Final HTML Processing
# =====================================================

def minify_html(html):

    html = re.sub(r">\s+<", "><", html)
    html = re.sub(r"\n{2,}", "\n", html)
    html = re.sub(r"[ \t]{2,}", " ", html)

    return html.strip()


# =====================================================
# Final HTML Builder
# =====================================================

def build_final_html(job, all_jobs):

    html = replace_placeholders(
        BODY_TEMPLATE,
        job,
        all_jobs
    )

    html = inject_internal_blocks(
        html,
        job,
        all_jobs
    )

    html = html.replace(

        "</footer>",

        create_seo_footer(job) + "\n</footer>"

    )

    html = minify_html(html)

    return html


# =====================================================
# Production HTML Generator
# =====================================================

def generate_html(job, all_jobs=None):

    job = validate_job(job)

    if all_jobs is None:

        all_jobs = [job]

    html = build_final_html(
        job,
        all_jobs
    )

    filename = slugify(
        safe(job, "title")
    ) + ".html"

    os.makedirs(
        OUTPUT_FOLDER,
        exist_ok=True
    )

    filepath = os.path.join(
        OUTPUT_FOLDER,
        filename
    )

    with open(
        filepath,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(html)

    logger.info(
        f"Generated : {filepath}"
    )

    return filepath


# =====================================================
# File Verification
# =====================================================

def verify_generated_file(filepath):

    if not os.path.exists(filepath):

        return False

    if os.path.getsize(filepath) < 1500:

        logger.warning(
            f"{filepath} seems too small."
        )

        return False

    return True


# =====================================================
# Safe HTML Generator
# =====================================================

def generate_verified_html(job, all_jobs=None):

    filepath = generate_html(
        job,
        all_jobs
    )

    if verify_generated_file(filepath):

        logger.info(
            "Verification Passed"
        )

    else:

        logger.warning(
            "Verification Failed"
        )

    return filepath
    # =====================================================
# Part 10 - Final Production Version
# =====================================================

def generate_all(job_list):

    logger.info("=" * 60)
    logger.info("Education Update Hub HTML Generator")
    logger.info("=" * 60)

    if not job_list:

        logger.info("No jobs to generate.")

        return []

    generated = []

    failed = []

    total = len(job_list)

    for index, job in enumerate(job_list, start=1):

        try:

            logger.info(
                f"[{index}/{total}] {safe(job,'title')}"
            )

            file = generate_verified_html(
                job,
                job_list
            )

            generated.append(file)

        except Exception as e:

            logger.exception(e)

            failed.append(job.get("title", "Unknown"))

    logger.info("=" * 60)

    logger.info(
        f"Generated Files : {len(generated)}"
    )

    logger.info(
        f"Failed Files : {len(failed)}"
    )

    if failed:

        logger.warning("Failed Jobs")

        for title in failed:

            logger.warning(title)

    logger.info("=" * 60)

    return generated


# =====================================================
# Report
# =====================================================

def generation_report(files):

    print("\n")

    print("=" * 60)

    print("HTML Generation Report")

    print("=" * 60)

    print(f"Total Files : {len(files)}")

    for file in files:

        print(file)

    print("=" * 60)


# =====================================================
# Standalone Testing
# =====================================================

if __name__ == "__main__":

    sample_job = {

        "title": "SSC CGL Recruitment 2026",

        "category": "SSC Jobs",

        "summary": "SSC CGL Recruitment 2026 notification released.",

        "source": "SSC",

        "notification_date": "25 July 2026",

        "start_date": "25 July 2026",

        "last_date": "20 August 2026",

        "exam_date": "October 2026",

        "vacancy": "14582",

        "qualification": "Graduate",

        "salary": "Level-4 to Level-7",

        "apply_link": "https://ssc.gov.in",

        "official_website": "https://ssc.gov.in"

    }

    files = generate_all([sample_job])

    generation_report(files)
