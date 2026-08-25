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


LANGUAGE_LABELS["en"]={"home":"Home","published":"Published","details":"Recruitment Details","category":"Category","department":"Department","vacancy":"Number of Posts","qualification":"Educational Qualification","salary":"Salary / Pay Scale","age_limit":"Age Limit","application_fee":"Application Fee","selection_process":"Selection Process","exam_date":"Exam Date","application_start_date":"Application Start Date","last_date":"Last Date","apply":"Apply Online","notification":"Download Notification","official":"Official Website","not_available":"Not Available","check_notification":"Check Official Notification"}
LANGUAGE_LABELS["ta"].update({"age_limit":"வயது வரம்பு","application_fee":"விண்ணப்பக் கட்டணம்","selection_process":"தேர்வு முறை","exam_date":"தேர்வு தேதி","application_start_date":"விண்ணப்ப தொடக்க தேதி"})
LANGUAGE_LABELS["te"].update({"age_limit":"వయోపరిమితి","application_fee":"దరఖాస్తు రుసుము","selection_process":"ఎంపిక విధానం","exam_date":"పరీక్ష తేదీ","application_start_date":"దరఖాస్తు ప్రారంభ తేదీ"})
LANGUAGE_LABELS["bn"].update({"age_limit":"বয়সসীমা","application_fee":"আবেদন ফি","selection_process":"নির্বাচন প্রক্রিয়া","exam_date":"পরীক্ষার তারিখ","application_start_date":"আবেদন শুরুর তারিখ"})
LANGUAGE_LABELS["gu"].update({"age_limit":"વય મર્યાદા","application_fee":"અરજી ફી","selection_process":"પસંદગી પ્રક્રિયા","exam_date":"પરીક્ષાની તારીખ","application_start_date":"અરજી શરૂ કરવાની તારીખ"})
LANGUAGE_LABELS["kn"].update({"age_limit":"ವಯೋಮಿತಿ","application_fee":"ಅರ್ಜಿ ಶುಲ್ಕ","selection_process":"ಆಯ್ಕೆ ಪ್ರಕ್ರಿಯೆ","exam_date":"ಪರೀಕ್ಷೆಯ ದಿನಾಂಕ","application_start_date":"ಅರ್ಜಿ ಪ್ರಾರಂಭ ದಿನಾಂಕ"})
LANGUAGE_LABELS["ml"].update({"age_limit":"പ്രായപരിധി","application_fee":"അപേക്ഷാ ഫീസ്","selection_process":"തിരഞ്ഞെടുപ്പ് പ്രക്രിയ","exam_date":"പരീക്ഷാ തീയതി","application_start_date":"അപേക്ഷ ആരംഭ തീയതി"})
LANGUAGE_LABELS["mr"].update({"age_limit":"वयोमर्यादा","application_fee":"अर्ज शुल्क","selection_process":"निवड प्रक्रिया","exam_date":"परीक्षा दिनांक","application_start_date":"अर्ज सुरू होण्याची तारीख"})
LANGUAGE_LABELS["pa"].update({"age_limit":"ਉਮਰ ਸੀਮਾ","application_fee":"ਅਰਜ਼ੀ ਫੀਸ","selection_process":"ਚੋਣ ਪ੍ਰਕਿਰਿਆ","exam_date":"ਪ੍ਰੀਖਿਆ ਮਿਤੀ","application_start_date":"ਅਰਜ਼ੀ ਸ਼ੁਰੂ ਮਿਤੀ"})
LANGUAGE_LABELS["or"].update({"age_limit":"ବୟସ ସୀମା","application_fee":"ଆବେଦନ ଶୁଳ୍କ","selection_process":"ଚୟନ ପ୍ରକ୍ରିୟା","exam_date":"ପରୀକ୍ଷା ତାରିଖ","application_start_date":"ଆବେଦନ ଆରମ୍ଭ ତାରିଖ"})


