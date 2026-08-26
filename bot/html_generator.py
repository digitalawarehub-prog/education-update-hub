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
from url_utils import slugify as canonical_slug, post_site_url

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


ENGLISH_SLUG_MAP = {"सरकारी":"government","नौकरी":"job","नौकरियां":"jobs","भर्ती":"recruitment","भर्तियां":"recruitments","रिक्ति":"vacancy","रिक्तियां":"vacancies","अधिसूचना":"notification","प्रवेश":"admit","पत्र":"card","परिणाम":"result","उत्तर":"answer","कुंजी":"key","छात्रवृत्ति":"scholarship","परीक्षा":"exam","पाठ्यक्रम":"syllabus","शिक्षक":"teacher","पुलिस":"police","वन":"forest","विभाग":"department","केंद्र":"central","राज्य":"state","उत्तराखंड":"uttarakhand","ऑनलाइन":"online","आवेदन":"application","अंतिम":"last","तिथि":"date"}

def generate_slug(title, job=None):
    """Use one collision-resistant slug algorithm everywhere in the site."""
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
    m=re.match(r"^(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})[T ]", text)
    if m:
        try:return datetime(int(m.group(1)),int(m.group(2)),int(m.group(3))).date()
        except ValueError:pass
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
    deadline=_deadline(job)
    today=datetime.now(TIMEZONE).date()

    # 1) An explicit deadline is the strongest signal.
    #    A future/today deadline stays active; an expired deadline does not.
    if deadline:
        return deadline >= today

    # 2) Current-year records can still be valid even when the source
    #    did not expose a separate last-date field. This is important for
    #    the existing database: Fresh=0 does NOT mean all database jobs are old.
    year=_year_in_record(job)
    if year:
        if year < today.year:
            return False
        if year == today.year:
            return True

    # 3) Scraper timestamp is important for admit-card/result notices where
    #    no application deadline exists.
    for key in ("scraped_at", "publish_date", "published_date", "date_published", "posted_date", "notification_date", "date"):
        raw = job.get(key)
        if raw:
            dt = _parse_date(raw)
            if dt:
                return dt >= today-timedelta(days=90)

    # 4) If publication date is available, retain reasonably recent updates.
    pub=_publication_date(job)
    if pub:
        return pub >= today-timedelta(days=120)

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
        "ACTIVE JOB FILTER | Input=%d | Active=%d | Removed=%d | Noise=%d | Expired/Old/No-date=%d",
        len(jobs),len(active),len(jobs)-len(active),noise,stale
    )
    return active


def filter_public_jobs(jobs):
    """Keep all real posts for the archive/category/homepage.

    Expired applications are intentionally NOT deleted from the website; only
    the Latest Jobs category filters them out by application deadline.
    """
    public = []
    removed = 0
    for job in jobs or []:
        title = str(job.get("title", "")).strip()
        category = str(job.get("category", "")).strip().lower()
        if (not title or title.lower() in NOISE_TITLES or category == "unknown" or
                job.get("is_valid_post") is False):
            removed += 1
            continue
        public.append(job)
    logger.info("PUBLIC POST FILTER | Input=%d | Public=%d | Removed=%d", len(jobs or []), len(public), removed)
    return public

# ==========================================================
# Remove Stale Auto-Generated Posts
# ==========================================================

def cleanup_stale_generated_posts(all_jobs, active_jobs):
    active_slugs = {generate_slug(str(j.get("title", "")), j) for j in active_jobs if j.get("title")}
    stale_slugs = set()
    for job in all_jobs:
        title = str(job.get("title", "")).strip()
        if title:
            slug = generate_slug(title, job)
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


# ==========================================================
# Language-aware post content
# ==========================================================

