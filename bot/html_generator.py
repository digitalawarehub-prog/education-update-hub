# ==========================================================
# HTML Generator V4.1
# Part 1 : Imports + Configuration + Helpers
# ==========================================================

import re
import html
import json
import logging

from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import homepage
import category_generator

logger = logging.getLogger("HTMLGeneratorV4")
logger.setLevel(logging.INFO)

# ==========================================================
# Configuration
# ==========================================================

BASE_URL = "https://educationupdatehub.in"

GA4_ID = "G-XRESX2YP1N"

TIMEZONE = ZoneInfo("Asia/Kolkata")

ROOT_DIR = Path(__file__).resolve().parent.parent

OUTPUT_DIR = ROOT_DIR / "generated" / "posts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_IMAGE = "images/default-job.png"

INDEX_FILE = ROOT_DIR / "index.html"

CATEGORY_PAGES = {
    "नवीनतम सरकारी नौकरियां": "latest-jobs.html",
    "Recruitment": "latest-jobs.html",

    "Result": "result.html",
    "Results": "result.html",

    "Admit Card": "admit-card.html",

    "Answer Key": "answer-key.html",

    "Scholarship": "scholarship.html",

    "Syllabus": "syllabus.html",

    "Teaching Exams": "teaching-exams.html",

    "Entrance Exams": "entrance-exams.html",

    "Government Schemes": "government-schemes.html",

    "Banking Jobs": "banking-jobs.html",

    "Railway Jobs": "railway-jobs.html",

    "UPSC": "upsc.html",

    "SSC": "ssc.html",

    "CTET": "ctet.html",

    "UTET": "utet.html",

    "D.El.Ed": "deled.html",

    "Central Jobs": "central-government-jobs.html",

    "Uttarakhand Jobs": "uttarakhand-jobs.html",

    "Other State Jobs": "other-state-jobs.html"
}

# ==========================================================
# Helpers
# ==========================================================

def escape_html(text):
    if text is None:
        return ""
    return html.escape(str(text))


def generate_slug(title):
    if not title:
        return "post"

    title = str(title).lower().strip()

    title = re.sub(r"\{\{.*?\}\}", "", title)
    title = re.sub(r"&", " and ", title)

    slug = re.sub(r"[^a-z0-9]+", "-", title)
    slug = re.sub(r"-+", "-", slug).strip("-")

    if slug:
        return slug

    return f"post-{abs(hash(title))}"


# ==========================================================
# Strict Freshness / Active Job Filter
# ==========================================================

ACTIVE_CATEGORIES = {
    "latest jobs", "recruitment", "banking jobs", "railway jobs",
    "upsc", "ssc", "teacher recruitment", "uttarakhand jobs",
    "central jobs", "central government jobs", "other state jobs",
    "up jobs", "up government jobs", "bihar jobs", "rajasthan jobs",
    "mp jobs", "forest jobs", "police jobs", "government jobs",
}

NON_JOB_CATEGORIES = {
    "result", "results", "admit card", "answer key", "scholarship",
    "syllabus", "teaching exams", "entrance exams", "government schemes",
    "ctet", "utet", "d.el.ed", "deled",
}

NOISE_TITLES = {
    "apply online", "apply now", "recruitment", "recruitments",
    "recruitment notices", "application forms", "application form",
    "apply links", "recruitment/admission links", "results", "answer keys",
    "question bank online exam", "forget password", "login", "home",
    "vacancy", "vacancies", "vacancy/nia", "vacancy position",
    "download interview letter", "download hindi notification",
    "download guidelines for candidates for filling up online application",
}

MONTHS = {
    "january":1,"jan":1,"february":2,"feb":2,"march":3,"mar":3,
    "april":4,"apr":4,"may":5,"june":6,"jun":6,"july":7,"jul":7,
    "august":8,"aug":8,"september":9,"sep":9,"sept":9,
    "october":10,"oct":10,"november":11,"nov":11,"december":12,"dec":12,
}