def detect_content_language(job):
    """Detect the language of the official notification, not the site chrome.

    When a PDF was extracted, its recorded notification_language is authoritative.
    Otherwise detect the dominant script from notification_text/notification_content.
    We never infer Hindi merely because a field is missing.
    """
    explicit = str(job.get("notification_language") or "").strip().lower()
    if explicit in LANGUAGE_LABELS or explicit == "en":
        return explicit

    source_text = " ".join(
        str(job.get(k, "") or "")
        for k in ("notification_text", "notification_content")
    ).strip()
    if not source_text:
        source_text = " ".join(
            str(job.get(k, "") or "")
            for k in ("content", "description", "summary", "title", "department")
        ).strip()

    counts = {lang: len(rx.findall(source_text)) for lang, rx in SCRIPT_RANGES.items()}
    best = max(counts, key=counts.get) if counts else "en"
    if counts.get("hi", 0) >= 20:
        mr_markers = ("आहे", "आहेत", "करण्यात", "उमेदवार", "महाराष्ट्र", "अर्जदार", "पात्रता", "रिक्त पदे", "शैक्षणिक")
        if sum(source_text.count(x) for x in mr_markers) >= 2:
            return "mr"
        return "hi"
    if counts.get(best, 0) >= 20:
        return best
    if len(re.findall(r"[A-Za-z]", source_text)) >= 20:
        return "en"
    return best if counts.get(best, 0) else "en"


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
    """Return extracted values verbatim.

    The notification language controls only the surrounding UI labels.  Field
    values (qualification, salary, selection process, etc.) are never machine
    translated, because the source notification must remain authoritative.
    """
    text = str(value or "").strip()
    if not text or text.lower() in {"not mentioned", "not available", "n/a", "na", "none", "null"}:
        return default
    return text


def localized_title(job):
    # The title is source text. Never translate an English/Hindi/regional title.
    return str(job.get("title", "Government Job Update")).strip()


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
    # Keep the scraped/source notification wording. No automatic translation.
    for key in ("description", "summary", "content", "notification_text"):
        source = str(job.get(key) or "").strip()
        if source:
            return source[:2500]
    return localized_title(job)

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
    # Use source-language text instead of generating a translated description.
    source = localized_summary(job).strip()
    if source:
        return re.sub(r"\s+", " ", source)[:160]
    return localized_title(job)[:160]


def canonical_url(slug):
    return f"{BASE_URL}/generated/posts/{slug}.html"


def published_date_display(job=None):
    iso=published_date(job)
    m=re.match(r"^(\d{4})-(\d{2})-(\d{2})$",str(iso or ""))
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else (iso or "Not Available")

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
    # Fallback only for genuinely new records that have no source date.
    return "उपलब्ध नहीं"


