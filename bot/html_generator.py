import os
import re

from seo_generator import generate_seo

OUTPUT_FOLDER = "generated"

BODY_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>

{{SEO}}

<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<link rel="stylesheet" href="../style.css">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>

<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">

</head>

<body>

<header class="top-header">
<div class="container">

<a href="../index.html">
<h1>Education Update Hub</h1>
</a>

</div>
</header>

<div class="container">

<nav class="breadcrumb">

<a href="../index.html">Home</a>

>

<a href="../teacher-recruitment.html">Latest Jobs</a>

>

<span>{{TITLE}}</span>

</nav>

<h1 class="post-title">
{{TITLE}}
</h1>

<div class="post-meta">

Published : {{DATE}}

|

Source : {{SOURCE}}

</div>

<img
src="../images/default-job.png"
alt="{{TITLE}}"
class="featured-image">

<div class="content">

<p>{{SUMMARY}}</p>

<hr>

<h2>Important Dates</h2>

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

<h2>Vacancy Details</h2>

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

<h2>Application Fee</h2>

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

<h2>Age Limit</h2>

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

<h2>How to Apply</h2>

<ol>

<li>{{STEP1}}</li>

<li>{{STEP2}}</li>

<li>{{STEP3}}</li>

<li>{{STEP4}}</li>

</ol>

<hr>

<h2>Important Links</h2>

<div class="important-links">

<p>
<a class="apply-btn"
href="{{APPLY_LINK}}"
target="_blank">
Apply Online
</a>
</p>

<p>
<a class="notification-btn"
href="{{NOTIFICATION_LINK}}"
target="_blank">
Download Notification
</a>
</p>

<p>
<a class="official-btn"
href="{{OFFICIAL_WEBSITE}}"
target="_blank">
Official Website
</a>
</p>

</div>

<hr>

<div class="join-box">

<h2>📢 Join Our WhatsApp Channel</h2>

<p>
Get Latest Government Jobs, Admit Card,
Results, Answer Key and Scholarship Updates.
</p>

<a class="whatsapp-btn"
href="https://whatsapp.com/channel/YOUR_CHANNEL_LINK"
target="_blank">

Join WhatsApp Channel

</a>

</div>

<br>

<div class="join-box">

<h2>📲 Join Telegram Channel</h2>

<p>
Never Miss Any Recruitment Notification.
</p>

<a class="telegram-btn"
href="https://t.me/YOUR_TELEGRAM_LINK"
target="_blank">

Join Telegram

</a>

</div>

<hr>

<h2>Share This Job</h2>

<div class="share-buttons">

<a target="_blank"
href="https://wa.me/?text={{POST_URL}}">
WhatsApp
</a>

<a target="_blank"
href="https://t.me/share/url?url={{POST_URL}}">
Telegram
</a>

<a target="_blank"
href="https://twitter.com/intent/tweet?url={{POST_URL}}">
Twitter (X)
</a>

<a target="_blank"
href="https://www.facebook.com/sharer/sharer.php?u={{POST_URL}}">
Facebook
</a>

</div>

<hr>

<h2>Frequently Asked Questions (FAQ)</h2>

<div class="faq">

<h3>{{FAQ1_Q}}</h3>
<p>{{FAQ1_A}}</p>

<h3>{{FAQ2_Q}}</h3>
<p>{{FAQ2_A}}</p>

<h3>{{FAQ3_Q}}</h3>
<p>{{FAQ3_A}}</p>

</div>

<hr>

<div class="author-box">

<h3>About Education Update Hub</h3>

<p>

Education Update Hub provides the latest Government Jobs,
Admit Cards, Results, Answer Keys, Scholarships,
Exam Notifications and Education News.

</p>

</div>

<hr>

<div class="related-posts">

<h2>Latest Government Jobs</h2>

<ul>

{{RELATED_POSTS}}

</ul>

</div>

</div>

</body>

