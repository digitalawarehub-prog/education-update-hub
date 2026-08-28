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
from url_utils import slugify as canonical_slug

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


def generate_slug(title, job=None):
    """Generate a filesystem-safe, bounded slug shared with url_utils.

    Long scraped notice titles previously produced >255-character filenames
    and crashed the cleanup stage with OSError: [Errno 36].
    """
    return canonical_slug(title, job or {})


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
    # Never generate a post from a source page that returned 404/unavailable.
    if job.get("fetch_error"):
        return False
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
    """Remove generated files not represented by the current active dataset."""
    active_slugs = {generate_slug(str(j.get("title", ""))) for j in active_jobs if j.get("title")}
    existing = list(OUTPUT_DIR.glob("*.html"))
    removed = 0
    failed = 0
    for path in existing:
        if path.stem in active_slugs:
            continue
        try:
            path.unlink()
            removed += 1
        except OSError as exc:
            failed += 1
            logger.warning("Unable to remove stale post: %s | %s", path.name, exc)
    logger.info("STALE POST CLEANUP | Existing=%d | Active=%d | Removed=%d | Failed=%d", len(existing), len(active_slugs), removed, failed)
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
    "other state jobs":"अन्य राज्य सरकारी नौकरियां","government schemes":"सरकारी योजनाएं","government scheme":"सरकारी योजना",
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


# Common English -> Hindi phrases used in scraped job fields.
# Proper organization names are intentionally kept where a reliable Hindi
# equivalent is not available; common descriptive text is translated.
VALUE_REPLACEMENTS = [
    ("Check Official Notification", "आधिकारिक अधिसूचना देखें"),
    ("Check Notification", "अधिसूचना देखें"),
    ("Not Mentioned", "उल्लेख नहीं किया गया"),
    ("Not Available", "उपलब्ध नहीं"),
    ("Government", "सरकारी विभाग"),
    ("Government of India", "भारत सरकार"),
    ("Central Government", "केंद्र सरकार"),
    ("State Government", "राज्य सरकार"),
    ("Department", "विभाग"),
    ("Recruitment", "भर्ती"),
    ("Recruitment Details", "भर्ती विवरण"),
    ("Application Form", "आवेदन पत्र"),
    ("Online Application", "ऑनलाइन आवेदन"),
    ("Apply Online", "ऑनलाइन आवेदन"),
    ("Application", "आवेदन"),
    ("Last Date to Apply", "आवेदन की अंतिम तिथि"),
    ("Last Date", "अंतिम तिथि"),
    ("Closing Date", "अंतिम तिथि"),
    ("Deadline", "अंतिम तिथि"),
    ("Qualification", "शैक्षणिक योग्यता"),
    ("Educational Qualification", "शैक्षणिक योग्यता"),
    ("Eligibility", "पात्रता"),
    ("Eligible", "पात्र"),
    ("Vacancy", "रिक्ति"),
    ("Vacancies", "रिक्तियां"),
    ("Total Posts", "कुल पद"),
    ("Posts", "पद"),
    ("Post", "पद"),
    ("Salary", "वेतन"),
    ("Pay Scale", "वेतनमान"),
    ("Pay Level", "वेतन स्तर"),
    ("Remuneration", "मानदेय"),
    ("Per Month", "प्रति माह"),
    ("Monthly", "मासिक"),
    ("Selection Process", "चयन प्रक्रिया"),
    ("Selection", "चयन"),
    ("Written Exam", "लिखित परीक्षा"),
    ("Computer Based Test", "कंप्यूटर आधारित परीक्षा"),
    ("Interview", "साक्षात्कार"),
    ("Document Verification", "दस्तावेज सत्यापन"),
    ("Age Limit", "आयु सीमा"),
    ("Experience", "अनुभव"),
    ("No Experience", "कोई अनुभव आवश्यक नहीं"),
    ("Years", "वर्ष"),
    ("Year", "वर्ष"),
    ("Month", "माह"),
    ("Months", "माह"),
    ("Days", "दिन"),
    ("Day", "दिन"),
    ("Full Time", "पूर्णकालिक"),
    ("Part Time", "अंशकालिक"),
    ("Permanent", "स्थायी"),
    ("Temporary", "अस्थायी"),
    ("Contract", "संविदात्मक"),
    ("Male", "पुरुष"),
    ("Female", "महिला"),
    ("Both", "दोनों"),
    ("Any Degree", "कोई भी स्नातक डिग्री"),
    ("Graduate", "स्नातक"),
    ("Graduation", "स्नातक"),
    ("Post Graduate", "स्नातकोत्तर"),
    ("Post Graduation", "स्नातकोत्तर"),
    ("Master Degree", "स्नातकोत्तर डिग्री"),
    ("Bachelor Degree", "स्नातक डिग्री"),
    ("Diploma", "डिप्लोमा"),
    ("Intermediate", "इंटरमीडिएट"),
    ("12th", "कक्षा 12वीं"),
    ("10th", "कक्षा 10वीं"),
    ("High School", "हाई स्कूल"),
    ("Class 12", "कक्षा 12वीं"),
    ("Class 10", "कक्षा 10वीं"),
    ("Recognized University", "मान्यता प्राप्त विश्वविद्यालय"),
    ("Recognised University", "मान्यता प्राप्त विश्वविद्यालय"),
    ("Recognized Board", "मान्यता प्राप्त बोर्ड"),
    ("As per", "के अनुसार"),
    ("According to", "के अनुसार"),
    ("Candidates", "अभ्यर्थी"),
    ("Candidate", "अभ्यर्थी"),
    ("Interested Candidates", "इच्छुक अभ्यर्थी"),
    ("Official Website", "आधिकारिक वेबसाइट"),
    ("Official Notification", "आधिकारिक अधिसूचना"),
    ("Notification", "अधिसूचना"),
    ("Result", "परिणाम"),
    ("Results", "परिणाम"),
    ("Answer Key", "उत्तर कुंजी"),
    ("Admit Card", "प्रवेश पत्र"),
    ("Exam", "परीक्षा"),
    ("Examination", "परीक्षा"),
    ("Selection List", "चयन सूची"),
    ("Merit List", "मेरिट सूची"),
    ("Counselling", "काउंसलिंग"),
    ("Counseling", "काउंसलिंग"),
    ("Medical Examination", "चिकित्सा परीक्षा"),
    ("Fee", "शुल्क"),
    ("Application Fee", "आवेदन शुल्क"),
    ("General", "सामान्य"),
    ("OBC", "अन्य पिछड़ा वर्ग"),
    ("SC", "अनुसूचित जाति"),
    ("ST", "अनुसूचित जनजाति"),
    ("EWS", "आर्थिक रूप से कमजोर वर्ग"),
    ("PwD", "दिव्यांग"),
    ("UR", "अनारक्षित"),
    ("State", "राज्य"),
    ("District", "जिला"),
    ("Location", "स्थान"),
    ("Job Location", "नौकरी का स्थान"),
    ("Online", "ऑनलाइन"),
    ("Offline", "ऑफलाइन"),
    ("Important Dates", "महत्वपूर्ण तिथियां"),
    ("Important Date", "महत्वपूर्ण तिथि"),
    ("Notification Date", "अधिसूचना जारी होने की तिथि"),
    ("Start Date", "प्रारंभ तिथि"),
    ("Starting Date", "प्रारंभ तिथि"),
    ("Application Start Date", "आवेदन प्रारंभ तिथि"),
    ("Application Last Date", "आवेदन की अंतिम तिथि"),
]