def breadcrumb(job):
    raw_category = str(job.get("category", "") or "")
    page = CATEGORY_PAGES.get(raw_category, "latest-jobs.html")
    labels = localized_labels(job)
    return [
        {"name": labels["home"], "url": BASE_URL},
        {"name": localized_category(job), "url": f"{BASE_URL}/{page}"},
        {"name": localized_title(job), "url": canonical_url(generate_slug(job.get("title", ""), job))}
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


_NOISE_PHRASES=[r"(?:हेतु\s*)?क्लिक\s*करें",r"के\s*लिए\s*क्लिक\s*करें",r"click\s*here",r"click\s*to\s*(?:apply|download|view|read)",r"here\s*to\s*(?:apply|download|view)",r"skip\s*to\s*main\s*content",r"download\s+(?:hindi|english)\s+notification"]
def _strip_navigation_noise(value):
    text=str(value or "")
    for pattern in _NOISE_PHRASES: text=re.sub(pattern,"",text,flags=re.I)
    text=re.sub(r"(?:^|\s)(?:[0-9]+|[ivxlcdm]+|[कखगघ])\s*[-.)]\s*"," ",text,flags=re.I)
    return re.sub(r"\s+"," ",text).strip(" -:;|,.")

def _clean_detail(value):
    if value is None:
        return ""
    value = _strip_navigation_noise(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip(" :-–|,;")


def _detail_source(job):
    """Return the strongest structured detail source first.

    Never use the title as a vacancy/qualification/salary source. Titles such
    as "Post AGM", "X posts", etc. are not reliable field values.
    """
    parts = []
    for key in ("notification_text", "content", "raw_text", "body", "text"):
        value = job.get(key)
        if value:
            parts.append(str(value))
    return re.sub(r"\s+", " ", " ".join(parts))


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
    raw = str(job.get("category", "") or "").casefold().strip()
    title = str(job.get("title", "") or "").casefold()
    blob = f"{raw} {title}"
    if "admit" in raw or any(x in title for x in ("admit card", "hall ticket", "call letter", "प्रवेश पत्र")):
        return "admit-card"
    if "answer" in raw or "answer key" in title or "उत्तर कुंजी" in title:
        return "answer-key"
    if "result" in raw or re.search(r"\bresult\b|\bmerit list\b|\bscore ?card\b|परिणाम", title):
        return "result"
    if "syllabus" in raw or "syllabus" in title or "पाठ्यक्रम" in title:
        return "syllabus"
    if "scholarship" in raw or "scholarship" in title or "छात्रवृत्ति" in title:
        return "scholarship"
    if "teaching" in raw or "teacher" in raw:
        return "teaching"
    if "entrance" in raw:
        return "entrance"
    return "recruitment"

def build_html_body(job):
    lang = detect_content_language(job)
    labels = localized_labels(job)

    title = escape_html(localized_title(job))
    category_raw = localized_category(job)
    category = escape_html(category_raw)
    department = escape_html(localize_value(job.get("department", "Government"), job, labels["not_available"]))
    post_type = _post_category_type(job)

    vacancy_raw, qualification_raw, salary_raw, age_raw, fee_raw, selection_raw, exam_raw, start_raw, last_date_raw = _job_details(job)
    vacancy = escape_html(localize_value(vacancy_raw, job, labels["check_notification"]))
    qualification = escape_html(localize_value(qualification_raw, job, labels["check_notification"]))
    salary = escape_html(localize_value(salary_raw, job, labels["check_notification"]))
    age_limit = escape_html(localize_value(age_raw, job, labels.get("not_available", "उपलब्ध नहीं")))
    application_fee = escape_html(localize_value(fee_raw, job, labels.get("not_available", "उपलब्ध नहीं")))
    selection_process = escape_html(localize_value(selection_raw, job, labels.get("not_available", "उपलब्ध नहीं")))
    exam_date = escape_html(localize_value(exam_raw, job, labels.get("not_available", "उपलब्ध नहीं")))
    application_start_date = escape_html(localize_value(start_raw, job, labels.get("not_available", "उपलब्ध नहीं")))

    deadline = _deadline(job)
    last_date_value = deadline.strftime("%d-%m-%Y") if deadline else localize_value(last_date_raw, job, labels["not_available"])
    last_date = escape_html(last_date_value)
    description = escape_html(localized_summary(job))

    original_category = str(job.get("category", "") or "").strip()
    category_page = CATEGORY_PAGES.get(original_category, "latest-jobs.html")

    apply_link = job.get("apply_link") or job.get("url") or "#"
    notification = job.get("notification_pdf") or job.get("url") or "#"
    official = job.get("official_website") or job.get("url") or "#"

    # Category-specific primary action and details. All visible labels use the
    # notification language; extracted values remain verbatim.
    rows = []
    action_url = official
    action_label = "🌐 " + labels["official"]
    secondary_url = notification
    secondary_label = "📄 " + labels["notification"]

    if post_type == "admit-card":
        rows = [
            (labels["category"], category), (labels["department"], department),
            (labels["exam_date"], exam_date), (labels.get("details", "Details"), labels["notification"]),
        ]
        action_url = job.get("admit_card_url") or job.get("url") or official
        action_label = "📥 " + labels["apply"]
    elif post_type == "result":
        rows = [
            (labels["category"], category), (labels["department"], department),
            (labels["exam_date"], exam_date), (labels["details"], "Result"),
        ]
        action_url = job.get("result_url") or job.get("url") or official
        action_label = "📊 Result"
    elif post_type == "answer-key":
        rows = [
            (labels["category"], category), (labels["department"], department),
            (labels["exam_date"], exam_date), (labels["details"], "Answer Key"),
        ]
        action_url = job.get("answer_key_url") or job.get("url") or official
        action_label = "📥 Answer Key"
    elif post_type == "syllabus":
        rows = [
            (labels["category"], category), (labels["department"], department),
            (labels["details"], title), ("Syllabus", labels["notification"]),
        ]
        action_url = job.get("syllabus_url") or job.get("url") or official
        action_label = "📚 Syllabus"
    elif post_type == "scholarship":
        rows = [
            (labels["category"], category), (labels["department"], department),
            (labels["qualification"], qualification), (labels["last_date"], last_date),
        ]
        action_url = apply_link
        action_label = "📝 " + labels["apply"]
    else:
        rows = [
            (labels["category"], category), (labels["department"], department),
            (labels["vacancy"], vacancy), (labels["qualification"], qualification),
            (labels["salary"], salary), (labels["age_limit"], age_limit),
            (labels["application_fee"], application_fee),
            (labels["selection_process"], selection_process),
            (labels["exam_date"], exam_date),
            (labels["application_start_date"], application_start_date),
            (labels["last_date"], last_date),
        ]
        action_url = apply_link
        action_label = "🚀 " + labels["apply"]

    table_rows = "\n".join(f'<tr><th>{k}</th><td>{v}</td></tr>' for k,v in rows)

    return f"""
<body>
<div id="header"></div>
<main class="post-wrapper">
<div class="post-container">
<nav class="breadcrumb">
<a href="../../index.html">{labels['home']}</a>
<span>›</span>
<a href="../../{category_page}">{category}</a>
<span>›</span>
<span>{title}</span>
</nav>

<h1 class="post-title">{title}</h1>

<p class="post-meta">
📅 {labels['published']} : {published_date_display(job)}
&nbsp;&nbsp;|&nbsp;&nbsp;
🏛 {department}
</p>

<p class="post-description">{description}</p>

<h2>📋 {labels['details']}</h2>
<table class="job-table">
{table_rows}
</table>

<div class="post-buttons">
<a class="apply-btn" href="{escape_html(action_url)}" target="_blank" rel="noopener">{action_label}</a>
<a class="notification-btn" href="{escape_html(secondary_url)}" target="_blank" rel="noopener">{secondary_label}</a>
<a class="official-btn" href="{escape_html(official)}" target="_blank" rel="noopener">{escape_html("🌐 " + labels["official"])}</a>
</div>
"""


# ==========================================================
# Part 4 : FAQ + Share + Related Posts + Footer
# ==========================================================

def build_extra_sections(job):
    """Build FAQ/share/related sections in the notification language.

    The FAQ uses extracted values verbatim.  No English/Hindi/regional
    translation is performed.
    """
    lang = detect_content_language(job)
    labels = localized_labels(job)
    title_raw = localized_title(job)
    title = escape_html(title_raw)
    summary_raw = localized_summary(job)
    summary = escape_html(summary_raw)

    vacancy, qualification, salary, age_limit, application_fee, selection_process, exam_date, application_start_date, last_date = _job_details(job)
    def val(value, fallback):
        return escape_html(localize_value(value, job, fallback))

    vacancy = val(vacancy, labels["check_notification"])
    qualification = val(qualification, labels["check_notification"])
    salary = val(salary, labels["check_notification"])
    age_limit = val(age_limit, labels["check_notification"])
    application_fee = val(application_fee, labels["check_notification"])
    selection_process = val(selection_process, labels["check_notification"])
    exam_date = val(exam_date, labels["check_notification"])
    deadline = _deadline(job)
    deadline_text = escape_html(
        deadline.strftime("%d-%m-%Y") if deadline
        else localize_value(last_date, job, labels["check_notification"])
    )

    post_type = _post_category_type(job)

    UI = {
        "en": {
            "faq":"Frequently Asked Questions", "related":"Related Updates",
            "share":"Share this update", "home":"Back to Home",
            "what":"What is this update?", "posts":"How many posts are available?",
            "qualification":"What is the educational qualification?",
            "age":"What is the age limit?", "fee":"What is the application fee?",
            "last":"What is the last date to apply?", "selection":"What is the selection process?",
            "official":"Check the official notification/website for the latest instructions.",
            "action":"Apply Online",
        },
        "hi": {
            "faq":"अक्सर पूछे जाने वाले प्रश्न", "related":"संबंधित अपडेट",
            "share":"इस अपडेट को साझा करें", "home":"होम पर वापस जाएं",
            "what":"यह अपडेट किस बारे में है?", "posts":"कुल कितने पद हैं?",
            "qualification":"शैक्षणिक योग्यता क्या है?", "age":"आयु सीमा क्या है?",
            "fee":"आवेदन शुल्क कितना है?", "last":"आवेदन की अंतिम तिथि क्या है?",
            "selection":"चयन प्रक्रिया क्या है?",
            "official":"नवीनतम निर्देशों के लिए आधिकारिक अधिसूचना/वेबसाइट देखें।",
            "action":"ऑनलाइन आवेदन करें",
        },
        "mr": {
            "faq":"वारंवार विचारले जाणारे प्रश्न", "related":"संबंधित अपडेट",
            "share":"हा अपडेट शेअर करा", "home":"मुख्यपृष्ठावर परत जा",
            "what":"हा अपडेट कशाबद्दल आहे?", "posts":"एकूण किती पदे आहेत?",
            "qualification":"शैक्षणिक पात्रता काय आहे?", "age":"वयोमर्यादा काय आहे?",
            "fee":"अर्ज शुल्क किती आहे?", "last":"अर्ज करण्याची अंतिम तारीख काय आहे?",
            "selection":"निवड प्रक्रिया काय आहे?",
            "official":"नवीनतम सूचनांसाठी अधिकृत अधिसूचना/वेबसाइट पहा.",
            "action":"ऑनलाइन अर्ज करा",
        },
        "ta": {
            "faq":"அடிக்கடி கேட்கப்படும் கேள்விகள்", "related":"தொடர்புடைய புதுப்பிப்புகள்",
            "share":"இந்த புதுப்பிப்பைப் பகிரவும்", "home":"முகப்புக்குத் திரும்பவும்",
            "what":"இந்த புதுப்பிப்பு எதைப் பற்றியது?", "posts":"மொத்த காலியிடங்கள் எத்தனை?",
            "qualification":"கல்வித் தகுதி என்ன?", "age":"வயது வரம்பு என்ன?",
            "fee":"விண்ணப்பக் கட்டணம் எவ்வளவு?", "last":"விண்ணப்பிக்க கடைசி தேதி என்ன?",
            "selection":"தேர்வு முறை என்ன?",
            "official":"சமீபத்திய வழிமுறைகளுக்கு அதிகாரப்பூர்வ அறிவிப்பு/இணையதளத்தைப் பார்க்கவும்.",
            "action":"ஆன்லைனில் விண்ணப்பிக்கவும்",
        },
        "te": {
            "faq":"తరచుగా అడిగే ప్రశ్నలు", "related":"సంబంధిత నవీకరణలు",
            "share":"ఈ నవీకరణను షేర్ చేయండి", "home":"హోమ్‌కు తిరిగి వెళ్లండి",
            "what":"ఈ నవీకరణ దేనికి సంబంధించినది?", "posts":"మొత్తం ఖాళీలు ఎన్ని?",
            "qualification":"విద్యార్హత ఏమిటి?", "age":"వయోపరిమితి ఏమిటి?",
            "fee":"దరఖాస్తు రుసుము ఎంత?", "last":"దరఖాస్తు చివరి తేదీ ఏమిటి?",
            "selection":"ఎంపిక విధానం ఏమిటి?",
            "official":"తాజా సూచనల కోసం అధికారిక నోటిఫికేషన్/వెబ్‌సైట్ చూడండి.",
            "action":"ఆన్‌లైన్‌లో దరఖాస్తు చేయండి",
        },
        "bn": {
            "faq":"প্রায়শই জিজ্ঞাসিত প্রশ্ন", "related":"সম্পর্কিত আপডেট",
            "share":"এই আপডেটটি শেয়ার করুন", "home":"হোমে ফিরে যান",
            "what":"এই আপডেটটি কী সম্পর্কে?", "posts":"মোট শূন্যপদ কত?",
            "qualification":"শিক্ষাগত যোগ্যতা কী?", "age":"বয়সসীমা কত?",
            "fee":"আবেদন ফি কত?", "last":"আবেদনের শেষ তারিখ কী?",
            "selection":"নির্বাচন প্রক্রিয়া কী?",
            "official":"সর্বশেষ নির্দেশনার জন্য অফিসিয়াল বিজ্ঞপ্তি/ওয়েবসাইট দেখুন।",
            "action":"অনলাইনে আবেদন করুন",
        },
        "gu": {
            "faq":"વારંવાર પૂછાતા પ્રશ્નો", "related":"સંબંધિત અપડેટ્સ",
            "share":"આ અપડેટ શેર કરો", "home":"હોમ પર પાછા જાઓ",
            "what":"આ અપડેટ શેના વિશે છે?", "posts":"કુલ ખાલી જગ્યાઓ કેટલી છે?",
            "qualification":"શૈક્ષણિક લાયકાત શું છે?", "age":"વય મર્યાદા કેટલી છે?",
            "fee":"અરજી ફી કેટલી છે?", "last":"અરજી કરવાની છેલ્લી તારીખ શું છે?",
            "selection":"પસંદગી પ્રક્રિયા શું છે?",
            "official":"નવીનતમ સૂચનાઓ માટે સત્તાવાર સૂચના/વેબસાઇટ જુઓ.",
            "action":"ઓનલાઇન અરજી કરો",
        },
        "kn": {
            "faq":"ಪದೇ ಪದೇ ಕೇಳಲಾಗುವ ಪ್ರಶ್ನೆಗಳು", "related":"ಸಂಬಂಧಿತ ನವೀಕರಣಗಳು",
            "share":"ಈ ನವೀಕರಣವನ್ನು ಹಂಚಿಕೊಳ್ಳಿ", "home":"ಮುಖಪುಟಕ್ಕೆ ಹಿಂತಿರುಗಿ",
            "what":"ಈ ನವೀಕರಣ ಯಾವುದರ ಕುರಿತು?", "posts":"ಒಟ್ಟು ಖಾಲಿ ಹುದ್ದೆಗಳು ಎಷ್ಟು?",
            "qualification":"ಶೈಕ್ಷಣಿಕ ಅರ್ಹತೆ ಏನು?", "age":"ವಯೋಮಿತಿ ಎಷ್ಟು?",
            "fee":"ಅರ್ಜಿ ಶುಲ್ಕ ಎಷ್ಟು?", "last":"ಅರ್ಜಿ ಸಲ್ಲಿಸಲು ಕೊನೆಯ ದಿನಾಂಕ ಯಾವುದು?",
            "selection":"ಆಯ್ಕೆ ಪ್ರಕ್ರಿಯೆ ಏನು?",
            "official":"ಇತ್ತೀಚಿನ ಸೂಚನೆಗಳಿಗಾಗಿ ಅಧಿಕೃತ ಅಧಿಸೂಚನೆ/ವೆಬ್‌ಸೈಟ್ ನೋಡಿ.",
            "action":"ಆನ್‌ಲೈನ್‌ನಲ್ಲಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ",
        },
        "ml": {
            "faq":"പതിവായി ചോദിക്കുന്ന ചോദ്യങ്ങൾ", "related":"ബന്ധപ്പെട്ട അപ്ഡേറ്റുകൾ",
            "share":"ഈ അപ്ഡേറ്റ് പങ്കിടുക", "home":"ഹോമിലേക്ക് മടങ്ങുക",
            "what":"ഈ അപ്ഡേറ്റ് എന്തിനെക്കുറിച്ചാണ്?", "posts":"ആകെ ഒഴിവുകൾ എത്ര?",
            "qualification":"വിദ്യാഭ്യാസ യോഗ്യത എന്താണ്?", "age":"പ്രായപരിധി എത്ര?",
            "fee":"അപേക്ഷാ ഫീസ് എത്രയാണ്?", "last":"അപേക്ഷിക്കാനുള്ള അവസാന തീയതി എന്താണ്?",
            "selection":"തിരഞ്ഞെടുപ്പ് പ്രക്രിയ എന്താണ്?",
            "official":"ഏറ്റവും പുതിയ നിർദ്ദേശങ്ങൾക്ക് ഔദ്യോഗിക വിജ്ഞാപനം/വെബ്സൈറ്റ് കാണുക.",
            "action":"ഓൺലൈനായി അപേക്ഷിക്കുക",
        },
        "pa": {
            "faq":"ਅਕਸਰ ਪੁੱਛੇ ਜਾਂਦੇ ਸਵਾਲ", "related":"ਸੰਬੰਧਿਤ ਅਪਡੇਟ",
            "share":"ਇਹ ਅਪਡੇਟ ਸਾਂਝਾ ਕਰੋ", "home":"ਹੋਮ ਤੇ ਵਾਪਸ ਜਾਓ",
            "what":"ਇਹ ਅਪਡੇਟ ਕਿਸ ਬਾਰੇ ਹੈ?", "posts":"ਕੁੱਲ ਅਸਾਮੀਆਂ ਕਿੰਨੀਆਂ ਹਨ?",
            "qualification":"ਵਿਦਿਅਕ ਯੋਗਤਾ ਕੀ ਹੈ?", "age":"ਉਮਰ ਸੀਮਾ ਕੀ ਹੈ?",
            "fee":"ਅਰਜ਼ੀ ਫੀਸ ਕਿੰਨੀ ਹੈ?", "last":"ਅਰਜ਼ੀ ਦੀ ਆਖਰੀ ਮਿਤੀ ਕੀ ਹੈ?",
            "selection":"ਚੋਣ ਪ੍ਰਕਿਰਿਆ ਕੀ ਹੈ?",
            "official":"ਤਾਜ਼ਾ ਹਦਾਇਤਾਂ ਲਈ ਅਧਿਕਾਰਤ ਨੋਟੀਫਿਕੇਸ਼ਨ/ਵੈੱਬਸਾਈਟ ਵੇਖੋ।",
            "action":"ਆਨਲਾਈਨ ਅਰਜ਼ੀ ਦਿਓ",
        },
        "or": {
            "faq":"ପ୍ରାୟ ପଚରାଯାଉଥିବା ପ୍ରଶ୍ନ", "related":"ସମ୍ବନ୍ଧିତ ଅପଡେଟ୍",
            "share":"ଏହି ଅପଡେଟ୍ ସେୟାର କରନ୍ତୁ", "home":"ମୂଳପୃଷ୍ଠାକୁ ଫେରନ୍ତୁ",
            "what":"ଏହି ଅପଡେଟ୍ କାହା ବିଷୟରେ?", "posts":"ମୋଟ ଖାଲି ପଦବୀ କେତେ?",
            "qualification":"ଶିକ୍ଷାଗତ ଯୋଗ୍ୟତା କଣ?", "age":"ବୟସ ସୀମା କେତେ?",
            "fee":"ଆବେଦନ ଶୁଳ୍କ କେତେ?", "last":"ଆବେଦନର ଶେଷ ତାରିଖ କଣ?",
            "selection":"ଚୟନ ପ୍ରକ୍ରିୟା କଣ?",
            "official":"ସର୍ବଶେଷ ନିର୍ଦ୍ଦେଶ ପାଇଁ ଅଧିକାରିକ ବିଜ୍ଞପ୍ତି/ୱେବସାଇଟ୍ ଦେଖନ୍ତୁ।",
            "action":"ଅନଲାଇନରେ ଆବେଦନ କରନ୍ତୁ",
        },
    }
    ui = UI.get(lang, UI["en"])

    # FAQ is intentionally factual and compact; extracted source values are not translated.
    faq_items = [
        (ui["what"], summary_raw),
        (ui["posts"], vacancy),
        (ui["qualification"], qualification),
        (ui["age"], age_limit),
        (ui["fee"], application_fee),
        (ui["last"], deadline_text),
        (ui["selection"], selection_process),
    ]
    if post_type in {"admit-card", "result", "answer-key", "syllabus"}:
        faq_items = [
            (ui["what"], summary_raw),
            (labels["exam_date"], exam_date),
            (labels["official"], ui["official"]),
        ]

    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a or "")}}
            for q, a in faq_items
        ],
    }
    faq_html = "\n".join(
        f'<div class="faq-item"><h3>{escape_html(q)}</h3><p>{a}</p></div>'
        for q, a in faq_items
    )

    current_slug = generate_slug(job.get("title", ""), job)
    related = []
    for post in sorted(OUTPUT_DIR.glob("*.html"), key=lambda x: x.stat().st_mtime, reverse=True):
        if post.stem == current_slug:
            continue
        related.append(post)
        if len(related) == 4:
            break
    related_html = "".join(
        f'<div class="related-card"><a href="../../generated/posts/{escape_html(post.name)}">'
        f'<h3>{escape_html(post.stem.replace("-", " ").title())}</h3></a></div>'
        for post in related
    )

    share_url = escape_html(post_site_url(job))
    if post_type == "admit-card":
        next_action_url, next_action_label = job.get("admit_card_url") or job.get("url") or "#", "📥 " + labels["notification"]
    elif post_type == "answer-key":
        next_action_url, next_action_label = job.get("answer_key_url") or job.get("url") or "#", "📥 " + labels["notification"]
    elif post_type == "result":
        next_action_url, next_action_label = job.get("result_url") or job.get("url") or "#", "📊 Result"
    elif post_type == "syllabus":
        next_action_url, next_action_label = job.get("syllabus_url") or job.get("url") or "#", "📚 Syllabus"
    else:
        next_action_url, next_action_label = job.get("apply_link") or job.get("url") or "#", "🚀 " + ui["action"]

    template = f"""
<!-- ================= SHARE ================= -->
<section class="share-section">
<h2>📤 {escape_html(ui["share"])}</h2>
<div class="share-buttons">
<a target="_blank" rel="noopener" href="https://wa.me/?text=SHARE_URL">WhatsApp</a>
<a target="_blank" rel="noopener" href="https://t.me/share/url?url=SHARE_URL">Telegram</a>
<a target="_blank" rel="noopener" href="https://twitter.com/intent/tweet?url=SHARE_URL">Twitter</a>
<a target="_blank" rel="noopener" href="https://www.facebook.com/sharer/sharer.php?u=SHARE_URL">Facebook</a>
</div>
</section>

<section class="faq-section">
<h2>❓ {escape_html(ui["faq"])}</h2>
FAQ_HTML
</section>

<section class="related-posts">
<h2>🔥 {escape_html(ui["related"])}</h2>
<div class="related-grid">
RELATED_HTML
</div>
</section>

<section class="next-action">
<a class="home-btn" href="../../index.html">🏠 {escape_html(ui["home"])}</a>
<a class="apply-btn" href="ACTION_LINK" target="_blank" rel="noopener">ACTION_LABEL</a>
</section>

<div id="footer"></div>
<script src="../../load.js"></script>
<script src="../../menu.js"></script>
<script src="../../script.js"></script>
<script type="application/ld+json">FAQ_SCHEMA</script>
</body>
</html>
"""
    return (
        template.replace("SHARE_URL", share_url)
        .replace("FAQ_HTML", faq_html)
        .replace("RELATED_HTML", related_html or f'<p>{escape_html(ui["official"])}</p>')
        .replace("ACTION_LINK", escape_html(next_action_url))
        .replace("ACTION_LABEL", escape_html(next_action_label))
        .replace("FAQ_SCHEMA", json.dumps(faq_schema, ensure_ascii=False, indent=2))
    )

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