LANGUAGE_LABELS = {
    "en": {
        "home":"Home", "published":"Published", "details":"Recruitment Details", "category":"Category",
        "department":"Department", "vacancy":"Number of Posts", "qualification":"Educational Qualification",
        "salary":"Salary / Pay Scale", "age_limit":"Age Limit", "application_fee":"Application Fee",
        "selection_process":"Selection Process", "exam_date":"Exam Date", "application_start_date":"Application Start",
        "last_date":"Last Date", "apply":"Apply Online", "notification":"Official Notification",
        "official":"Official Website", "not_available":"Not Available", "check_notification":"Check Official Notification",
    },
    "hi": {
        "home":"होम", "published":"प्रकाशित", "details":"भर्ती विवरण", "category":"श्रेणी",
        "department":"विभाग", "vacancy":"पदों की संख्या", "qualification":"शैक्षणिक योग्यता",
        "salary":"वेतनमान", "age_limit":"आयु सीमा", "application_fee":"आवेदन शुल्क", "selection_process":"चयन प्रक्रिया", "exam_date":"परीक्षा तिथि", "application_start_date":"आवेदन प्रारंभ", "last_date":"अंतिम तिथि", "apply":"ऑनलाइन आवेदन करें",
        "notification":"आधिकारिक अधिसूचना डाउनलोड करें", "official":"आधिकारिक वेबसाइट",
        "not_available":"उपलब्ध नहीं", "check_notification":"आधिकारिक अधिसूचना देखें",
    },
    "ta": {
        "home":"முகப்பு", "published":"வெளியிடப்பட்டது", "details":"ஆட்சேர்ப்பு விவரங்கள்", "category":"வகை",
        "department":"துறை", "vacancy":"காலியிடங்கள்", "qualification":"கல்வித் தகுதி",
        "salary":"சம்பளம்", "last_date":"கடைசி தேதி", "apply":"ஆன்லைனில் விண்ணப்பிக்கவும்",
        "notification":"அதிகாரப்பூர்வ அறிவிப்பைப் பதிவிறக்கவும்", "official":"அதிகாரப்பூர்வ இணையதளம்",
        "not_available":"கிடைக்கவில்லை", "check_notification":"அதிகாரப்பூர்வ அறிவிப்பைப் பார்க்கவும்",
    },
    "te": {
        "home":"హోమ్", "published":"ప్రచురణ తేదీ", "details":"నియామక వివరాలు", "category":"వర్గం",
        "department":"శాఖ", "vacancy":"ఖాళీల సంఖ్య", "qualification":"విద్యార్హత",
        "salary":"వేతనం", "last_date":"చివరి తేదీ", "apply":"ఆన్‌లైన్‌లో దరఖాస్తు చేయండి",
        "notification":"అధికారిక నోటిఫికేషన్ డౌన్‌లోడ్ చేయండి", "official":"అధికారిక వెబ్‌సైట్",
        "not_available":"అందుబాటులో లేదు", "check_notification":"అధికారిక నోటిఫికేషన్ చూడండి",
    },
    "bn": {
        "home":"হোম", "published":"প্রকাশিত", "details":"নিয়োগের বিবরণ", "category":"বিভাগ",
        "department":"দপ্তর", "vacancy":"শূন্যপদ", "qualification":"শিক্ষাগত যোগ্যতা",
        "salary":"বেতন", "last_date":"শেষ তারিখ", "apply":"অনলাইনে আবেদন করুন",
        "notification":"অফিসিয়াল বিজ্ঞপ্তি ডাউনলোড করুন", "official":"অফিসিয়াল ওয়েবসাইট",
        "not_available":"উপলব্ধ নয়", "check_notification":"অফিসিয়াল বিজ্ঞপ্তি দেখুন",
    },
    "gu": {
        "home":"હોમ", "published":"પ્રકાશિત", "details":"ભરતીની વિગતો", "category":"શ્રેણી",
        "department":"વિભાગ", "vacancy":"ખાલી જગ્યાઓ", "qualification":"શૈક્ષણિક લાયકાત",
        "salary":"પગાર", "last_date":"છેલ્લી તારીખ", "apply":"ઓનલાઇન અરજી કરો",
        "notification":"સત્તાવાર સૂચના ડાઉનલોડ કરો", "official":"સત્તાવાર વેબસાઇટ",
        "not_available":"ઉપલબ્ધ નથી", "check_notification":"સત્તાવાર સૂચના જુઓ",
    },
    "kn": {
        "home":"ಮುಖಪುಟ", "published":"ಪ್ರಕಟಿಸಲಾಗಿದೆ", "details":"ನೇಮಕಾತಿ ವಿವರಗಳು", "category":"ವರ್ಗ",
        "department":"ಇಲಾಖೆ", "vacancy":"ಖಾಲಿ ಹುದ್ದೆಗಳು", "qualification":"ಶೈಕ್ಷಣಿಕ ಅರ್ಹತೆ",
        "salary":"ವೇತನ", "last_date":"ಕೊನೆಯ ದಿನಾಂಕ", "apply":"ಆನ್‌ಲೈನ್‌ನಲ್ಲಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ",
        "notification":"ಅಧಿಕೃತ ಅಧಿಸೂಚನೆ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ", "official":"ಅಧಿಕೃತ ವೆಬ್‌ಸೈಟ್",
        "not_available":"ಲಭ್ಯವಿಲ್ಲ", "check_notification":"ಅಧಿಕೃತ ಅಧಿಸೂಚನೆಯನ್ನು ನೋಡಿ",
    },
    "ml": {
        "home":"ഹോം", "published":"പ്രസിദ്ധീകരിച്ചത്", "details":"റിക്രൂട്ട്മെന്റ് വിശദാംശങ്ങൾ", "category":"വിഭാഗം",
        "department":"വകുപ്പ്", "vacancy":"ഒഴിവുകൾ", "qualification":"വിദ്യാഭ്യാസ യോഗ്യത",
        "salary":"ശമ്പളം", "last_date":"അവസാന തീയതി", "apply":"ഓൺലൈനായി അപേക്ഷിക്കുക",
        "notification":"ഔദ്യോഗിക വിജ്ഞാപനം ഡൗൺലോഡ് ചെയ്യുക", "official":"ഔദ്യോഗിക വെബ്സൈറ്റ്",
        "not_available":"ലഭ്യമല്ല", "check_notification":"ഔദ്യോഗിക വിജ്ഞാപനം കാണുക",
    },
    "mr": {
        "home":"मुख्यपृष्ठ", "published":"प्रकाशित", "details":"भरतीचा तपशील", "category":"श्रेणी",
        "department":"विभाग", "vacancy":"रिक्त पदे", "qualification":"शैक्षणिक पात्रता",
        "salary":"वेतन", "last_date":"अंतिम तारीख", "apply":"ऑनलाइन अर्ज करा",
        "notification":"अधिकृत अधिसूचना डाउनलोड करा", "official":"अधिकृत वेबसाइट",
        "not_available":"उपलब्ध नाही", "check_notification":"अधिकृत अधिसूचना पहा",
    },
    "pa": {
        "home":"ਮੁੱਖ ਪੰਨਾ", "published":"ਪ੍ਰਕਾਸ਼ਿਤ", "details":"ਭਰਤੀ ਵੇਰਵੇ", "category":"ਸ਼੍ਰੇਣੀ",
        "department":"ਵਿਭਾਗ", "vacancy":"ਖਾਲੀ ਅਸਾਮੀਆਂ", "qualification":"ਵਿਦਿਅਕ ਯੋਗਤਾ",
        "salary":"ਤਨਖਾਹ", "last_date":"ਆਖਰੀ ਮਿਤੀ", "apply":"ਆਨਲਾਈਨ ਅਰਜ਼ੀ ਦਿਓ",
        "notification":"ਅਧਿਕਾਰਤ ਨੋਟੀਫਿਕੇਸ਼ਨ ਡਾਊਨਲੋਡ ਕਰੋ", "official":"ਅਧਿਕਾਰਤ ਵੈੱਬਸਾਈਟ",
        "not_available":"ਉਪਲਬਧ ਨਹੀਂ", "check_notification":"ਅਧਿਕਾਰਤ ਨੋਟੀਫਿਕੇਸ਼ਨ ਵੇਖੋ",
    },
    "or": {
        "home":"ମୂଳପୃଷ୍ଠା", "published":"ପ୍ରକାଶିତ", "details":"ନିଯୁକ୍ତି ବିବରଣୀ", "category":"ଶ୍ରେଣୀ",
        "department":"ବିଭାଗ", "vacancy":"ଖାଲି ପଦବୀ", "qualification":"ଶିକ୍ଷାଗତ ଯୋଗ୍ୟତା",
        "salary":"ବେତନ", "last_date":"ଶେଷ ତାରିଖ", "apply":"ଅନଲାଇନରେ ଆବେଦନ କରନ୍ତୁ",
        "notification":"ଅଧିକାରିକ ବିଜ୍ଞପ୍ତି ଡାଉନଲୋଡ୍ କରନ୍ତୁ", "official":"ଅଧିକାରିକ ୱେବସାଇଟ୍",
        "not_available":"ଉପଲବ୍ଧ ନାହିଁ", "check_notification":"ଅଧିକାରିକ ବିଜ୍ଞପ୍ତି ଦେଖନ୍ତୁ",
    },
}

