# =====================================================
# html_generator.py (Production Version)
# Part 1 - Imports, Config & Logging
# =====================================================

import os
import re
import html
import logging
from pathlib import Path
from datetime import datetime

from seo_generator import generate_seo

from config import (
    SITE_NAME,
    SITE_URL,
    DEFAULT_IMAGE,
    WHATSAPP_CHANNEL,
    TELEGRAM_CHANNEL,
    ADSENSE_CLIENT,
    GA_MEASUREMENT_ID,
)

# =====================================================
# Paths
# =====================================================

BASE_DIR = Path(__file__).resolve().parent

OUTPUT_FOLDER = BASE_DIR / "generated"

OUTPUT_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)

# =====================================================
# Logging
# =====================================================

logger = logging.getLogger("HTMLGenerator")

if not logger.handlers:

    handler = logging.StreamHandler()

    formatter = logging.Formatter(

        "%(asctime)s | %(levelname)s | %(message)s"

    )

    handler.setFormatter(formatter)

    logger.addHandler(handler)

logger.setLevel(logging.INFO)
# =====================================================
# Part 2 - Production Utility Functions
# =====================================================

def clean_text(text: str) -> str:
    """
    Clean text by removing extra spaces and HTML entities.
    """

    if text is None:
        return ""

    text = html.unescape(str(text))

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def sanitize_html(text: str) -> str:
    """
    Escape unsafe HTML.
    """

    return html.escape(clean_text(text))


def slugify(text: str) -> str:
    """
    Create SEO friendly slug.
    """

    text = clean_text(text).lower()

    text = re.sub(r"&", " and ", text)

    text = re.sub(r"[^a-z0-9]+", "-", text)

    text = re.sub(r"-{2,}", "-", text)

    text = text.strip("-")

    return text or "government-job"


def safe(job: dict, key: str, default="N/A"):

    value = job.get(key)

    if value is None:
        return default

    value = clean_text(value)

    if value == "":
        return default

    return value


def create_slug(job):

    return slugify(
        safe(job, "title", "government-job")
    )


def get_post_url(job):

    if job.get("post_url"):

        return job["post_url"]

    return (
        f"{SITE_URL}/generated/"
        f"{create_slug(job)}.html"
    )


def get_image(job):

    image = clean_text(
        job.get("image", "")
    )

    if image:

        return image

    return DEFAULT_IMAGE


def get_today():

    return datetime.now().strftime(
        "%d %B %Y"
    )


def create_breadcrumb(job):

    category = slugify(
        safe(job, "category", "latest-jobs")
    )

    category_name = safe(
        job,
        "category",
        "Latest Jobs"
    )

    return f"""
<a href="{SITE_URL}">Home</a>

&gt;

<a href="{SITE_URL}/{category}.html">

{category_name}

</a>

&gt;

<span>

{sanitize_html(safe(job,'title'))}

</span>
"""
# =====================================================
# Part 3 - Smart Defaults & Job Normalizer
# =====================================================

def default_summary(job):

    title = safe(job, "title")
    qualification = safe(job, "qualification", "Various Qualification")
    vacancy = safe(job, "vacancy", "As Per Notification")
    last_date = safe(job, "last_date", "Check Notification")

    return (
        f"{title} notification has been released. "
        f"Eligible candidates having {qualification} qualification "
        f"can apply online. Total vacancies: {vacancy}. "
        f"Check eligibility, age limit, selection process, salary, "
        f"important dates and apply before {last_date}."
    )


# =====================================================
# Generate Smart FAQ
# =====================================================

def build_faq(job):

    job["faq1_q"] = "What is the last date to apply?"

    job["faq1_a"] = safe(
        job,
        "last_date",
        "Refer Official Notification"
    )

    job["faq2_q"] = "What is the required qualification?"

    job["faq2_a"] = safe(
        job,
        "qualification",
        "Refer Official Notification"
    )

    job["faq3_q"] = "How can I apply?"

    job["faq3_a"] = (
        "Visit the official website and submit "
        "the online application form."
    )

    return job