def hindi_value(value, default="उपलब्ध नहीं"):
    text = str(value or "").strip()
    if not text:
        return default

    low = text.lower()
    if low in {
        "not mentioned", "not available", "n/a", "na", "none",
        "null", "check official notification", "check notification"
    }:
        return default

    # Long phrases first so that smaller replacements do not interfere.
    replacements = sorted(
        VALUE_REPLACEMENTS,
        key=lambda item: len(item[0]),
        reverse=True
    )

    for old, new in replacements:
        text = re.sub(
            rf"(?<![A-Za-z]){re.escape(old)}(?![A-Za-z])",
            new,
            text,
            flags=re.IGNORECASE
        )

    # Common field punctuation/phrases left by scrapers.
    text = re.sub(r"\bper\s+annum\b", "प्रति वर्ष", text, flags=re.I)
    text = re.sub(r"\bper\s+year\b", "प्रति वर्ष", text, flags=re.I)
    text = re.sub(r"\bmonths?\b", "माह", text, flags=re.I)
    text = re.sub(r"\byears?\b", "वर्ष", text, flags=re.I)
    text = re.sub(r"\bposts?\b", "पद", text, flags=re.I)
    text = re.sub(r"\bvacancies\b", "रिक्तियां", text, flags=re.I)
    text = re.sub(r"\bvacancy\b", "रिक्ति", text, flags=re.I)

    return text.strip() or default


def hindi_detail(value, default="अधिसूचना देखें"):
    return hindi_value(value, default)


def hindi_department(value):
    return hindi_value(value, "सरकारी विभाग")



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