SCRIPT_RANGES = {
    "hi": re.compile(r"[\u0900-\u097F]"),
    "bn": re.compile(r"[\u0980-\u09FF]"),
    "gu": re.compile(r"[\u0A80-\u0AFF]"),
    "pa": re.compile(r"[\u0A00-\u0A7F]"),
    "or": re.compile(r"[\u0B00-\u0B7F]"),
    "ta": re.compile(r"[\u0B80-\u0BFF]"),
    "te": re.compile(r"[\u0C00-\u0C7F]"),
    "kn": re.compile(r"[\u0C80-\u0CFF]"),
    "ml": re.compile(r"[\u0D00-\u0D7F]"),
}

# Common English phrases used in scraped fields. These are deliberately
# conservative so organization names, qualifications and numeric data are not damaged.
EN_HI_VALUE_MAP = {
    "government":"सरकारी विभाग", "government of india":"भारत सरकार", "central government":"केंद्र सरकार",
    "state government":"राज्य सरकार", "department":"विभाग", "recruitment":"भर्ती", "application":"आवेदन",
    "online application":"ऑनलाइन आवेदन", "apply online":"ऑनलाइन आवेदन", "last date to apply":"आवेदन की अंतिम तिथि",
    "last date":"अंतिम तिथि", "deadline":"अंतिम तिथि", "closing date":"अंतिम तिथि", "qualification":"शैक्षणिक योग्यता",
    "educational qualification":"शैक्षणिक योग्यता", "eligibility":"पात्रता", "vacancy":"रिक्ति", "vacancies":"रिक्तियां",
    "total posts":"कुल पद", "posts":"पद", "post":"पद", "salary":"वेतन", "pay scale":"वेतनमान",
    "pay level":"वेतन स्तर", "remuneration":"मानदेय", "selection process":"चयन प्रक्रिया", "selection":"चयन",
    "written exam":"लिखित परीक्षा", "computer based test":"कंप्यूटर आधारित परीक्षा", "interview":"साक्षात्कार",
    "document verification":"दस्तावेज सत्यापन", "age limit":"आयु सीमा", "experience":"अनुभव", "years":"वर्ष",
    "year":"वर्ष", "months":"माह", "month":"माह", "days":"दिन", "day":"दिन", "graduate":"स्नातक",
    "graduation":"स्नातक", "post graduate":"स्नातकोत्तर", "post graduation":"स्नातकोत्तर", "diploma":"डिप्लोमा",
    "intermediate":"इंटरमीडिएट", "high school":"हाई स्कूल", "recognized university":"मान्यता प्राप्त विश्वविद्यालय",
    "recognized board":"मान्यता प्राप्त बोर्ड", "candidates":"अभ्यर्थी", "candidate":"अभ्यर्थी", "official website":"आधिकारिक वेबसाइट",
    "official notification":"आधिकारिक अधिसूचना", "notification":"अधिसूचना", "result":"परिणाम", "results":"परिणाम",
    "answer key":"उत्तर कुंजी", "admit card":"प्रवेश पत्र", "exam":"परीक्षा", "examination":"परीक्षा",
    "application fee":"आवेदन शुल्क", "fee":"शुल्क", "general":"सामान्य", "job location":"नौकरी का स्थान",
    "online":"ऑनलाइन", "offline":"ऑफलाइन", "important dates":"महत्वपूर्ण तिथियां", "notification date":"अधिसूचना जारी होने की तिथि",
    "in":"में", "with":"के साथ", "for":"के लिए", "from":"से", "to":"तक", "and":"और", "or":"या",
    "engineering":"इंजीनियरिंग", "technology":"प्रौद्योगिकी", "science":"विज्ञान", "commerce":"वाणिज्य",
    "arts":"कला", "law":"कानून", "medical":"चिकित्सा", "nursing":"नर्सिंग", "pharmacy":"फार्मेसी",
    "computer science":"कंप्यूटर विज्ञान", "information technology":"सूचना प्रौद्योगिकी", "management":"प्रबंधन",
    "administration":"प्रशासन", "finance":"वित्त", "accounting":"लेखांकन", "human resources":"मानव संसाधन",
    "recognized":"मान्यता प्राप्त", "university":"विश्वविद्यालय", "college":"महाविद्यालय", "board":"बोर्ड",
    "minimum":"न्यूनतम", "maximum":"अधिकतम", "required":"आवश्यक", "must":"अनिवार्य", "should":"चाहिए",
    "age":"आयु", "between":"के बीच", "before":"से पहले", "after":"के बाद", "until":"तक", "till":"तक",
    "not mentioned":"उल्लेख नहीं किया गया", "not available":"उपलब्ध नहीं", "check official notification":"आधिकारिक अधिसूचना देखें",
}