# =====================================================
# Ensure Complete Job Data
# =====================================================

def ensure_defaults(job):

    job = dict(job)

    defaults = {

        "title": "Government Recruitment",

        "summary": default_summary(job),

        "date": get_today(),

        "source": SITE_NAME,

        "category": "Latest Jobs",

        "notification_date": "Available Soon",

        "start_date": "Check Notification",

        "last_date": "Check Notification",

        "exam_date": "To Be Announced",

        "post_name": safe(job, "title"),

        "vacancy": "As Per Notification",

        "qualification": "Refer Notification",

        "salary": "As Per Rules",

        "selection_process":
            "Written Exam / Interview",

        "gen_fee": "Refer Notification",

        "sc_fee": "Refer Notification",

        "min_age": "18 Years",

        "max_age": "As Per Rules",

        "step1":
            "Visit the official website.",

        "step2":
            "Read the official notification carefully.",

        "step3":
            "Fill the application form correctly.",

        "step4":
            "Submit the application before the last date.",

        "apply_link": "#",

        "notification_link": "#",

        "official_website": "#"

    }

    for key, value in defaults.items():

        if not job.get(key):

            job[key] = value

    job["summary"] = default_summary(job)

    job["post_url"] = get_post_url(job)

    job["image"] = get_image(job)

    job = build_faq(job)

    return job
    # =====================================================
# Part 4 - BODY_TEMPLATE (Section 1)
# =====================================================