def _parse_date(value):
    if not value:
        return None
    text=re.sub(r"\s+", " ", str(value).strip())
    m=re.search(r"\b(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})\b", text)
    if m:
        try:return datetime(int(m.group(1)),int(m.group(2)),int(m.group(3))).date()
        except ValueError:pass
    m=re.search(r"\b(\d{1,2})[-/.](\d{1,2})[-/.](20\d{2})\b", text)
    if m:
        try:return datetime(int(m.group(3)),int(m.group(2)),int(m.group(1))).date()
        except ValueError:pass
    mp="|".join(sorted(MONTHS,key=len,reverse=True))
    m=re.search(rf"\b(\d{{1,2}})\s+({mp})\.?\s+(20\d{{2}})\b",text,re.I)
    if m:
        try:return datetime(int(m.group(3)),MONTHS[m.group(2).lower().rstrip('.')],int(m.group(1))).date()
        except ValueError:pass
    m=re.search(rf"\b({mp})\.?\s+(\d{{1,2}}),?\s+(20\d{{2}})\b",text,re.I)
    if m:
        try:return datetime(int(m.group(3)),MONTHS[m.group(1).lower().rstrip('.')],int(m.group(2))).date()
        except ValueError:pass
    return None


def _deadline(job):
    for key in ("last_date","deadline","application_last_date","last_date_to_apply","closing_date","application_deadline"):
        dt=_parse_date(job.get(key))
        if dt:return dt
    text=" ".join(str(job.get(k, "")) for k in ("title","description","content","last_date","summary"))
    patterns=[
        r"(?:last\s*date(?:\s*to\s*apply)?|application\s*(?:last\s*)?date|deadline|closing\s*date|registration\s*(?:last\s*)?date|apply\s*(?:online\s*)?(?:till|by|before))\s*[:\-–]?\s*([^|<;]{3,70})",
        r"(?:अंतिम\s*तिथि|अंतिम\s*तारीख|आवेदन\s*की\s*अंतिम\s*तिथि|आवेदन\s*की\s*अंतिम\s*तारीख)\s*[:\-–]?\s*([^|<;]{3,70})",
    ]
    for pattern in patterns:
        m=re.search(pattern,text,re.I)
        if m:
            dt=_parse_date(m.group(1))
            if dt:return dt
    return None


def _publication_date(job):
    for key in ("publish_date","published_date","date_published","posted_date","notification_date","date"):
        dt=_parse_date(job.get(key))
        if dt:return dt
    return None


def _year_in_record(job):
    text=" ".join(str(job.get(k,"")) for k in ("title","year","tags","keywords"))
    years=[int(y) for y in re.findall(r"\b(20\d{2})\b",text)]
    return max(years) if years else None


def _noise_job(job):
    title=re.sub(r"\s+"," ",str(job.get("title","")).strip()).lower()
    return (not title) or title in NOISE_TITLES


def is_active_job(job):
    if _noise_job(job):
        return False
    category=str(job.get("category","नवीनतम सरकारी नौकरियां")).strip().lower()
    if category in NON_JOB_CATEGORIES:
        return True
    deadline=_deadline(job)
    today=datetime.now(TIMEZONE).date()
    if deadline:
        return deadline >= today
    year=_year_in_record(job)
    if year and year < today.year:
        return False
    pub=_publication_date(job)
    if pub:
        return pub >= today-timedelta(days=60)
    # A recruitment record with no usable deadline/date is unsafe to publish.
    return False


def filter_active_jobs(jobs):
    active=[]
    noise=0
    stale=0
    for job in jobs:
        if is_active_job(job):
            active.append(job)
        else:
            if _noise_job(job): noise += 1
            else: stale += 1
    logger.info(
        "FRESH JOB FILTER | Input=%d | Active=%d | Removed=%d | Noise=%d | Expired/Old/No-date=%d",
        len(jobs),len(active),len(jobs)-len(active),noise,stale
    )
    return active

# ==========================================================
# Remove Stale Auto-Generated Posts
# ==========================================================

def cleanup_stale_generated_posts(all_jobs, active_jobs):
    active_slugs = {generate_slug(str(j.get("title", ""))) for j in active_jobs if j.get("title")}
    stale_slugs = set()
    for job in all_jobs:
        title = str(job.get("title", "")).strip()
        if title:
            slug = generate_slug(title)
            if slug and slug not in active_slugs:
                stale_slugs.add(slug)
    removed = 0
    for slug in stale_slugs:
        path = OUTPUT_DIR / f"{slug}.html"
        if path.exists():
            try:
                path.unlink()
                removed += 1
            except Exception:
                logger.exception("Unable to remove stale post: %s", path)
    logger.info("STALE POST CLEANUP | Candidates=%d | Removed=%d", len(stale_slugs), removed)
    return removed