def detect_content_language(job):
    """Detect source language without translating it.

    Latin/English content must remain English; an English title with a few
    Hindi words in metadata must not be converted to Hindi.
    """
    text = " ".join(str(job.get(k, "") or "") for k in (
        "notification_text", "notification_content", "content", "description", "summary", "title", "department",
        "qualification", "eligibility", "salary", "last_date"
    ))
    counts = {lang: len(rx.findall(text)) for lang, rx in SCRIPT_RANGES.items()}
    latin = len(re.findall(r"[A-Za-z]", text))
    best = max(counts, key=counts.get) if counts else "hi"
    best_count = counts.get(best, 0)
    if best_count >= 5 and best_count >= latin * 0.35:
        return best
    if latin >= 10:
        return "en"
    if best_count >= 2:
        return best
    return "hi"


def localized_labels(job):
    return LANGUAGE_LABELS.get(detect_content_language(job), LANGUAGE_LABELS["hi"])


def _english_to_hindi(text):
    value = str(text or "")
    for old, new in sorted(EN_HI_VALUE_MAP.items(), key=lambda x: len(x[0]), reverse=True):
        value = re.sub(rf"(?<![A-Za-z]){re.escape(old)}(?![A-Za-z])", new, value, flags=re.I)
    value = re.sub(r"\bper\s+(?:annum|year)\b", "प्रति वर्ष", value, flags=re.I)
    value = re.sub(r"\bmonths?\b", "माह", value, flags=re.I)
    value = re.sub(r"\byears?\b", "वर्ष", value, flags=re.I)
    value = re.sub(r"\bposts?\b", "पद", value, flags=re.I)
    value = re.sub(r"\bvacancies\b", "रिक्तियां", value, flags=re.I)
    return value.strip()


def localize_value(value, job, default):
    text = str(value or "").strip()
    if not text or text.lower() in {"not mentioned", "not available", "n/a", "na", "none", "null"}:
        return default
    lang = detect_content_language(job)
    if lang == "hi":
        return _english_to_hindi(text)
    # English and regional-language notifications keep their original field values.
    # Translation is intentionally disabled.
    if lang != "hi":
        return text
    return text


def localized_title(job):
    # Never translate the source title. The notification language is preserved.
    return str(job.get("title", "Government Update") or "Government Update").strip()


def localized_category(job):
    raw = str(job.get("category", "नवीनतम सरकारी नौकरियां") or "").strip()
    lang = detect_content_language(job)
    if lang == "hi":
        return hindi_category(raw)
    labels = localized_labels(job)
    mapping = {
        "ta":"அரசு வேலைகள்", "te":"ప్రభుత్వ ఉద్యోగాలు", "bn":"সরকারি চাকরি", "gu":"સરકારી નોકરીઓ",
        "kn":"ಸರ್ಕಾರಿ ಉದ್ಯೋಗಗಳು", "ml":"സർക്കാർ ജോലികൾ", "mr":"सरकारी नोकऱ्या", "pa":"ਸਰਕਾਰੀ ਨੌਕਰੀਆਂ", "or":"ସରକାରୀ ଚାକିରି",
    }
    return mapping.get(lang, raw)


def localized_summary(job):
    # Preserve source wording for every language. Do not translate notification text.
    source = str(job.get("description") or job.get("summary") or "").strip()
    source = re.sub(r"\\n+", " ", source)
    source = re.sub(r"\s+", " ", source).strip()
    if source:
        return source
    return str(job.get("title", "Government Update") or "Government Update").strip()

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
    title = localized_title(job)
    deadline = _deadline(job)
    suffix = f" अंतिम तिथि {deadline.strftime('%d-%m-%Y')}।" if deadline else " महत्वपूर्ण तिथियां और आवेदन प्रक्रिया देखें।"
    return (f"{title} भर्ती की पूरी जानकारी, योग्यता, रिक्तियां, वेतन, आवेदन प्रक्रिया और आधिकारिक अधिसूचना की जानकारी यहां देखें।" + suffix)[:160]


def canonical_url(slug):
    return f"{BASE_URL}/generated/posts/{slug}.html"


def published_date(job=None):
    """Return the source/notification date; never use workflow run date for old posts."""
    job = job or {}
    candidates = [
        job.get("notification_date"),
        job.get("publish_date"),
        job.get("published_date"),
        job.get("date_published"),
        job.get("source_date"),
    ]
    text = " ".join(str(job.get(k, "")) for k in ("title", "description", "content"))
    patterns = [
        r"(?:dated|date\s*of\s*advertisement|advertisement\s*dated|notification\s*dated)\s*[:\-–]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"(?:दिनांक|दिनांकित|विज्ञापन\s*दिनांक|अधिसूचना\s*दिनांक)\s*[:\-–]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
    ]
    for value in candidates:
        value = str(value or "").strip()
        if value:
            m = re.search(r"(\d{4})[-/]?(\d{1,2})[-/]?(\d{1,2})", value)
            if m:
                return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
            m = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})", value)
            if m:
                y = int(m.group(3)); y += 2000 if y < 100 else 0
                return f"{y:04d}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    for pattern in patterns:
        m = re.search(pattern, text, re.I)
        if m:
            d, mth, y = re.split(r"[/-]", m.group(1))
            y = int(y); y += 2000 if y < 100 else 0
            return f"{y:04d}-{int(mth):02d}-{int(d):02d}"
    # Fallback only when the source has no date.
    return "Not Available" if detect_content_language(job) == "en" else "उपलब्ध नहीं"


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
                generate_slug(job.get("title", ""), job)
            )
        }
    ]


logger.info("HTML Generator V4.1 Part 1 Loaded Successfully")
# ==========================================================
# Part 2 : HTML Head + SEO + Schema
# ==========================================================