BODY_TEMPLATE = """<!DOCTYPE html>

<html lang="en">

<head>

{{SEO}}

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1">

<meta name="robots"
content="index,follow,max-image-preview:large">

<meta name="author"
content="Education Update Hub">

<link rel="canonical"
href="{{POST_URL}}">

<link rel="icon"
href="/favicon.ico">

<link rel="stylesheet"
href="/style.css">

</head>

<body>

<header class="site-header">

<div class="container">

<a href="/"
class="logo">

Education Update Hub

</a>

<nav>

<a href="/">Home</a>

<a href="/latest-jobs.html">
Latest Jobs
</a>

<a href="/admit-card.html">
Admit Card
</a>

<a href="/result.html">
Results
</a>

</nav>

</div>

</header>

<main class="container">

<nav class="breadcrumb">

{{BREADCRUMB}}

</nav>

<article class="job-article">

<h1>

{{TITLE}}

</h1>

<div class="meta">

<span>

📅 {{DATE}}

</span>

<span>

🏢 {{SOURCE}}

</span>

</div>

<img

src="{{IMAGE}}"

alt="{{TITLE}}"

loading="lazy"

class="featured-image">

<div class="summary-box">

<p>

{{SUMMARY}}

</p>

</div>

<section>

<h2>

Important Dates

</h2>

<table class="job-table">

<tr>

<th>Notification</th>

<td>

{{NOTIFICATION_DATE}}

</td>

</tr>

<tr>

<th>Application Start</th>

<td>

{{START_DATE}}

</td>

</tr>

<tr>

<th>Last Date</th>

<td>

{{LAST_DATE}}

</td>

</tr>

<tr>

<th>Exam Date</th>

<td>

{{EXAM_DATE}}

</td>

</tr>

</table>

</section>

<section>

<h2>

Vacancy Details

</h2>

<table class="job-table">

<tr>

<th>Post</th>

<td>

{{POST_NAME}}

</td>

</tr>

<tr>

<th>Total Vacancy</th>

<td>

{{VACANCY}}

</td>

</tr>

<tr>

<th>Qualification</th>

<td>

{{QUALIFICATION}}

</td>

</tr>

<tr>

<th>Salary</th>

<td>

{{SALARY}}

</td>

</tr>

</table>

</section>
<section>

<h2>

Application Fee

</h2>

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

</section>

<section>

<h2>

Age Limit

</h2>

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

</section>

<section>

<h2>

Selection Process

</h2>

<p>

{{SELECTION_PROCESS}}

</p>

</section>

<section>

<h2>

How To Apply

</h2>

<ol>

<li>{{STEP1}}</li>

<li>{{STEP2}}</li>

<li>{{STEP3}}</li>

<li>{{STEP4}}</li>

</ol>

</section>

<section>

<h2>

Important Links

</h2>

<div class="button-group">

<a
class="btn apply-btn"
href="{{APPLY_LINK}}"
target="_blank"
rel="nofollow noopener">

Apply Online

</a>

<a
class="btn notification-btn"
href="{{NOTIFICATION_LINK}}"
target="_blank"
rel="nofollow noopener">

Download Notification

</a>

<a
class="btn website-btn"
href="{{OFFICIAL_WEBSITE}}"
target="_blank"
rel="noopener">

Official Website

</a>

</div>

</section>

<!-- Adsense Top -->

<div class="adsense-box">

{{ADSENSE_TOP}}

</div>

<section class="join-box">

<h2>

Join WhatsApp Channel

</h2>

<p>

Get instant updates about
Government Jobs,
Results,
Admit Cards,
Scholarships and
Education News.

</p>

<a

class="btn whatsapp-btn"

href="{{WHATSAPP_LINK}}"

target="_blank"

rel="noopener">

Join WhatsApp

</a>

</section>

<section class="join-box">

<h2>

Join Telegram Channel

</h2>

<p>

Join our Telegram channel
for fastest recruitment updates.

</p>

<a

class="btn telegram-btn"

href="{{TELEGRAM_LINK}}"

target="_blank"

rel="noopener">

Join Telegram

</a>

</section>

<section>

<h2>

Share This Job

</h2>

<div class="share-buttons">

<a
target="_blank"
href="https://wa.me/?text={{POST_URL}}">

WhatsApp

</a>

<a
target="_blank"
href="https://t.me/share/url?url={{POST_URL}}">

Telegram

</a>

<a
target="_blank"
href="https://twitter.com/intent/tweet?url={{POST_URL}}">

X

</a>

<a
target="_blank"
href="https://www.facebook.com/sharer/sharer.php?u={{POST_URL}}">

Facebook

</a>

</div>

</section>

<!-- Adsense Middle -->

<div class="adsense-box">

{{ADSENSE_MIDDLE}}

</div>
<section>

<h2>

Frequently Asked Questions

</h2>

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

</section>

<!-- Adsense Bottom -->

<div class="adsense-box">

{{ADSENSE_BOTTOM}}

</div>

<section class="about-site">

<h2>

About Education Update Hub

</h2>

<p>

Education Update Hub publishes the latest Government Jobs,
Admit Cards, Results, Answer Keys, Scholarships,
Entrance Exams and Education News based on official
notifications. Candidates are advised to verify all
information from the official notification before applying.

</p>

</section>

<section>

<h2>

Related Government Jobs

</h2>

<ul>

{{RELATED_POSTS}}

</ul>

</section>

<section>

<h2>

Latest Government Jobs

</h2>

<ul>

{{LATEST_POSTS}}

</ul>

</section>

<section class="disclaimer">

<h2>

Disclaimer

</h2>

<p>

The information provided on this page is for educational
and informational purposes only. Although every effort is
made to ensure accuracy, candidates must verify all
details from the official notification before applying.
Education Update Hub shall not be responsible for any
changes made by the recruiting authority.

</p>

</section>

<footer class="site-footer">

<p>

© {{YEAR}}
Education Update Hub.
All Rights Reserved.

</p>

</footer>

</article>

</main>

</body>

</html>
"""
# =====================================================
# Part 7 - HTML Builder Functions
# =====================================================