# ==========================================================
# Hindi Content
# ==========================================================

TITLE_REPLACEMENTS=[
    ("Government Jobs","सरकारी नौकरियां"),("Government Job","सरकारी नौकरी"),
    ("Recruitment","भर्ती"),("Recruitments","भर्तियां"),("Vacancies","रिक्तियां"),("Vacancy","रिक्ति"),
    ("Notification","अधिसूचना"),("Admit Card","प्रवेश पत्र"),("Answer Key","उत्तर कुंजी"),("Answer Keys","उत्तर कुंजी"),
    ("Results","परिणाम"),("Result","परिणाम"),("Scholarship","छात्रवृत्ति"),("Teacher","शिक्षक"),("Teachers","शिक्षक"),
    ("Police","पुलिस"),("Forest","वन"),("Jobs","नौकरियां"),("Job","नौकरी"),("Apply Online","ऑनलाइन आवेदन"),
    ("Online Application","ऑनलाइन आवेदन"),("Last Date","अंतिम तिथि"),("Examination","परीक्षा"),("Exam","परीक्षा"),
    ("Qualification","योग्यता"),("Salary","वेतन"),("Recruitment Details","भर्ती विवरण"),
]

CATEGORY_HI={
    "latest jobs":"नवीनतम सरकारी नौकरियां","recruitment":"सरकारी भर्ती","result":"परिणाम","results":"परिणाम",
    "admit card":"प्रवेश पत्र","answer key":"उत्तर कुंजी","scholarship":"छात्रवृत्ति","syllabus":"पाठ्यक्रम",
    "teaching exams":"शिक्षक परीक्षाएं","entrance exams":"प्रवेश परीक्षाएं","banking jobs":"बैंकिंग नौकरियां",
    "railway jobs":"रेलवे नौकरियां","upsc":"UPSC","ssc":"SSC","central jobs":"केंद्र सरकार की नौकरियां",
    "central government jobs":"केंद्र सरकार की नौकरियां","uttarakhand jobs":"उत्तराखंड सरकारी नौकरियां",
    "other state jobs":"अन्य राज्य सरकारी नौकरियां","government schemes":"सरकारी योजनाएं",
}


def hindi_title(title):
    text=str(title or "").strip()
    for old,new in TITLE_REPLACEMENTS:
        text=re.sub(rf"\b{re.escape(old)}\b",new,text,flags=re.I)
    return text or "सरकारी नौकरी अपडेट"


def hindi_category(category):
    raw=str(category or "नवीनतम सरकारी नौकरियां").strip()
    return CATEGORY_HI.get(raw.lower(),hindi_title(raw))


def hindi_summary(job):
    title=hindi_title(job.get("title","सरकारी नौकरी"))
    deadline=_deadline(job)
    if deadline:
        return f"{title} के संबंध में नवीनतम जानकारी यहां दी गई है। इस पोस्ट में पद, योग्यता, वेतन, महत्वपूर्ण तिथियां और आवेदन प्रक्रिया की जानकारी दी गई है। इच्छुक अभ्यर्थी आवेदन करने से पहले आधिकारिक अधिसूचना अवश्य पढ़ें। आवेदन की अंतिम तिथि {deadline.strftime('%d-%m-%Y')} है।"
    return f"{title} के संबंध में महत्वपूर्ण जानकारी इस पोस्ट में दी गई है। अभ्यर्थी पद, योग्यता, वेतन और आवेदन प्रक्रिया की जानकारी देखकर आधिकारिक वेबसाइट पर उपलब्ध अधिसूचना के अनुसार आगे की प्रक्रिया पूरी करें।"


def hindi_detail(value, default="अधिसूचना देखें"):
    text=str(value or "").strip()
    if not text or text.lower() in {"not mentioned","not available","check official notification","check notification","n/a"}:
        return default
    return text

def get_image(job):
    return (
        job.get("featured_image")
        or job.get("thumbnail")
        or job.get("image")
        or DEFAULT_IMAGE
    )


def generate_meta_description(job):
    title = hindi_title(job.get("title", ""))
    deadline = _deadline(job)
    suffix = f" अंतिम तिथि {deadline.strftime('%d-%m-%Y')}।" if deadline else " महत्वपूर्ण तिथियां और आवेदन प्रक्रिया देखें।"
    return (f"{title} भर्ती की पूरी जानकारी, योग्यता, रिक्तियां, वेतन, आवेदन प्रक्रिया और आधिकारिक अधिसूचना की जानकारी यहां देखें।" + suffix)[:160]