def build_html_head(job):

    title = escape_html(localized_title(job) or "सरकारी अपडेट")

    slug = generate_slug(title, job)

    description = generate_meta_description(job)

    canonical = canonical_url(slug)

    publish_date = published_date(job)

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
<html lang="{detect_content_language(job)}">

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

<!-- NewsArticle Schema -->

<script type="application/ld+json">
{json.dumps(article_schema, indent=2)}
</script>

<!-- Breadcrumb Schema -->

<script type="application/ld+json">
{json.dumps(breadcrumb_schema, indent=2)}
</script>

<style>
/* AUTOMATION POSTS: no photos/images inside post content */
.post-wrapper img, .post-container img, .job-table img, .post-description img {{ display:none !important; }}
</style>
</head>
"""
# ==========================================================
# Part 3 : HTML Body Template
# ==========================================================


def _clean_detail(value):
    if value is None:
        return ""
    value = str(value).strip()
    value = re.sub(r"(?:\\n|\\r|\\t)+", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip(" :-–|,;")


def _detail_source(job):
    """Build a safe detail source from all persisted text fields.

    The database intentionally truncates large HTML/PDF bodies, so description
    and structured fields are also included. The title itself is never used as
    a vacancy/qualification/salary source.
    """
    parts = []
    for key in (
        "notification_text", "notification_content", "content", "raw_text",
        "body", "text", "description", "summary", "eligibility",
        "qualification", "salary", "last_date", "application_fee",
        "selection_process", "exam_date", "application_start_date"
    ):
        value = job.get(key)
        if value:
            value = re.sub(r"(?:\\n|\\r|\\t)+", " ", str(value))
            parts.append(value)
    return re.sub(r"\s+", " ", " ".join(parts)).strip()


_DETAIL_PLACEHOLDERS = {
    "", "-", "—", "n/a", "na", "not available", "not mentioned",
    "official notification", "check official notification",
    "see official notification", "आधिकारिक अधिसूचना देखें",
    "उपलब्ध नहीं", "उपलब्ध नहीं है"
}

def _usable_detail(value, field=None):
    value = _clean_detail(value)
    if not value:
        return False
    low = value.casefold().strip()
    if low in _DETAIL_PLACEHOLDERS:
        return False
    if "आधिकारिक अधिसूचना देखें" in low or "check official notification" in low:
        return False
    if field == "vacancy":
        # Vacancy should contain at least one number. Reject title fragments.
        if not re.search(r"\b\d{1,6}\b", value):
            return False
    return True


def _extract_detail(job, keys, patterns, default="Not Mentioned", field=None):
    for key in keys:
        value = _clean_detail(job.get(key))
        if _usable_detail(value, field):
            return value

    text = _detail_source(job)
    if text:
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                value = _clean_detail(match.group(1))
                if _usable_detail(value, field) and len(value) <= 400:
                    return value

    return default


def _job_details(job):
    vacancy = _extract_detail(job, ("vacancy", "vacancies", "total_vacancies", "total_posts", "posts"),
        (r"(?:total\s+)?(?:number\s+of\s+)?(?:vacanc(?:y|ies)|posts?)\s*[:\-–]?\s*(\d{1,6}(?:\s*[-–]\s*\d{1,6})?)",
         r"(?:कुल\s*)?(?:रिक्त\s*पद|पदों\s*की\s*संख्या|कुल\s*पद|रिक्तियां|रिक्ति)\s*[:\-–]?\s*(\d{1,6})",
         r"\b(\d{1,6})\s+(?:posts?|vacancies|vacant\s+posts?)\b"), "Not Mentioned", "vacancy")
    qualification = _extract_detail(job, ("qualification", "educational_qualification", "eligibility", "education"),
        (r"(?:essential\s+)?(?:educational\s+)?qualification\s*[:\-–]\s*(.{2,320}?)(?=\s+(?:age|experience|salary|pay\s+scale|selection|fee|last\s+date)\b|$)",
         r"eligibility(?:\s+criteria)?\s*[:\-–]\s*(.{2,320}?)(?=\s+(?:age|experience|salary|selection|fee|last\s+date)\b|$)",
         r"(?:शैक्षणिक\s*)?(?:योग्यता|अर्हता)\s*[:\-–]\s*(.{2,320}?)(?=\s+(?:आयु|अनुभव|वेतन|चयन|शुल्क|अंतिम)\b|$)"), "Check Official Notification")
    salary = _extract_detail(job, ("salary", "pay_scale", "pay", "remuneration", "salary_details"),
        (r"(?:salary|pay\s*scale|remuneration|pay\s+level)\s*[:\-–]\s*(.{2,220}?)(?=\s+(?:age|qualification|selection|fee|last\s+date)\b|$)",
         r"(?:वेतन|मानदेय|वेतनमान|पे\s*लेवल)\s*[:\-–]\s*(.{2,220}?)(?=\s+(?:आयु|योग्यता|चयन|शुल्क|अंतिम)\b|$)"))
    age_limit = _extract_detail(job, ("age_limit", "age", "age_criteria"),
        (r"(?:age\s*limit|age\s*criteria)\s*[:\-–]?\s*(.{2,180}?)(?=\s+(?:salary|qualification|experience|fee|selection|last\s+date)\b|$)",
         r"(?:आयु\s*सीमा|उम्र\s*सीमा)\s*[:\-–]?\s*(.{2,180}?)(?=\s+(?:वेतन|योग्यता|अनुभव|शुल्क|चयन|अंतिम)\b|$)"), "Not Available")
    application_fee = _extract_detail(job, ("application_fee", "fee", "exam_fee"),
        (r"(?:application\s+fee|exam(?:ination)?\s+fee|fee)\s*[:\-–]?\s*(.{2,180}?)(?=\s+(?:selection|last\s+date|age|qualification)\b|$)",
         r"(?:आवेदन\s*शुल्क|परीक्षा\s*शुल्क)\s*[:\-–]?\s*(.{2,180}?)(?=\s+(?:चयन|अंतिम|आयु|योग्यता)\b|$)"), "Not Available")
    selection_process = _extract_detail(job, ("selection_process", "selection"),
        (r"(?:selection\s*process|selection\s*procedure)\s*[:\-–]?\s*(.{2,220}?)(?=\s+(?:exam|fee|last\s+date|age|salary)\b|$)",
         r"(?:चयन\s*प्रक्रिया)\s*[:\-–]?\s*(.{2,220}?)(?=\s+(?:परीक्षा|शुल्क|अंतिम|आयु|वेतन)\b|$)"), "Not Available")
    exam_date = _extract_detail(job, ("exam_date", "examination_date"),
        (r"(?:exam(?:ination)?\s+date|date\s+of\s+exam)\s*[:\-–]?\s*(.{2,100}?)(?=\s+(?:exam|fee|last\s+date|age)\b|$)",
         r"(?:परीक्षा\s*तिथि|परीक्षा\s*दिनांक)\s*[:\-–]?\s*(.{2,100}?)(?=\s+(?:शुल्क|अंतिम|आयु)\b|$)"), "Not Available")
    application_start_date = _extract_detail(job, ("application_start_date", "start_date", "application_date"),
        (r"(?:commencement\s+of\s+(?:online\s+)?registration|application\s+start\s+date|start\s+date)\s*[:\-–]?\s*(.{2,100}?)(?=\s+(?:closure|last\s+date|deadline|exam)\b|$)",
         r"(?:आवेदन\s*प्रारंभ|आवेदन\s*आरंभ\s*तिथि)\s*[:\-–]?\s*(.{2,100}?)(?=\s+(?:अंतिम|परीक्षा)\b|$)"), "Not Available")
    last_date = _extract_detail(job, ("last_date", "deadline", "application_last_date", "last_date_to_apply", "closing_date"),
        (r"(?:closure\s+of\s+(?:online\s+)?registration\s+of\s+application)\s*[:\-–]?\s*(.{2,100}?)(?=\s+(?:editing|printing|fee|exam)\b|$)",
         r"(?:last\s+date|deadline|closing\s+date|last\s+date\s+to\s+apply)\s*[:\-–]?\s*(.{2,100}?)(?=\s+(?:editing|printing|fee|exam)\b|$)",
         r"(?:अंतिम\s*तिथि|अंतिम\s*तारीख|आवेदन\s*की\s*अंतिम\s*तिथि)\s*[:\-–]?\s*(.{2,100}?)(?=\s+(?:परीक्षा|शुल्क)\b|$)"), "Not Available")
    return vacancy, qualification, salary, age_limit, application_fee, selection_process, exam_date, application_start_date, last_date


def _post_category_type(job):
    """Determine the public post type from the actual title first."""
    raw = str(job.get("category", "") or "").casefold().strip()
    title = re.sub(r"\s+", " ", str(job.get("title", "") or "")).casefold().strip()
    stored = str(job.get("post_type", "") or "").casefold().strip()

    # Specific update types always win over a generic category such as Teaching.
    if any(x in title for x in ("admit card", "admit-card", "hall ticket", "e-admit", "call letter", "प्रवेश पत्र", "प्रवेश-पत्र")):
        return "admit-card"
    if any(x in title for x in ("answer key", "answer-key", "answerkey", "उत्तर कुंजी", "उत्तरकुंजी")):
        return "answer-key"
    if any(x in title for x in ("shortlisted candidate", "shortlisted candidates", "shortlist", "selection list", "selected candidates", "marks of the candidates", "marks obtained", "merit list", "score card", "scorecard", "final result", "result of", "result dated", "परिणाम", "मेरिट")):
        return "result"
    if re.search(r"\bresult\b", title, re.I):
        return "result"
    if any(x in title for x in ("syllabus", "exam pattern", "पाठ्यक्रम")):
        return "syllabus"
    if any(x in title for x in ("scholarship", "fellowship", "छात्रवृत्ति")):
        return "scholarship"
    if stored in {"admit-card", "answer-key", "result", "syllabus", "scholarship", "recruitment"}:
        return stored
    if raw in {"admit card", "admit-card"}: return "admit-card"
    if raw in {"answer key", "answer-key"}: return "answer-key"
    if raw in {"result", "results"}: return "result"
    if raw == "syllabus": return "syllabus"
    if raw == "scholarship": return "scholarship"
    if raw in {"recruitment", "latest jobs", "latest job", "jobs", "job", "teaching", "teacher recruitment"}:
        return "recruitment"
    return "notice"


def _clean_url(value):
    value = str(value or "").strip()
    if not value or value in {"#", "None", "null", "javascript:void(0)"}:
        return ""
    return value


def _action_buttons(job, post_type):
    """Return only real, distinct actions. Never label the source URL as Apply."""
    links = []
    seen = set()

    def add(url, label, css):
        url = _clean_url(url)
        if not url or url in seen:
            return
        seen.add(url)
        links.append(f'<a class="{css}" href="{escape_html(url)}" target="_blank" rel="noopener">{escape_html(label)}</a>')

    official = _clean_url(job.get("official_website"))
    notification = _clean_url(job.get("notification_pdf") or job.get("official_notification_pdf"))
    source = _clean_url(job.get("url"))
    apply = _clean_url(job.get("apply_link"))
    result = _clean_url(job.get("result_url"))
    admit = _clean_url(job.get("admit_card_url"))
    answer = _clean_url(job.get("answer_key_url"))
    syllabus = _clean_url(job.get("syllabus_url"))

    if post_type == "admit-card":
        add(admit or source, "📥 Download Admit Card", "apply-btn")
        add(notification, "📄 Official Notification", "notification-btn")
    elif post_type == "answer-key":
        add(answer or source, "📥 Download Answer Key", "apply-btn")
        add(notification, "📄 Official Notification", "notification-btn")
    elif post_type == "result":
        add(result or source, "📊 View Result / Notice", "apply-btn")
        add(notification, "📄 Official Notification", "notification-btn")
    elif post_type == "syllabus":
        add(syllabus or notification or source, "📚 Download Syllabus", "apply-btn")
        add(notification, "📄 Official Notification", "notification-btn")
    elif post_type == "scholarship":
        add(apply or source, "📝 Apply Online", "apply-btn")
        add(notification, "📄 Official Notification", "notification-btn")
    elif post_type == "recruitment":
        add(apply, "🚀 Apply Online", "apply-btn")
        add(notification, "📄 Official Notification", "notification-btn")
        if not apply and not notification:
            add(source, "🔎 View Official Notice", "notification-btn")
    else:
        add(notification or source, "🔎 View Official Notice", "notification-btn")

    add(official, "🌐 Official Website", "official-btn")
    return "\n".join(links)


def _detail_rows(job, post_type, category, department, title, labels):
    vacancy_raw, qualification_raw, salary_raw, age_raw, fee_raw, selection_raw, exam_raw, start_raw, last_date_raw = _job_details(job)
    def val(raw, default):
        text = str(raw or "").strip()
        if not text or text.casefold() in {"not mentioned", "not available", "check official notification", "check notification"}:
            return ""
        return escape_html(localize_value(text, job, default))

    rows = []
    def add(label, value):
        value = str(value or "").strip()
        if value and value not in {"Not Available", "उपलब्ध नहीं", "Check Official Notification", "आधिकारिक अधिसूचना देखें"}:
            rows.append((label, value))

    add(labels["category"], escape_html(category))
    add(labels["department"], escape_html(department))

    if post_type == "recruitment":
        add(labels["vacancy"], val(vacancy_raw, labels["check_notification"]))
        add(labels["qualification"], val(qualification_raw, labels["check_notification"]))
        add(labels["salary"], val(salary_raw, labels["check_notification"]))
        add(labels["age_limit"], val(age_raw, labels["not_available"]))
        add(labels["application_fee"], val(fee_raw, labels["not_available"]))
        add(labels["selection_process"], val(selection_raw, labels["not_available"]))
        add(labels["exam_date"], val(exam_raw, labels["not_available"]))
        add(labels["application_start_date"], val(start_raw, labels["not_available"]))
        deadline = _deadline(job)
        last = deadline.strftime("%d-%m-%Y") if deadline else val(last_date_raw, labels["not_available"])
        add(labels["last_date"], escape_html(last))
    elif post_type == "admit-card":
        add(labels["exam_date"], val(exam_raw, labels["not_available"]))
    elif post_type == "result":
        add("Update Type", "Result / Selection / Marks Notice")
        add(labels["exam_date"], val(exam_raw, labels["not_available"]))
    elif post_type == "answer-key":
        add("Update Type", "Answer Key")
        add(labels["exam_date"], val(exam_raw, labels["not_available"]))
    elif post_type == "syllabus":
        add("Update Type", "Syllabus / Exam Pattern")
    elif post_type == "scholarship":
        add(labels["qualification"], val(qualification_raw, labels["check_notification"]))
        deadline = _deadline(job)
        last = deadline.strftime("%d-%m-%Y") if deadline else val(last_date_raw, labels["not_available"])
        add(labels["last_date"], escape_html(last))
    else:
        add("Update Type", "Official Notice")
    return rows


def build_html_body(job):
    lang = detect_content_language(job)
    labels = localized_labels(job)
    title = escape_html(localized_title(job))
    category_raw = localized_category(job)
    category = escape_html(category_raw)
    department = escape_html(str(job.get("department", "") or "").strip() or labels["not_available"])
    post_type = _post_category_type(job)
    description = escape_html(localized_summary(job))

    original_category = str(job.get("category", "") or "").strip()
    category_page = CATEGORY_PAGES.get(original_category, "latest-jobs.html")
    rows = _detail_rows(job, post_type, category_raw, str(job.get("department", "") or "").strip() or labels["not_available"], title, labels)
    table_html = "" if not rows else '<table class="job-table">' + "".join(f'<tr><th>{k}</th><td>{v}</td></tr>' for k,v in rows) + '</table>'
    buttons = _action_buttons(job, post_type)

    return f"""