def replace_placeholders(template, job):

    replacements = {

        "{{TITLE}}": sanitize_html(safe(job, "title")),

        "{{SUMMARY}}": sanitize_html(safe(job, "summary")),

        "{{DATE}}": safe(job, "date"),

        "{{SOURCE}}": safe(job, "source"),

        "{{IMAGE}}": safe(job, "image"),

        "{{POST_URL}}": safe(job, "post_url"),

        "{{BREADCRUMB}}": create_breadcrumb(job),

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

        "{{SELECTION_PROCESS}}": safe(job, "selection_process"),

        "{{STEP1}}": safe(job, "step1"),

        "{{STEP2}}": safe(job, "step2"),

        "{{STEP3}}": safe(job, "step3"),

        "{{STEP4}}": safe(job, "step4"),

        "{{APPLY_LINK}}": safe(job, "apply_link"),

        "{{NOTIFICATION_LINK}}": safe(job, "notification_link"),

        "{{OFFICIAL_WEBSITE}}": safe(job, "official_website"),

        "{{FAQ1_Q}}": safe(job, "faq1_q"),

        "{{FAQ1_A}}": safe(job, "faq1_a"),

        "{{FAQ2_Q}}": safe(job, "faq2_q"),

        "{{FAQ2_A}}": safe(job, "faq2_a"),

        "{{FAQ3_Q}}": safe(job, "faq3_q"),

        "{{FAQ3_A}}": safe(job, "faq3_a"),

        "{{RELATED_POSTS}}": job.get("related_posts", ""),

        "{{LATEST_POSTS}}": job.get("latest_posts", ""),

        "{{WHATSAPP_LINK}}": WHATSAPP_CHANNEL,

        "{{TELEGRAM_LINK}}": TELEGRAM_CHANNEL,

        "{{YEAR}}": str(datetime.now().year)

    }

    html_output = template

    for key, value in replacements.items():

        html_output = html_output.replace(
            key,
            str(value)
        )

    return html_output


# =====================================================
# Inject SEO + Adsense
# =====================================================

def build_final_html(job):

    job = ensure_defaults(job)

    html_output = replace_placeholders(
        BODY_TEMPLATE,
        job
    )

    seo = generate_seo(job)

    html_output = html_output.replace(
        "{{SEO}}",
        seo
    )

    html_output = html_output.replace(
        "{{ADSENSE_TOP}}",
        '<!-- Adsense Top -->'
    )

    html_output = html_output.replace(
        "{{ADSENSE_MIDDLE}}",
        '<!-- Adsense Middle -->'
    )

    html_output = html_output.replace(
        "{{ADSENSE_BOTTOM}}",
        '<!-- Adsense Bottom -->'
    )

    return html_output


# =====================================================
# HTML Minifier
# =====================================================

def minify_html(html_content):

    html_content = re.sub(
        r">\s+<",
        "><",
        html_content
    )

    html_content = re.sub(
        r"\n+",
        "\n",
        html_content
    )

    return html_content.strip()
    # =====================================================
# Part 8 - HTML Generation & Validation
# =====================================================

def validate_html(html_content):

    required_tags = [

        "<!DOCTYPE html>",
        "<html",
        "<head",
        "<body",
        "</html>",
        "<title",
        'rel="canonical"'

    ]

    missing = []

    html_lower = html_content.lower()

    for tag in required_tags:

        if tag.lower() not in html_lower:

            missing.append(tag)

    return missing


# =====================================================
# Generate HTML
# =====================================================

def generate_html(job):

    job = ensure_defaults(job)

    html_output = build_final_html(job)

    html_output = minify_html(html_output)

    errors = validate_html(html_output)

    if errors:

        raise ValueError(

            "HTML Validation Failed: "

            + ", ".join(errors)

        )

    return html_output


# =====================================================
# Save HTML File
# =====================================================

def save_html(job, html_output):

    slug = create_slug(job)

    file_path = OUTPUT_FOLDER / f"{slug}.html"

    file_path.write_text(

        html_output,

        encoding="utf-8"

    )

    logger.info(

        "Generated: %s",

        file_path.name

    )

    return file_path