def _clean_publish_detail(value, field=""):
    """Return only a complete, useful detail; reject OCR/menu fragments."""
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    text = re.sub(r"^[\s=.:;,_|/\\\-–—•·]+", "", text)
    text = re.sub(r"\s*[=.:;,_|/\\]+\s*$", "", text).strip()
    if not text:
        return ""
    low = text.casefold()
    bad = {
        "not mentioned", "not available", "n/a", "na", "none", "null",
        "check official notification", "check notification", "as per rules",
        "official notification", ".", "-", "=",
    }
    if low in bad:
        return ""
    # Typical OCR fragments from lists/navigation/PDF page furniture.
    bad_fragments = (
        "slips, etc", "go to index", "previous button", "app store google play",
        "stipulated dates before registering", "candidates are warned", "page no.-",
        "page no.", "page no", "step-1", "step 1:", "misconduct", "the page you requested",
        "candidates are warned", "examination will be conducted",
    )
    if any(x in low for x in bad_fragments):
        return ""
    if field == "qualification" and len(text) < 12:
        return ""
    # If the extracted sentence clearly ends on a connector, it is incomplete.
    trailing = ("and", "or", "of", "with", "for", "to", "the", "के", "की", "का", "में", "से", "हेतु", "तथा", "और", "या")
    words = re.findall(r"[A-Za-zÀ-ÿ]+|[\u0900-\u097F]+", low)
    if words and words[-1] in trailing:
        return ""
    # A value consisting almost entirely of punctuation/symbols is unusable.
    alnum = len(re.findall(r"[A-Za-z0-9\u0900-\u097F]", text))
    if alnum < 2:
        return ""
    return text


def _detail_rows_html(job, vacancy, qualification, salary, last_date):
    rows = []
    fields = [
        ("श्रेणी", hindi_category(job.get("category", "नवीनतम सरकारी नौकरियां")), "category"),
        ("विभाग", hindi_department(job.get("department", "Government")), "department"),
        ("कुल रिक्तियां", hindi_detail(vacancy, ""), "vacancy"),
        ("शैक्षणिक योग्यता", hindi_detail(qualification, ""), "qualification"),
        ("वेतनमान", hindi_detail(salary, ""), "salary"),
        ("आयु सीमा", hindi_detail(job.get("age_limit", ""), ""), "age_limit"),
        ("आवेदन शुल्क", hindi_detail(job.get("application_fee", ""), ""), "application_fee"),
        ("चयन प्रक्रिया", hindi_detail(job.get("selection_process", ""), ""), "selection_process"),
        ("परीक्षा तिथि", hindi_detail(job.get("exam_date", ""), ""), "exam_date"),
        ("आवेदन प्रारंभ", hindi_detail(job.get("application_start_date", ""), ""), "application_start_date"),
        ("अंतिम तिथि", hindi_detail(last_date, ""), "last_date"),
    ]
    for label, value, field in fields:
        cleaned = _clean_publish_detail(value, field)
        if not cleaned:
            continue
        rows.append(f"<tr>\n<th>{escape_html(label)}</th>\n<td>{escape_html(cleaned)}</td>\n</tr>")
    return "\n".join(rows)


def _safe_link(value, allow_pdf=True):
    value = str(value or "").strip()
    if not re.match(r"^https?://", value, re.I):
        return ""
    if not allow_pdf and re.search(r"\.pdf(?:$|[?#])", value, re.I):
        return ""
    return value


def _action_buttons_html(job):
    ptype = str(job.get("post_type") or job.get("category") or "").strip().casefold()
    apply_link = _safe_link(job.get("apply_link"), allow_pdf=False)
    notification = _safe_link(job.get("notification_pdf") or job.get("official_notification_pdf"), allow_pdf=True)
    official = _safe_link(job.get("official_website"), allow_pdf=False) or _safe_link(job.get("url"), allow_pdf=False)
    if apply_link and notification and apply_link.rstrip("/") == notification.rstrip("/"):
        apply_link = ""
    if official and notification and official.rstrip("/") == notification.rstrip("/"):
        official = ""
    # Never render duplicate buttons pointing to exactly the same URL.
    buttons = []
    seen = set()
    def add_button(css, href, text):
        if not href or href in seen:
            return
        seen.add(href)
        buttons.append(f'<a class="{css}" href="{escape_html(href)}" target="_blank" rel="noopener">{text}</a>')

    if ptype in {"government-scheme", "government scheme", "scheme"} or "scheme" in ptype or "yojana" in ptype:
        add_button("official-btn", official, "🌐 योजना की आधिकारिक जानकारी")
        if notification:
            add_button("notification-btn", notification, "📄 योजना की अधिसूचना देखें")
        return "\n".join(buttons)
    if ptype in {"result", "results"}:
        add_button("apply-btn", apply_link or official, "📊 परिणाम देखें")
        add_button("notification-btn", notification, "📄 आधिकारिक अधिसूचना")
        add_button("official-btn", official, "🌐 आधिकारिक वेबसाइट")
        return "\n".join(buttons)
    if ptype in {"admit-card", "admit card"}:
        add_button("apply-btn", apply_link or official, "🎫 एडमिट कार्ड डाउनलोड करें")
        add_button("notification-btn", notification, "📄 आधिकारिक सूचना")
        add_button("official-btn", official, "🌐 आधिकारिक वेबसाइट")
        return "\n".join(buttons)
    if ptype in {"answer-key", "answer key"}:
        add_button("apply-btn", apply_link or official, "🔑 उत्तर कुंजी देखें")
        add_button("notification-btn", notification, "📄 आधिकारिक सूचना")
        add_button("official-btn", official, "🌐 आधिकारिक वेबसाइट")
        return "\n".join(buttons)
    if ptype in {"scholarship"}:
        add_button("apply-btn", apply_link or official, "🎓 छात्रवृत्ति की जानकारी देखें")
        add_button("official-btn", official, "🌐 आधिकारिक वेबसाइट")
        return "\n".join(buttons)
    # Recruitment/default: show Apply only when a real application link exists.
    add_button("apply-btn", apply_link, "🚀 ऑनलाइन आवेदन करें")
    add_button("notification-btn", notification, "📄 आधिकारिक अधिसूचना डाउनलोड करें")
    add_button("official-btn", official, "🌐 आधिकारिक वेबसाइट")
    return "\n".join(buttons)