<body>
<div id="header"></div>
<main class="post-wrapper">
<div class="post-container">
<nav class="breadcrumb">
<a href="../../index.html">{labels['home']}</a><span>›</span><a href="../../{category_page}">{category}</a><span>›</span><span>{title}</span>
</nav>
<h1 class="post-title">{title}</h1>
<p class="post-meta">📅 {labels['published']} : {published_date(job)} &nbsp;&nbsp;|&nbsp;&nbsp; 🏛 {department}</p>
<p class="post-description">{description}</p>
<h2>📋 {labels['details'] if post_type == 'recruitment' else 'Update Details'}</h2>
{table_html or '<div class="job-notice"><p>Detailed information is available in the official notice. Please use the official links below.</p></div>'}
<div class="post-buttons">
{buttons}
</div>
"""


# ==========================================================
# Part 4 : FAQ + Share + Related Posts + Footer
# ==========================================================

def build_extra_sections(job):
    """Language-safe FAQ/share/related sections."""
    lang = detect_content_language(job)
    title = escape_html(localized_title(job))
    summary = escape_html(localized_summary(job))
    post_type = _post_category_type(job)
    share_url = escape_html(post_site_url(job))

    if lang == "en":
        share_heading, related_heading, home_label = "Share this update", "Related Updates", "Back to Home"
        if post_type == "result":
            faq_items = [(f"How can I view {title}?", "Open the official result/notice link provided above."), ("Where can I find the official notification?", "Use the Official Notification button above when available."), ("What is the official website?", "Use the Official Website button above.")]
        elif post_type == "admit-card":
            faq_items = [(f"How can I download {title}?", "Open the official admit card link provided above."), ("Where can I find the official notification?", "Use the Official Notification button above when available.")]
        elif post_type == "recruitment":
            faq_items = [(f"What is {title}?", summary), ("What is the last date to apply?", "See the Last Date field above when available."), ("Where can I find the official notification?", "Use the Official Notification button above when available.")]
        else:
            faq_items = [(f"What is {title}?", summary)]
    elif lang == "hi":
        share_heading, related_heading, home_label = "इस अपडेट को साझा करें", "संबंधित अपडेट", "होम पर वापस जाएं"
        faq_items = [(f"{title} क्या है?", summary), ("आधिकारिक अधिसूचना कहाँ मिलेगी?", "ऊपर दिए गए आधिकारिक अधिसूचना बटन का उपयोग करें।"), ("आधिकारिक वेबसाइट कौन-सी है?", "ऊपर दिए गए आधिकारिक वेबसाइट बटन का उपयोग करें।")]
    else:
        faq_items, share_heading, related_heading, home_label = [], "", "", ""

    faq_html = ""
    faq_schema = {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[]}
    if faq_items:
        faq_html = '<section class="faq-section"><h2>' + escape_html("Frequently Asked Questions" if lang == "en" else "अक्सर पूछे जाने वाले प्रश्न") + '</h2>' + ''.join(f'<div class="faq-item"><h3>{escape_html(q)}</h3><p>{escape_html(a)}</p></div>' for q,a in faq_items) + '</section>'
        faq_schema["mainEntity"] = [{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq_items]

    related = []
    current_slug = generate_slug(job.get("title", ""), job)
    for post in sorted(OUTPUT_DIR.glob("*.html"), key=lambda x: x.stat().st_mtime, reverse=True):
        if post.stem == current_slug:
            continue
        related.append(post)
        if len(related) == 4:
            break
    related_html = "".join(f'<div class="related-card"><a href="../../generated/posts/{escape_html(post.name)}"><h3>{escape_html(post.stem.replace("-", " " ).title())}</h3></a></div>' for post in related)

    parts = []
    if share_heading:
        parts.append(f'<section class="share-section"><h2>📤 {escape_html(share_heading)}</h2><div class="share-buttons"><a target="_blank" rel="noopener" href="https://wa.me/?text={share_url}">WhatsApp</a><a target="_blank" rel="noopener" href="https://t.me/share/url?url={share_url}">Telegram</a><a target="_blank" rel="noopener" href="https://twitter.com/intent/tweet?url={share_url}">Twitter</a><a target="_blank" rel="noopener" href="https://www.facebook.com/sharer/sharer.php?u={share_url}">Facebook</a></div></section>')
    if faq_html:
        parts.append(faq_html)
    if related_heading:
        empty = escape_html("No related updates available." if lang == "en" else "अभी संबंधित अपडेट उपलब्ध नहीं हैं।")
        parts.append(f'<section class="related-posts"><h2>🔥 {escape_html(related_heading)}</h2><div class="related-grid">{related_html or "<p>" + empty + "</p>"}</div></section>')
    if home_label:
        parts.append(f'<section class="next-action"><a class="home-btn" href="../../index.html">🏠 {escape_html(home_label)}</a></section>')
    parts.append('<div id="footer"></div><script src="../../load.js"></script><script src="../../menu.js"></script><script src="../../script.js"></script>')
    if faq_schema["mainEntity"]:
        parts.append('<script type="application/ld+json">' + json.dumps(faq_schema, ensure_ascii=False, indent=2) + '</script>')
    return "\n".join(parts)


# ==========================================================
# Part 5 : Core HTML Generation Engine
# ==========================================================

def _remove_post_images(html):
    """Remove every <img> element from automated post content.

    This is intentionally applied to the generated body/extra sections only;
    SEO metadata such as og:image/schema image remains in the HTML head.
    """
    if not html:
        return html
    html = re.sub(r'<img\b[^>]*>', '', html, flags=re.I)
    html = re.sub(r'<picture\b[^>]*>.*?</picture>', '', html, flags=re.I | re.S)
    return html


def build_html(job):
    body = _remove_post_images(build_html_body(job))
    extra = _remove_post_images(build_extra_sections(job))
    return (
        build_html_head(job)
        + body
        + extra
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
    # Generate the complete public archive. Application-expired jobs remain
    # available in their category/history; only Latest Jobs hides them.
    public_jobs = filter_public_jobs(jobs)
    cleanup_stale_generated_posts(jobs, public_jobs)

    generated = []
    failed = 0
    seen = set()
    language_counts = {}
    for _job in public_jobs:
        _lang = detect_content_language(_job)
        language_counts[_lang] = language_counts.get(_lang, 0) + 1
    logger.info("POST LANGUAGE ROUTING | %s", language_counts)

    for job in public_jobs:
        try:
            title = str(job.get("title", "")).strip()
            slug = generate_slug(title, job)
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
    logger.info("Public Posts : %d", len(public_jobs))
    logger.info("Generated    : %d", len(generated))
    logger.info("Failed     : %d", failed)
    logger.info("=" * 60)

    try:
        category_generator.build_categories(public_jobs)
        logger.info("Category Pages Updated Successfully.")
    except Exception:
        logger.exception("Category Generator Failed")

    return {
        "success": len(generated),
        "failed": failed,
        "total": len(public_jobs),
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

    public_jobs = filter_public_jobs(jobs)

    result = generate_all(public_jobs)

    verify_generated_files()

    # Homepage and category pages keep the complete archive. Latest Jobs is
    # filtered separately inside category_generator by application deadline.
    homepage.run(public_jobs)
    category_generator.run(public_jobs)

    html_statistics()

    logger.info(
        "Website Generated Successfully."
    )

    return result


logger.info(
    "HTML Generator V4.1 Loaded Successfully."
)