</html>
"""
def slugify(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def generate_html(job):

    html = BODY_TEMPLATE

    html = html.replace(
        "{{SEO}}",
        generate_seo(job)
    )

    replacements = {

        "{{TITLE}}": job.get("title", ""),

        "{{SOURCE}}": job.get("source", ""),

        "{{DATE}}": job.get("date", ""),

        "{{SUMMARY}}": job.get("summary", ""),

        "{{NOTIFICATION_DATE}}": job.get("notification_date", ""),

        "{{START_DATE}}": job.get("start_date", ""),

        "{{LAST_DATE}}": job.get("last_date", ""),

        "{{EXAM_DATE}}": job.get("exam_date", ""),

        "{{POST_NAME}}": job.get("post_name", ""),

        "{{VACANCY}}": job.get("vacancy", ""),

        "{{GEN_FEE}}": job.get("gen_fee", ""),

        "{{SC_FEE}}": job.get("sc_fee", ""),

        "{{MIN_AGE}}": job.get("min_age", ""),

        "{{MAX_AGE}}": job.get("max_age", ""),

        "{{SALARY}}": job.get("salary", ""),

        "{{QUALIFICATION}}": job.get("qualification", ""),

        "{{STEP1}}": job.get("step1", ""),

        "{{STEP2}}": job.get("step2", ""),

        "{{STEP3}}": job.get("step3", ""),

        "{{STEP4}}": job.get("step4", ""),

        "{{APPLY_LINK}}": job.get("apply_link", "#"),

        "{{NOTIFICATION_LINK}}": job.get("notification_link", "#"),

        "{{OFFICIAL_WEBSITE}}": job.get("official_website", "#"),

        "{{POST_URL}}": job.get("post_url", "#"),

        "{{FAQ1_Q}}": job.get("faq1_q", ""),

        "{{FAQ1_A}}": job.get("faq1_a", ""),

        "{{FAQ2_Q}}": job.get("faq2_q", ""),

        "{{FAQ2_A}}": job.get("faq2_a", ""),

        "{{FAQ3_Q}}": job.get("faq3_q", ""),

        "{{FAQ3_A}}": job.get("faq3_a", ""),

        "{{RELATED_POSTS}}": job.get("related_posts", "")
    }

    for key, value in replacements.items():
        html = html.replace(key, str(value))
        filename = slugify(job.get("title", "job")) + ".html"

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    filepath = os.path.join(OUTPUT_FOLDER, filename)

    with open(filepath, "w", encoding="utf-8") as file:
        file.write(html)

    print(f"✅ HTML Generated Successfully : {filepath}")

    return filepath


def generate_all(job_list):

    generated_files = []

    for job in job_list:
        try:
            generated_files.append(generate_html(job))
        except Exception as e:
            print(f"❌ Error generating '{job.get('title','Unknown')}'")
            print(e)

    print(f"\n🎉 Total HTML Files Generated : {len(generated_files)}")

    return generated_files


if __name__ == "__main__":

    sample_job = {

        "title": "Sample Recruitment 2026",

        "source": "Education Update Hub",

        "date": "24 July 2026",

        "summary": "This is a sample recruitment notification.",

        "notification_date": "24 July 2026",

        "start_date": "25 July 2026",

        "last_date": "20 August 2026",

        "exam_date": "September 2026",

        "post_name": "Clerk",

        "vacancy": "100",

        "gen_fee": "₹500",

        "sc_fee": "₹250",

        "min_age": "18 Years",

        "max_age": "40 Years",

        "salary": "₹25,500 - ₹81,100",

        "qualification": "Graduate",

        "step1": "Visit the official website.",

        "step2": "Register yourself.",

        "step3": "Fill the application form and upload documents.",

        "step4": "Pay the fee and submit the form.",

        "apply_link": "#",

        "notification_link": "#",

        "official_website": "#",

        "post_url": "https://educationupdatehub.in/sample-recruitment-2026.html",

        "faq1_q": "What is the last date to apply?",

        "faq1_a": "20 August 2026.",

        "faq2_q": "What is the qualification?",

        "faq2_a": "Graduation.",

        "faq3_q": "What is the official website?",

        "faq3_a": "Visit the official website.",

        "related_posts": """
<li><a href="#">SSC Recruitment 2026</a></li>
<li><a href="#">Railway Recruitment 2026</a></li>
<li><a href="#">Bank Recruitment 2026</a></li>
"""
    }

    generate_html(sample_job)