def build_html_body(job):

    title = escape_html(hindi_title(job.get("title", "")))

    category = escape_html(
        hindi_category(job.get("category", "नवीनतम सरकारी नौकरियां"))
    )

    department = escape_html(
        hindi_department(job.get("department", "Government"))
    )

    vacancy_raw, qualification_raw, salary_raw, last_date_raw = _job_details(job)

    vacancy = escape_html(
        hindi_detail(vacancy_raw, "अधिसूचना में देखें")
    )
    qualification = escape_html(
        hindi_detail(qualification_raw, "आधिकारिक अधिसूचना में देखें")
    )
    salary = escape_html(
        hindi_detail(salary_raw, "अधिसूचना में देखें")
    )
    last_date = escape_html(
        hindi_detail(last_date_raw, "उपलब्ध नहीं")
    )

    description = escape_html(hindi_summary(job))

    content = ""


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

{_detail_rows_html(job, vacancy_raw, qualification_raw, salary_raw, last_date_raw)}

</table>

<div class="post-buttons">
{_action_buttons_html(job)}
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

    ptype = str(job.get("post_type") or job.get("category") or "").strip().casefold()
    scheme_mode = ptype in {"government-scheme", "government scheme", "scheme"} or "scheme" in ptype or "yojana" in ptype
    first_answer = (f"{title} से संबंधित सरकारी योजना की आधिकारिक जानकारी, पात्रता और लाभ यहां दिए गए हैं।" if scheme_mode else f"{title} से संबंधित आधिकारिक अपडेट की जानकारी यहां दी गई है। महत्वपूर्ण विवरण और आधिकारिक स्रोत देखें।")
    second_question = "योजना की जानकारी कहां से देखें?" if scheme_mode else "आवेदन कैसे करें?"
    second_answer = ("ऊपर दिए गए आधिकारिक योजना लिंक से संबंधित जानकारी देखें।" if scheme_mode else "यदि आवेदन लिंक उपलब्ध है तो ऊपर दिए गए ऑनलाइन आवेदन बटन से आवेदन करें; अन्यथा आधिकारिक वेबसाइट देखें।")
    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": f"{title} क्या है?", "acceptedAnswer": {"@type": "Answer", "text": first_answer}},
            {"@type": "Question", "name": second_question, "acceptedAnswer": {"@type": "Answer", "text": second_answer}},
            {"@type": "Question", "name": "आधिकारिक जानकारी कहां मिलेगी?", "acceptedAnswer": {"@type": "Answer", "text": "ऊपर उपलब्ध आधिकारिक लिंक का उपयोग करें।"}}
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
<a href="../../index.html" class="home-btn">

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

    slug = generate_slug(title, job)

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
            slug = generate_slug(title, job)
            if not title:
                failed += 1
                logger.warning("Generation skipped: empty title")
                continue

            # The canonical slug includes job_id/source URL. This prevents
            # unrelated notices with the same title from being discarded.
            if slug in seen:
                import hashlib
                unique_key = str(job.get("url") or job.get("source_url") or job.get("job_id") or title)
                suffix = hashlib.sha1(unique_key.encode("utf-8")).hexdigest()[:8]
                slug = f"{slug[:140].rstrip('-')}-{suffix}"
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