# =====================================================
# Generate Verified HTML
# =====================================================

def generate_verified_html(job):

    try:

        html_output = generate_html(job)

        file_path = save_html(

            job,

            html_output

        )

        return {

            "success": True,

            "file": str(file_path),

            "slug": create_slug(job)

        }

    except Exception as exc:

        logger.exception(

            "Failed to generate HTML for %s",

            safe(job, "title")

        )

        return {

            "success": False,

            "title": safe(job, "title"),

            "error": str(exc)

        }
        # =====================================================
# Part 9 - Bulk HTML Generator
# =====================================================

def generate_all(jobs):

    results = []

    success = 0

    failed = 0

    logger.info(

        "Starting HTML generation for %d jobs",

        len(jobs)

    )

    for job in jobs:

        result = generate_verified_html(job)

        results.append(result)

        if result["success"]:

            success += 1

        else:

            failed += 1

    logger.info(

        "Generation Completed | Success=%d | Failed=%d",

        success,

        failed

    )

    return {

        "success": success,

        "failed": failed,

        "total": len(jobs),

        "results": results

    }


# =====================================================
# Build Generation Report
# =====================================================

def build_report(summary):

    report = []

    report.append("HTML GENERATION REPORT")

    report.append("=" * 40)

    report.append(f"Total Jobs : {summary['total']}")

    report.append(f"Generated  : {summary['success']}")

    report.append(f"Failed     : {summary['failed']}")

    report.append("")

    for item in summary["results"]:

        if item["success"]:

            report.append(

                f"✔ {item['slug']}"

            )

        else:

            report.append(

                f"✘ {item['title']}"

            )

            report.append(

                f"   {item['error']}"

            )

            report.append("")

    return "\n".join(report)


# =====================================================
# Save Report
# =====================================================

def save_report(summary):

    report = build_report(summary)

    report_file = OUTPUT_FOLDER / "generation_report.txt"

    report_file.write_text(

        report,

        encoding="utf-8"

    )

    logger.info(

        "Report Saved: %s",

        report_file.name

    )

    return report_file


# =====================================================
# Production Runner
# =====================================================

def run_generator(jobs):

    summary = generate_all(jobs)

    save_report(summary)

    return summary
    # =====================================================
# Part 10 - Production Entry Point
# =====================================================

def main(jobs):

    logger.info("=" * 60)

    logger.info("Education Update Hub HTML Generator Started")

    logger.info("=" * 60)

    summary = run_generator(jobs)

    logger.info("")

    logger.info("Generation Summary")

    logger.info("-------------------------------")

    logger.info("Total   : %d", summary["total"])

    logger.info("Success : %d", summary["success"])

    logger.info("Failed  : %d", summary["failed"])

    logger.info("-------------------------------")

    if summary["failed"] == 0:

        logger.info("All HTML files generated successfully.")

    else:

        logger.warning(

            "%d files failed during generation.",

            summary["failed"]

        )

    logger.info("HTML Generator Finished.")

    return summary


# =====================================================
# Future Hooks
# =====================================================

def after_generation(summary):

    """
    Future integrations.

    Example:

    update_homepage()

    update_sitemap()

    generate_rss()

    ping_google()

    ping_bing()

    submit_indexnow()

    """

    logger.info(

        "Post-generation hooks completed."

    )


# =====================================================
# Standalone Testing
# =====================================================

if __name__ == "__main__":

    logger.info("Running standalone mode.")

    sample_jobs = [

        {

            "title": "Sample Government Recruitment",

            "vacancy": "100",

            "qualification": "Graduate",

            "last_date": "30 August 2026",

            "salary": "Level-6",

            "category": "Latest Jobs",

            "official_website": "https://example.gov.in",

            "apply_link": "https://example.gov.in/apply",

            "notification_link": "https://example.gov.in/notification"

        }

    ]

    summary = main(sample_jobs)

    after_generation(summary)