def canonical_url(slug):
    return f"{BASE_URL}/generated/posts/{slug}.html"


def published_date():
    return datetime.now(TIMEZONE).strftime("%Y-%m-%d")


def breadcrumb(job):

    category = job.get("category", "नवीनतम सरकारी नौकरियां")

    page = CATEGORY_PAGES.get(
        category,
        "latest-jobs.html"
    )

    return [
        {
            "name": "होम",
            "url": BASE_URL
        },
        {
            "name": category,
            "url": f"{BASE_URL}/{page}"
        },
        {
            "name": job.get("title", ""),
            "url": canonical_url(
                generate_slug(job.get("title", ""))
            )
        }
    ]


logger.info("HTML Generator V4.1 Part 1 Loaded Successfully")
# ==========================================================
# Part 2 : HTML Head + SEO + Schema
# ==========================================================

def build_html_head(job):

    title = escape_html(hindi_title(job.get("title", "Latest Update")))

    slug = generate_slug(title)

    description = generate_meta_description(job)

    image = get_image(job)

    # Relative image ko absolute bana do
    if not image.startswith("http"):
        image = f"{BASE_URL}/{image.lstrip('/')}"

    canonical = canonical_url(slug)

    publish_date = published_date()

    breadcrumb_items = breadcrumb(job)

    breadcrumb_schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": []
    }

    for index, item in enumerate(
        breadcrumb_items,
        start=1
    ):

        breadcrumb_schema["itemListElement"].append({
            "@type": "ListItem",
            "position": index,
            "name": item["name"],
            "item": item["url"]
        })

    article_schema = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": title,
        "description": description,
        "image": [image],
        "datePublished": publish_date,
        "dateModified": publish_date,
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": canonical
        },
        "author": {
            "@type": "Organization",
            "name": "Education Update Hub"
        },
        "publisher": {
            "@type": "Organization",
            "name": "Education Update Hub",
            "logo": {
                "@type": "ImageObject",
                "url": f"{BASE_URL}/images/logo.png"
            }
        }
    }

    return f"""<!DOCTYPE html>
<html lang="hi">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>{title} | Education Update Hub</title>

<meta name="description"
content="{description}">

<meta name="keywords"
content="{title}, Government Jobs, Sarkari Result, Admit Card, Results, Answer Key, Scholarship">

<meta name="robots"
content="index,follow,max-image-preview:large">

<meta name="author"
content="Education Update Hub">

<link rel="canonical"
href="{canonical}">

<link rel="icon"
href="{BASE_URL}/favicon.ico">

<link rel="stylesheet"
href="../../style.css">

<!-- Google Analytics -->

<script async
src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}">
</script>

<script>
window.dataLayer = window.dataLayer || [];
function gtag(){{dataLayer.push(arguments);}}
gtag('js', new Date());
gtag('config', '{GA4_ID}');
</script>

<!-- Google Adsense -->

<meta name="google-adsense-account"
content="ca-pub-4508009805424675">

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

<meta property="og:locale"
content="hi_IN">

<!-- Twitter -->

<meta name="twitter:card"
content="summary_large_image">

<meta name="twitter:title"
content="{title}">

<meta name="twitter:description"
content="{description}">

<meta name="twitter:image"
content="{image}">

<!-- NewsArticle Schema -->

<script type="application/ld+json">
{json.dumps(article_schema, indent=2)}
</script>

<!-- Breadcrumb Schema -->

<script type="application/ld+json">
{json.dumps(breadcrumb_schema, indent=2)}
</script>

</head>
"""
# ==========================================================
# Part 3 : HTML Body Template
# ==========================================================


def _clean_detail(value):
    if value is None:
        return ""
    value = str(value).strip()
    value = re.sub(r"\s+", " ", value)
    return value.strip(" :-–|,;")


def _detail_source(job):
    parts = []
    for key in ("title", "content", "description", "text", "raw_text", "body"):
        value = job.get(key)
        if value:
            parts.append(str(value))
    return re.sub(r"\s+", " ", " ".join(parts))


def _extract_detail(job, keys, patterns, default="Not Mentioned"):
    for key in keys:
        value = _clean_detail(job.get(key))
        if value:
            return value

    text = _detail_source(job)
    if text:
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                value = _clean_detail(match.group(1))
                if value and len(value) <= 300:
                    return value

    return default


def _job_details(job):
    vacancy = _extract_detail(
        job,
        ("vacancy", "vacancies", "total_vacancies", "total_posts", "posts"),
        (
            r"(?:total\s+)?(?:vacanc(?:y|ies)|posts?)\s*[:\-–]\s*([^|.;]{1,120})",
            r"(?:कुल\s*)?(?:रिक्त\s*पद|पदों\s*की\s*संख्या|पद)\s*[:\-–]\s*([^|.;]{1,120})",
            r"\b(\d{1,5})\s+(?:posts?|vacancies|पद)\b",
        ),
    )
    qualification = _extract_detail(
        job,
        ("qualification", "educational_qualification", "eligibility", "education"),
        (
            r"(?:educational\s+)?qualification\s*[:\-–]\s*([^|.;]{1,220})",
            r"eligibility\s*[:\-–]\s*([^|.;]{1,220})",
            r"(?:शैक्षणिक\s*)?(?:योग्यता|अर्हता)\s*[:\-–]\s*([^|.;]{1,220})",
        ),
        "Check Official Notification",
    )
    salary = _extract_detail(
        job,
        ("salary", "pay_scale", "pay", "remuneration", "salary_details"),
        (
            r"(?:salary|pay\s*scale|remuneration|pay)\s*[:\-–]\s*([^|.;]{1,180})",
            r"(?:वेतन|मानदेय|वेतनमान)\s*[:\-–]\s*([^|.;]{1,180})",
        ),
    )
    last_date = _extract_detail(
        job,
        ("last_date", "deadline", "application_last_date", "last_date_to_apply", "closing_date"),
        (
            r"(?:last\s+date|deadline|closing\s+date|last\s+date\s+to\s+apply)\s*[:\-–]\s*([^|.;]{1,100})",
            r"(?:अंतिम\s*तिथि|अंतिम\s*तारीख|आवेदन\s*की\s*अंतिम\s*तिथि)\s*[:\-–]?\s*([^|.;]{1,100})",
            r"(?:last\s*date|deadline)\s*[:\-–]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        ),
        "Not Available",
    )
    return vacancy, qualification, salary, last_date


def build_html_body(job):

    title = escape_html(hindi_title(job.get("title", "")))

    category = escape_html(
        hindi_category(job.get("category", "नवीनतम सरकारी नौकरियां"))
    )

    department = escape_html(
        job.get("department", "Government")
    )

    vacancy_raw, qualification_raw, salary_raw, last_date_raw = _job_details(job)

    vacancy = escape_html(vacancy_raw)
    qualification = escape_html(qualification_raw)
    salary = escape_html(salary_raw)
    last_date = escape_html(last_date_raw)

    description = escape_html(hindi_summary(job))

    content = ""

    image = get_image(job)

    if not image.startswith("http"):
        image = f"../../{image.lstrip('/')}"

    apply_link = (
        job.get("apply_link")
        or job.get("url")
        or "#"
    )

    notification = (
        job.get("notification_pdf")
        or job.get("url")
        or "#"
    )

    official = (
        job.get("official_website")
        or job.get("url")
        or "#"
    )

    body = f"""
<body>

<div id="header"></div>

<main class="post-wrapper">

<div class="post-container">

<nav class="breadcrumb">

<a href="../../index.html">होम</a>

<span>›</span>

<a href="../../{CATEGORY_PAGES.get(category,'latest-jobs.html')}">

{category}

</a>

<span>›</span>

<span>{title}</span>

</nav>

<h1 class="post-title">

{title}

</h1>

<p class="post-meta">

📅 प्रकाशित :
{published_date()}

&nbsp;&nbsp;|&nbsp;&nbsp;

🏛 {department}

</p>



<p class="post-description">

{description}

</p>

<div class="post-content">

{content.replace(chr(10), "<br>")}

</div>

<h2>📋 भर्ती विवरण</h2>

<table class="job-table">

<tr>
<th>श्रेणी</th>
<td>{category}</td>
</tr>

<tr>
<th>विभाग</th>
<td>{department}</td>
</tr>

<tr>
<th>कुल रिक्तियां</th>
<td>{vacancy}</td>
</tr>

<tr>
<th>शैक्षणिक योग्यता</th>
<td>{qualification}</td>
</tr>

<tr>
<th>वेतनमान</th>
<td>{salary}</td>
</tr>

<tr>
<th>अंतिम तिथि</th>
<td>{last_date}</td>
</tr>

</table>

<div class="post-buttons">

<a
class="apply-btn"
href="{apply_link}"
target="_blank"
rel="noopener">

🚀 ऑनलाइन आवेदन करें

</a>

<a
class="notification-btn"
href="{notification}"
target="_blank"
rel="noopener">

📄 आधिकारिक अधिसूचना डाउनलोड करें

</a>

<a
class="official-btn"
href="{official}"
target="_blank"
rel="noopener">

🌐 आधिकारिक वेबसाइट

</a>

</div>

"""

    return body


# ==========================================================
# Part 4 : FAQ + Share + Related Posts + Footer
# ==========================================================

def build_extra_sections(job):

    title = escape_html(job.get("title", ""))

    apply_link = (
        job.get("apply_link")
        or job.get("url")
        or "#"
    )

    slug = generate_slug(title)

    canonical = canonical_url(slug)

    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": f"{title} क्या है?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": f"{title} से संबंधित आधिकारिक भर्ती/अपडेट की जानकारी यहां दी गई है। योग्यता, महत्वपूर्ण तिथियां और अधिसूचना देखें।"
                }
            },
            {
                "@type": "Question",
                "name": "आवेदन कैसे करें?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "ऊपर दिए गए ऑनलाइन आवेदन बटन पर क्लिक करके आधिकारिक वेबसाइट से आवेदन पूरा करें।"
                }
            },
            {
                "@type": "Question",
                "name": "अधिसूचना कहां से डाउनलोड करें?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "ऊपर दिए गए आधिकारिक अधिसूचना लिंक पर क्लिक करें।"
                }
            }
        ]
    }

    related_html = ""

    posts = sorted(
        OUTPUT_DIR.glob("*.html"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    count = 0

    for post in posts:

        if post.stem == slug:
            continue

        title_text = post.stem.replace("-", " ").title()

        related_html += f"""
<div class="related-card">
    <a href="../../generated/posts/{post.name}">
        <h3>{title_text}</h3>
    </a>
</div>
"""

        count += 1

        if count == 4:
            break

    return f"""
<!-- ================= SHARE ================= -->

<section class="share-section">

<h2>📤 इस अपडेट को साझा करें</h2>

<div class="share-buttons">

<a target="_blank"
rel="noopener"
href="https://wa.me/?text={canonical}">
WhatsApp
</a>

<a target="_blank"
rel="noopener"
href="https://t.me/share/url?url={canonical}">
Telegram
</a>

<a target="_blank"
rel="noopener"
href="https://twitter.com/intent/tweet?url={canonical}">
Twitter
</a>

<a target="_blank"
rel="noopener"
href="https://www.facebook.com/sharer/sharer.php?u={canonical}">
Facebook
</a>

</div>

</section>

<!-- ================= FAQ ================= -->

<section class="faq-section">

<h2>अक्सर पूछे जाने वाले प्रश्न</h2>

<div class="faq-item">

<h3>What is {title}?</h3>

<p>
This page provides complete official information,
eligibility, vacancy, salary,
important dates and application process.
</p>

</div>

<div class="faq-item">

<h3>आवेदन कैसे करें?</h3>

<p>
Click the Apply Online button above
and complete your application from
the official website.
</p>

</div>

<div class="faq-item">

<h3>अधिसूचना कहां से डाउनलोड करें?</h3>

<p>
Use the Download Notification button
available above.
</p>

</div>

</section>

<!-- ================= RELATED POSTS ================= -->

<section class="related-posts">

<h2>🔥 संबंधित अपडेट</h2>

<div class="related-grid">

{related_html}

</div>

</section>

<!-- ================= ACTION BUTTONS ================= -->

<section class="next-action">

<a class="apply-btn"
href="{apply_link}"
target="_blank"
rel="noopener">

🚀 अभी आवेदन करें

</a>

<a class="home-btn"
href="../../index.html">

🏠 होम पर वापस जाएं

</a>

</section>

<div id="footer"></div>

<script src="../../load.js"></script>
<script src="../../menu.js"></script>
<script src="../../script.js"></script>

<script type="application/ld+json">
{json.dumps(faq_schema, indent=2)}
</script>

</body>

</html>
"""
# ==========================================================
# Part 5 : Core HTML Generation Engine
# ==========================================================

def build_html(job):
    return (
        build_html_head(job)
        + build_html_body(job)
        + build_extra_sections(job)
    )


# ==========================================================
# Write HTML File
# ==========================================================

def write_html_file(filename, html_content):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    filepath = OUTPUT_DIR / filename

    with open(
        filepath,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(html_content)

    return filepath


# ==========================================================
# Generate Single Post
# ==========================================================

INVALID_TITLES = {
    "",
    "support",
    "student",
    "results",
    "more",
    "more...",
    "support_agent support",
    "event student",
    "event key dates"
}


def generate_post(job):

    title = str(
        job.get("title", "")
    ).strip()

    category = str(
        job.get("category", "")
    ).strip()

    if (
        not title
        or len(title) < 5
        or title.lower() in INVALID_TITLES
        or category.lower() == "unknown"
    ):
        return None

    slug = generate_slug(title)

    filename = f"{slug}.html"

    html_content = build_html(job)

    filepath = write_html_file(
        filename,
        html_content
    )

    job["slug"] = slug
    job["html_file"] = f"generated/posts/{filename}"

    logger.info(
        "Generated : %s",
        filename
    )

    return filepath


# ==========================================================
# Generate All Posts
# ==========================================================

def generate_all(jobs, category_jobs=None):
    # The same active dataset is used everywhere: posts, category pages and homepage.
    active_jobs = filter_active_jobs(jobs)
    cleanup_stale_generated_posts(jobs, active_jobs)

    generated = []
    failed = 0
    seen = set()

    for job in active_jobs:
        try:
            title = str(job.get("title", "")).strip()
            slug = generate_slug(title)
            if not title or slug in seen:
                failed += 1
                continue

            seen.add(slug)
            filepath = generate_post(job)
            if filepath:
                generated.append(filepath)
            else:
                failed += 1
        except Exception:
            logger.exception("Generation Failed : %s", job.get("title", ""))
            failed += 1

    logger.info("=" * 60)
    logger.info("Active Jobs : %d", len(active_jobs))
    logger.info("Generated  : %d", len(generated))
    logger.info("Failed     : %d", failed)
    logger.info("=" * 60)

    try:
        category_generator.build_categories(active_jobs)
        logger.info("Category Pages Updated Successfully.")
    except Exception:
        logger.exception("Category Generator Failed")

    return {
        "success": len(generated),
        "failed": failed,
        "total": len(active_jobs),
        "results": [
            {"success": True, "file": str(file), "title": Path(file).stem, "slug": Path(file).stem}
            for file in generated
        ]
    }

# ==========================================================
# Verify Generated Files
# ==========================================================

def verify_generated_files():

    html_files = list(
        OUTPUT_DIR.glob("*.html")
    )

    logger.info(
        "Verified %d HTML Files",
        len(html_files)
    )

    return len(html_files)


# ==========================================================
# Clean Output Folder
# ==========================================================

def clean_output_directory():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

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
# Statistics
# ==========================================================

def html_statistics():

    total = len(
        list(
            OUTPUT_DIR.glob("*.html")
        )
    )

    logger.info("=" * 50)
    logger.info("HTML Generator V4.1")
    logger.info("=" * 50)
    logger.info("Generated HTML : %d", total)
    logger.info("Output Folder  : %s", OUTPUT_DIR)
    logger.info("=" * 50)


# ==========================================================
# Build Complete Website
# ==========================================================

def build_site(jobs):

    # Clean the auto-generated post folder first so expired/old HTML files
    # cannot remain visible from a previous run.
    clean_output_directory()

    active_jobs = filter_active_jobs(jobs)

    result = generate_all(active_jobs)

    verify_generated_files()

    # IMPORTANT: Homepage and category generator must use the SAME filtered
    # active dataset; otherwise stale jobs can return to the homepage.
    homepage.run(active_jobs)
    category_generator.run(active_jobs)

    html_statistics()

    logger.info(
        "Website Generated Successfully."
    )

    return result


logger.info(
    "HTML Generator V4.1 Loaded Successfully."
)
