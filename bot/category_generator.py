# ==========================================================
# Category Generator V5
# Part 1 : Imports + Configuration + Helpers
# ==========================================================

import re
import logging
from pathlib import Path
from url_utils import slugify as canonical_slug, post_relative_url, post_exists
from datetime import datetime, timedelta

logger = logging.getLogger("CategoryGeneratorV5")

ROOT_DIR = Path(__file__).resolve().parent.parent

# ==========================================================
# Category Pages
# ==========================================================

CATEGORY_FILES = {
    # Core categories
    "latest-jobs": ROOT_DIR / "latest-jobs.html",
    "banking": ROOT_DIR / "banking-jobs.html",
    "railway": ROOT_DIR / "railway-jobs.html",
    "upsc": ROOT_DIR / "upsc.html",
    "ssc": ROOT_DIR / "ssc.html",
    "teacher-recruitment": ROOT_DIR / "teacher-recruitment.html",
    "ctet": ROOT_DIR / "ctet.html",
    "utet": ROOT_DIR / "utet.html",
    "deled": ROOT_DIR / "deled.html",
    "admit-card": ROOT_DIR / "admit-card.html",
    "result": ROOT_DIR / "result.html",
    "answer-key": ROOT_DIR / "answer-key.html",
    "scholarship": ROOT_DIR / "scholarship.html",
    "syllabus": ROOT_DIR / "syllabus.html",
    "teaching-exams": ROOT_DIR / "teaching-exams.html",
    "entrance-exams": ROOT_DIR / "entrance-exams.html",
    "government-schemes": ROOT_DIR / "government-schemes.html",

    # Main location buckets
    "uttarakhand-jobs": ROOT_DIR / "uttarakhand-jobs.html",
    "central-government-jobs": ROOT_DIR / "central-government-jobs.html",
    "other-state-jobs": ROOT_DIR / "other-state-jobs.html",

    # Uttarakhand specific categories
    "ukpsc": ROOT_DIR / "ukpsc.html",
    "uksssc": ROOT_DIR / "uksssc.html",
    "high-court": ROOT_DIR / "high-court.html",
    "forest": ROOT_DIR / "forest.html",
    "police": ROOT_DIR / "police.html",

    # Other state specific categories
    "andhra-pradesh-jobs": ROOT_DIR / "andhra-pradesh-jobs.html",
    "arunachal-pradesh-jobs": ROOT_DIR / "arunachal-pradesh-jobs.html",
    "assam-jobs": ROOT_DIR / "assam-jobs.html",
    "chhattisgarh-jobs": ROOT_DIR / "chhattisgarh-jobs.html",
    "goa-jobs": ROOT_DIR / "goa-jobs.html",
    "gujarat-jobs": ROOT_DIR / "gujarat-jobs.html",
    "haryana-jobs": ROOT_DIR / "haryana-jobs.html",
    "himachal-pradesh-jobs": ROOT_DIR / "himachal-pradesh-jobs.html",
    "jharkhand-jobs": ROOT_DIR / "jharkhand-jobs.html",
    "karnataka-jobs": ROOT_DIR / "karnataka-jobs.html",
    "kerala-jobs": ROOT_DIR / "kerala-jobs.html",
    "maharashtra-jobs": ROOT_DIR / "maharashtra-jobs.html",
    "manipur-jobs": ROOT_DIR / "manipur-jobs.html",
    "meghalaya-jobs": ROOT_DIR / "meghalaya-jobs.html",
    "mizoram-jobs": ROOT_DIR / "mizoram-jobs.html",
    "nagaland-jobs": ROOT_DIR / "nagaland-jobs.html",
    "odisha-jobs": ROOT_DIR / "odisha-jobs.html",
    "punjab-jobs": ROOT_DIR / "punjab-jobs.html",
    "sikkim-jobs": ROOT_DIR / "sikkim-jobs.html",
    "tamil-nadu-jobs": ROOT_DIR / "tamil-nadu-jobs.html",
    "telangana-jobs": ROOT_DIR / "telangana-jobs.html",
    "tripura-jobs": ROOT_DIR / "tripura-jobs.html",
    "west-bengal-jobs": ROOT_DIR / "west-bengal-jobs.html",
    "up-government-jobs": ROOT_DIR / "up-government-jobs.html",
    "bihar-jobs": ROOT_DIR / "bihar-jobs.html",
    "rajasthan-jobs": ROOT_DIR / "rajasthan-jobs.html",
    "mp-jobs": ROOT_DIR / "mp-jobs.html",
}

# ==========================================================
# Category Markers
# ==========================================================

START_MARKER = "<!-- AUTO_CATEGORY_START -->"

END_MARKER = "<!-- AUTO_CATEGORY_END -->"

# ==========================================================
# Helpers
# ==========================================================

def safe(value, default=""):

    if value is None:
        return default

    return str(value).strip()


def slugify(title, job=None):
    return canonical_slug(title, job)


def get_image(job):

    return (

        job.get("featured_image")

        or job.get("thumbnail")

        or job.get("image")

        or "images/default-job.png"

    )


def category(job):

    return safe(

        job.get("category"),

        "latest-jobs"

    ).lower()


logger.info(
    "Category Generator V5 Part 1 Loaded Successfully"
)
# ==========================================================
# Category Generator V5
# Part 2 : Category Card Builder
# ==========================================================

def build_category_card(job, page_name=None):
    title = safe(job.get("title"))
    image = get_image(job)
    slug = slugify(title, job)
    description = safe(
        job.get("description"),
        "Click to read complete details."
    )
    last_date = safe(job.get("last_date"), "Check Notification")

    category_labels = {
        "latest-jobs": "Latest Jobs",
        "banking": "Banking Jobs",
        "railway": "Railway Jobs",
        "upsc": "UPSC",
        "ssc": "SSC",
        "teacher-recruitment": "Teacher Recruitment",
        "ctet": "CTET",
        "utet": "UTET",
        "deled": "D.El.Ed",
        "admit-card": "Admit Card",
        "result": "Results",
        "answer-key": "Answer Key",
        "scholarship": "Scholarship",
        "syllabus": "Syllabus",
        "teaching-exams": "Teaching Exams",
        "entrance-exams": "Entrance Exams",
        "government-schemes": "Government Schemes",
        "uttarakhand-jobs": "Uttarakhand Jobs",
        "central-government-jobs": "Central Government Jobs",
        "other-state-jobs": "Other State Jobs",
        "up-government-jobs": "UP Jobs",
        "bihar-jobs": "Bihar Jobs",
        "rajasthan-jobs": "Rajasthan Jobs",
        "mp-jobs": "MP Jobs",
        "forest": "Forest Jobs",
        "police": "Police Jobs",
    }

    # Add all state page names automatically.
    state_labels = {
        key: key.replace("-jobs", "").replace("-", " ").title()
        for key in CATEGORY_FILES
        if key.endswith("-jobs")
    }
    category_labels.update(state_labels)

    label = category_labels.get(
        page_name,
        safe(job.get("category"), "Latest Jobs")
    )

    link = post_relative_url(job)

    return f"""
<div class="card">
    <a href="{link}">
        <img src="{image}" alt="{title}" loading="lazy">
    </a>

    <div class="post-content">
        <span class="category-tag">{label}</span>

        <h3>
            <a href="{link}">{title}</a>
        </h3>

        <p>{description}</p>

        <div class="post-meta">
            <span>📅 {last_date}</span>
        </div>

        <a class="read-more-btn" href="{link}">
            Read More →
        </a>
    </div>
</div>
"""

# ==========================================================
# Sidebar List Item
# ==========================================================

def build_sidebar_item(job):

    title = safe(job.get("title"))

    slug = slugify(title, job)

    return f"""
<li>

    <a href="generated/posts/{slug}.html">

        {title}

    </a>

</li>
"""


# ==========================================================
# Featured Card
# ==========================================================

def build_featured_card(job):

    title = safe(job.get("title"))

    slug = slugify(title, job)

    image = get_image(job)

    return f"""
<div class="featured-post">

    <a href="generated/posts/{slug}.html">

        <img
            src="{image}"
            alt="{title}"
            loading="lazy">

        <h2>

            {title}

        </h2>

    </a>

</div>
"""


# ==========================================================
# Register Category Item
# ==========================================================

def create_category_item(job):

    return {

        "card": build_category_card(job),

        "sidebar": build_sidebar_item(job),

        "featured": build_featured_card(job)

    }


logger.info(
    "Category Generator V5 Part 2 Loaded Successfully"
)
# ==========================================================
# Category Generator V5
# Part 3 : Category Detection Engine
# ==========================================================

CATEGORY_RULES = {
    "banking": [
        "bank", "ibps", "sbi", "rbi", "pnb", "canara", "boi",
        "union bank", "bank of baroda"
    ],
    "railway": [
        "railway", "rrb", "rrc", "metro rail"
    ],
    "upsc": [
        "upsc", "nda", "cds", "civil services", "ies", "ifs"
    ],
    "ssc": [
        "ssc", "cgl", "chsl", "mts", "gd", "stenographer", "selection post"
    ],
    "teacher-recruitment": [
        "teacher", "lecturer", "assistant professor", "principal",
        "tgt", "pgt", "education department"
    ],
    "ctet": ["ctet"],
    "utet": ["utet", "uktet"],
    "deled": ["d.el.ed", "deled", "btc"],
    "admit-card": ["admit card", "hall ticket", "call letter"],
    "result": ["result", "merit list", "score card", "scorecard"],
    "answer-key": ["answer key", "provisional answer key", "final answer key"],
    "scholarship": ["scholarship", "nsp", "fellowship", "financial assistance"],
    "uttarakhand-jobs": [
        "uttarakhand", "उत्तराखंड", "ukpsc", "uksssc", "ukmssb",
        "ubse", "uktet", "uk.gov.in", "psc.uk.gov.in", "sssc.uk.gov.in"
    ],
    "central-government-jobs": [
        "central government", "government of india", "union government",
        "ministry of", "upsc", "ssc", "ibps", "sbi", "rbi",
        "railway", "rrb", "rrc", "lic", "nicl", "defence",
        "indian army", "indian navy", "air force", "psu"
    ],
    "latest-jobs": [
        "recruitment", "vacancy", "notification", "apply online", "job"
    ],
    "syllabus": ["syllabus", "exam pattern"],
    "government-schemes": ["scheme", "yojana", "government scheme"],
    "teaching-exams": ["ctet", "utet", "tet", "teacher eligibility"],
    "entrance-exams": ["neet", "jee", "cuet", "gate", "cat"],

    # Other-state detection rules
    "andhra-pradesh-jobs": ["andhra pradesh", "andhra", "ap govt", "ap government"],
    "arunachal-pradesh-jobs": ["arunachal pradesh", "arunachal"],
    "assam-jobs": ["assam government", "assam govt", "assam", "apsc"],
    "chhattisgarh-jobs": ["chhattisgarh", "chhattisgarh government", "cg govt", "cgpsc"],
    "goa-jobs": ["goa government", "goa govt", "goa"],
    "gujarat-jobs": ["gujarat government", "gujarat govt", "gujarat", "gpsc"],
    "haryana-jobs": ["haryana government", "haryana govt", "haryana", "hpsc"],
    "himachal-pradesh-jobs": ["himachal pradesh", "himachal govt", "himachal government", "hppsc"],
    "jharkhand-jobs": ["jharkhand", "jharkhand government", "jharkhand govt", "jpsc"],
    "karnataka-jobs": ["karnataka", "karnataka government", "karnataka govt", "kpsc"],
    "kerala-jobs": ["kerala", "kerala government", "kerala govt", "kerala psc", "kpsc kerala"],
    "maharashtra-jobs": ["maharashtra", "maharashtra government", "maharashtra govt", "mpsc"],
    "manipur-jobs": ["manipur", "manipur government", "manipur govt", "mpsc manipur"],
    "meghalaya-jobs": ["meghalaya", "meghalaya government", "meghalaya govt", "mpsc meghalaya"],
    "mizoram-jobs": ["mizoram", "mizoram government", "mizoram govt", "mpsc mizoram"],
    "nagaland-jobs": ["nagaland", "nagaland government", "nagaland govt", "npsc"],
    "odisha-jobs": ["odisha", "odisha government", "odisha govt", "opsc", "odisha police"],
    "punjab-jobs": ["punjab", "punjab government", "punjab govt", "ppsc"],
    "sikkim-jobs": ["sikkim", "sikkim government", "sikkim govt", "spsc"],
    "tamil-nadu-jobs": ["tamil nadu", "tamilnadu", "tamil nadu government", "tn govt", "tnpsc"],
    "telangana-jobs": ["telangana", "telangana government", "telangana govt", "tspsc"],
    "tripura-jobs": ["tripura", "tripura government", "tripura govt", "tpsc"],
    "west-bengal-jobs": ["west bengal", "west bengal government", "west bengal govt", "wbpsc"],
    "up-government-jobs": [
        "uttar pradesh", "up government", "up govt", "upsssc", "uppsc", "up police"
    ],
    "bihar-jobs": ["bihar government", "bihar govt", "bihar", "bpsc", "bihar police"],
    "rajasthan-jobs": [
        "rajasthan government", "rajasthan govt", "rajasthan", "rpsc", "rajasthan police"
    ],
    "mp-jobs": [
        "madhya pradesh", "madhya pradesh government", "mp government",
        "mp govt", "mppsc", "mp police"
    ],
    "forest": ["forest department", "forest guard", "forester", "forest ranger"],
    "police": ["police recruitment", "police constable", "sub inspector", "head constable", "police vacancy"],
}


# ==========================================================
# Detect Category
# ==========================================================

def detect_categories(job):
    """Strict multi-category routing.

    A post may appear in multiple relevant pages, but only when the post itself
    contains a strong signal for that page.  In particular, UKSSSC must never
    be mistaken for SSC and a generic ``.gov.in`` URL must never be treated as
    a category signal.
    """
    raw_category = safe(job.get("category")).lower().strip()
    title = safe(job.get("title"))
    meta_text = " ".join([
        title,
        safe(job.get("department")),
        safe(job.get("url")),
        safe(job.get("source")),
        safe(job.get("state")),
        safe(job.get("organization")),
        raw_category,
    ]).lower()
    full_text = (meta_text + " " + safe(job.get("description")) + " " + safe(job.get("notification_text"))).lower()
    # Use title/meta for specific category detection.  Scraped body text often
    # contains unrelated navigation words such as "entrance", "police", etc.
    text = meta_text

    matched=[]
    def add(page):
        if page in CATEGORY_FILES and page not in matched:
            matched.append(page)

    # ---------- strong organization/location signals ----------
    uk = any(x in text for x in (
        "uttarakhand", "उत्तराखंड", "ukpsc", "uksssc", "ukmssb", "ubse",
        "uktet", "uk.gov.in", "psc.uk.gov.in", "sssc.uk.gov.in",
        "uttarakhand high court", "high court of uttarakhand",
        "uttarakhand police", "uttarakhand forest"
    ))
    ukpsc = any(x in text for x in ("ukpsc", "uttarakhand public service commission", "psc.uk.gov.in"))
    uksssc = any(x in text for x in ("uksssc", "uttarakhand subordinate service selection commission", "sssc.uk.gov.in"))
    highcourt = any(x in text for x in ("uttarakhand high court", "high court of uttarakhand", "highcourtuttarakhand"))
    ukforest = any(x in text for x in ("uttarakhand forest", "uttarakhand forest department", "uttarakhand forest guard", "uttarakhand forester"))
    ukpolice = any(x in text for x in ("uttarakhand police", "uk police", "uttarakhand police constable", "uttarakhand police si"))

    # Specific UK pages first.  These are never inferred from a generic word.
    if uk:
        add("uttarakhand-jobs")
        if ukpsc: add("ukpsc")
        if uksssc: add("uksssc")
        if highcourt: add("high-court")
        if ukforest: add("forest")
        if ukpolice: add("police")

    # ---------- national organization signals ----------
    # Exclude UKSSSC from SSC detection.
    ssc = (not uksssc) and any(x in text for x in (
        "staff selection commission", "ssc.gov.in", "ssc cgl", "ssc chsl",
        "ssc mts", "ssc gd", "ssc je", "ssc jht", "ssc stenographer",
        "selection post", "staff selection"
    ))
    upsc = any(x in text for x in ("upsc.gov.in", "union public service commission", "upsc recruitment", "upsc cse", "civil services examination"))
    banking = any(x in text for x in (
        "ibps", "ibps.in", "sbi recruitment", "sbi.co.in", "state bank of india",
        "reserve bank of india", "rbi.org.in", "bank of india", "bank of baroda",
        "punjab national bank", "pnb bank", "canara bank", "union bank", "bank recruitment",
        "banking recruitment", "bank officer", "bank clerk", "probationary officer", "specialist officer"
    ))
    railway = any(x in text for x in (
        "indian railways", "railway recruitment", "railway vacancy", "rrb ", "rrb.",
        "rrbcdg", "railway recruitment board", "railway recruitment cell", "rrc ", "metro rail"
    ))
    teacher = any(x in text for x in (
        "teacher recruitment", "assistant professor", "associate professor", "professor recruitment",
        "lecturer recruitment", "school teacher", "teacher vacancy", "tgt", "pgt", "ctet", "utet"
    )) or bool(re.search(r"\btet\b", text))
    scholarship = any(x in text for x in ("scholarship", "छात्रवृत्ति", "national scholarship portal", "nsp scholarship"))
    answer_key = any(x in text for x in ("answer key", "उत्तर कुंजी", "answer-key", "उत्तरकुंजी"))
    admit = any(x in text for x in ("admit card", "admit-card", "hall ticket", "call letter", "प्रवेश पत्र"))
    result = any(x in text for x in ("result", "results", "merit list", "scorecard", "परिणाम", "मेरिट सूची"))
    syllabus = any(x in text for x in ("syllabus", "indicative syllabus", "पाठ्यक्रम"))
    entrance = any(x in text for x in (
        "entrance exam", "entrance test", "admission test", "neet", "jee", "cuet",
        "university entrance", "common entrance", "entrance examination"
    )) or bool(re.search(r"\b(?:gate|cat)\b", text))
    scheme = any(x in text for x in ("government scheme", "govt scheme", "yojana", "योजना", "government schemes"))
    forest_generic = any(x in text for x in ("forest department", "forest guard", "forest ranger", "forest officer", "forest service", "forester")) or bool(re.search(r"\bforest\b", text))
    police_generic = any(x in text for x in ("police recruitment", "police constable", "sub inspector", "head constable", "police vacancy", "police department"))

    if ssc: add("ssc")
    if upsc: add("upsc")
    if banking: add("banking")
    if railway: add("railway")
    if scholarship: add("scholarship")
    if answer_key: add("answer-key")
    if admit: add("admit-card")
    if result: add("result")
    if syllabus: add("syllabus")
    if entrance: add("entrance-exams")
    if scheme: add("government-schemes")
    if teacher: add("teacher-recruitment")
    if "ctet" in text: add("ctet")
    if "utet" in text or "uktet" in text: add("utet")
    if "d.el.ed" in text or "d.el.ed" in text or "deled" in text: add("deled")
    if forest_generic: add("forest")
    if police_generic: add("police")

    # ---------- state buckets ----------
    other_state = {
        "up-government-jobs": ("uttar pradesh", "uppsc", "upsssc", "up police"),
        "bihar-jobs": ("bihar", "bpsc", "bihar police"),
        "rajasthan-jobs": ("rajasthan", "rpsc", "rajasthan police"),
        "mp-jobs": ("madhya pradesh", "mppsc", "mp police"),
        "andhra-pradesh-jobs": ("andhra pradesh", "ap government"),
        "arunachal-pradesh-jobs": ("arunachal pradesh",),
        "assam-jobs": ("assam", "apsc"),
        "chhattisgarh-jobs": ("chhattisgarh", "cgpsc"),
        "goa-jobs": ("goa government", "goa govt"),
        "gujarat-jobs": ("gujarat", "gpsc"),
        "haryana-jobs": ("haryana", "hpsc"),
        "himachal-pradesh-jobs": ("himachal pradesh", "hppsc"),
        "jharkhand-jobs": ("jharkhand", "jpsc"),
        "karnataka-jobs": ("karnataka", "kpsc"),
        "kerala-jobs": ("kerala", "kerala psc"),
        "maharashtra-jobs": ("maharashtra", "mpsc"),
        "manipur-jobs": ("manipur",), "meghalaya-jobs": ("meghalaya",),
        "mizoram-jobs": ("mizoram",), "nagaland-jobs": ("nagaland", "npsc"),
        "odisha-jobs": ("odisha", "opsc"), "punjab-jobs": ("punjab", "ppsc"),
        "sikkim-jobs": ("sikkim", "spsc"), "tamil-nadu-jobs": ("tamil nadu", "tnpsc"),
        "telangana-jobs": ("telangana", "tspsc"), "tripura-jobs": ("tripura", "tpsc"),
        "west-bengal-jobs": ("west bengal", "wbpsc"),
    }
    if not uk:
        for page, signals in other_state.items():
            if any(x in text for x in signals):
                add("other-state-jobs"); add(page); break

    # Main content category / fallback.
    category_map = {
        "latest jobs":"latest-jobs", "latest job":"latest-jobs", "recruitment":"latest-jobs",
        "result":"result", "results":"result", "admit card":"admit-card", "answer key":"answer-key",
        "scholarship":"scholarship", "syllabus":"syllabus", "teaching exams":"teaching-exams",
        "teaching exam":"teaching-exams", "entrance exams":"entrance-exams", "entrance exam":"entrance-exams",
        "government schemes":"government-schemes", "government scheme":"government-schemes",
        "banking jobs":"banking", "banking":"banking", "railway jobs":"railway", "railway":"railway",
        "uttarakhand jobs":"uttarakhand-jobs", "central jobs":"central-government-jobs",
        "central government jobs":"central-government-jobs", "other state jobs":"other-state-jobs",
        "forest":"forest", "forest jobs":"forest", "police":"police", "police jobs":"police",
        "upsc":"upsc", "ssc":"ssc", "ctet":"ctet", "utet":"utet", "deled":"deled",
    }
    if raw_category in category_map:
        page=category_map[raw_category]
        # Never allow a generic raw category to turn a UK post into SSC.
        if page == "ssc" and uksssc: pass
        else: add(page)

    # Generic recruitment posts go to Latest Jobs, but this must not be the
    # only classification when a strong specific page was detected above.
    recruitment = any(x in full_text for x in (
        "recruitment", "vacancy", "advertisement", "advt", "applications are invited", "online application", "भर्ती", "रिक्ति", "विज्ञापन"
    ))
    if recruitment or raw_category in {"recruitment", "government jobs", "latest jobs", "latest job"}:
        add("latest-jobs")

    # Location bucket: UK, Central, or Other State. Do not use the word
    # 'ssc' alone for Central because UKSSSC contains it.
    if uk:
        add("uttarakhand-jobs")
    elif any(x in text for x in (
        "government of india", "union government", "ministry of", "upsc.gov.in", "ssc.gov.in",
        "ibps", "sbi.co.in", "railway recruitment", "indian railways", "rrbcdg"
    )) or ssc or upsc or banking or railway:
        add("central-government-jobs")
    elif any(x in text for signals in other_state.values() for x in signals):
        add("other-state-jobs")

    if not matched:
        add("latest-jobs")
    return matched


# ==========================================================
# Strict Freshness Filter for Category Pages
# ==========================================================

ACTIVE_JOB_CATEGORIES = {
    "latest jobs", "latest job", "recruitment", "banking", "banking jobs",
    "railway", "railway jobs", "teacher recruitment", "uttarakhand jobs",
    "central jobs", "central government jobs", "other state jobs",
    "up jobs", "up government jobs", "bihar jobs", "rajasthan jobs", "mp jobs",
    "forest", "forest jobs", "police", "police jobs", "government jobs",
}

NON_JOB_CATEGORIES = {
    "result", "results", "admit card", "answer key", "answer keys", "scholarship",
    "syllabus", "teaching exams", "entrance exams", "government schemes", "ctet", "utet", "deled",
}

NOISE_TITLES = {
    "apply online", "apply now", "recruitment", "recruitments", "recruitment notices",
    "application forms", "application form", "apply links", "recruitment/admission links",
    "results", "answer keys", "question bank online exam", "forget password", "login",
    "vacancy", "vacancies", "vacancy/nia", "vacancy position", "download interview letter",
    "download hindi notification",
}

_MONTHS = {
    "january":1,"jan":1,"february":2,"feb":2,"march":3,"mar":3,"april":4,"apr":4,
    "may":5,"june":6,"jun":6,"july":7,"jul":7,"august":8,"aug":8,"september":9,
    "sep":9,"sept":9,"october":10,"oct":10,"november":11,"nov":11,"december":12,"dec":12,
}

def _fresh_parse_date(value):
    if not value:return None
    text=re.sub(r"\s+"," ",str(value).strip())
    m=re.search(r"\b(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})\b",text)
    if m:
        try:return datetime(int(m.group(1)),int(m.group(2)),int(m.group(3))).date()
        except ValueError:pass
    m=re.search(r"\b(\d{1,2})[-/.](\d{1,2})[-/.](20\d{2})\b",text)
    if m:
        try:return datetime(int(m.group(3)),int(m.group(2)),int(m.group(1))).date()
        except ValueError:pass
    mp="|".join(sorted(_MONTHS,key=len,reverse=True))
    m=re.search(rf"\b(\d{{1,2}})\s+({mp})\.?\s+(20\d{{2}})\b",text,re.I)
    if m:
        try:return datetime(int(m.group(3)),_MONTHS[m.group(2).lower().rstrip('.')],int(m.group(1))).date()
        except ValueError:pass
    return None

def _fresh_deadline(job):
    for key in ("last_date","deadline","application_last_date","last_date_to_apply","application_deadline","closing_date"):
        dt=_fresh_parse_date(job.get(key))
        if dt:return dt
    text=" ".join(str(job.get(k,"")) for k in ("title","description","content","last_date"))
    for pattern in [
        r"(?:last\s*date(?:\s*to\s*apply)?|application\s*(?:last\s*)?date|deadline|closing\s*date)\s*[:\-–]?\s*([^|<;]{3,70})",
        r"(?:अंतिम\s*तिथि|अंतिम\s*तारीख|आवेदन\s*की\s*अंतिम\s*तिथि)\s*[:\-–]?\s*([^|<;]{3,70})",
    ]:
        m=re.search(pattern,text,re.I)
        if m:
            dt=_fresh_parse_date(m.group(1))
            if dt:return dt
    return None

def _fresh_year(job):
    text=" ".join(str(job.get(k,"")) for k in ("title","year","tags","keywords"))
    years=[int(x) for x in re.findall(r"\b(20\d{2})\b",text)]
    return max(years) if years else None

def _fresh_is_active(job):
    title=re.sub(r"\s+"," ",str(job.get("title","")).strip()).lower()
    if not title or title in NOISE_TITLES:return False
    deadline=_fresh_deadline(job); today=datetime.now().date()
    if deadline:return deadline>=today
    year=_fresh_year(job)
    if year is not None:return year>=today.year
    for key in ("publish_date","published_date","date_published","posted_date","notification_date","date"):
        dt=_fresh_parse_date(job.get(key))
        if dt:return dt>=today-timedelta(days=120)
    return False

def filter_category_jobs(jobs):
    active=[job for job in jobs if _fresh_is_active(job)]
    logger.info("CATEGORY FRESH FILTER | Input=%d | Active=%d | Removed=%d",len(jobs),len(active),len(jobs)-len(active))
    return active

# ==========================================================
# Group Jobs
# ==========================================================

def group_jobs(jobs):

    grouped = {
        page: []
        for page in CATEGORY_FILES
    }

    for job in jobs:

        pages = detect_categories(job)

        for page in pages:

            grouped[page].append(job)

    return grouped
# ==========================================================
# Category Generator V5
# Part 4 : Category Page Update Engine
# ==========================================================

def replace_category_section(content, items):

    start = content.find(START_MARKER)
    end = content.find(END_MARKER)

    if start == -1 or end == -1:
        return content

    end += len(END_MARKER)

    auto_section = (
        START_MARKER
        + "\n\n"
        + "\n".join(items)
        + "\n\n"
        + END_MARKER
    )

    return (
        content[:start]
        + auto_section
        + content[end:]
    )

# ==========================================================
# Update Category Page
# ==========================================================

def update_category_page(page_name, jobs):

    page = CATEGORY_FILES.get(page_name)

    if not page:

        logger.warning(
            "Unknown Category : %s",
            page_name
        )

        return False

    if not page.exists():

        logger.warning(
            "Missing File : %s",
            page.name
        )

        return False

    with open(
        page,
        "r",
        encoding="utf-8"
    ) as file:

        html = file.read()

    # ======================================================
    # Auto Migration (Manual -> Automation)
    # ======================================================

    if START_MARKER not in html or END_MARKER not in html:

        # ======================================================
        # Force Automation Layout
        # ======================================================

        start = html.find('<div class="post-grid">')

        if start == -1:
            start = html.find('<div class="post-list">')

        end = html.find('<div id="footer">', start)

        if start != -1 and end != -1:

            html = (
                html[:start]
                +
        """
        <div class="post-grid">

        <!-- AUTO_CATEGORY_START -->

        <!-- AUTO_CATEGORY_END -->

        </div>

        """
                +
                html[end:]
            )

        else:

            logger.warning(
                "Unable to locate post section : %s",
                page.name
            )

            return False

    # ======================================================
    # Build Cards
    # ======================================================

    cards = []

    for job in jobs:
        # Never publish a category card whose local generated post does not exist.
        # This removes the 404 links left by older slug versions.
        if not post_exists(job):
            continue
        cards.append(build_category_card(job, page_name))

    if not cards:
        cards.append("""
    <div class="empty-category">
        <h3>No Posts Available</h3>
    </div>
    """)

    # ======================================================
    # Replace Automation Section
    # ======================================================

    html = replace_category_section(
        html,
        cards
    )

    with open(
        page,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(html)

    logger.info(
        "%s Updated (%d Posts)",
        page.name,
        len(cards)
    )

    return True

# ==========================================================
# Update All Categories
# ==========================================================

def update_all_categories(grouped_jobs):

    updated = 0
    skipped = 0

    for page_name, jobs in grouped_jobs.items():

        page = CATEGORY_FILES.get(page_name)

        if page is None:
            logger.warning("Unknown Category : %s", page_name)
            skipped += 1
            continue

        if not page.exists():
            logger.warning("Category Page Missing : %s", page)
            skipped += 1
            continue

        if update_category_page(page_name, jobs):
            updated += 1

    logger.info("=" * 60)
    logger.info("Updated : %d", updated)
    logger.info("Skipped : %d", skipped)
    logger.info("=" * 60)

    return updated
# ==========================================================
# Category Generator V5
# Part 5 : Sorting + Duplicate Removal + Statistics
# ==========================================================

MAX_POSTS_PER_CATEGORY = 50


# ==========================================================
# Remove Duplicate Jobs
# ==========================================================

def remove_duplicate_jobs(jobs):

    unique = []

    seen = set()

    for job in jobs:

        slug = slugify(
            safe(job.get("title"))
        )

        if slug in seen:
            continue

        seen.add(slug)

        unique.append(job)

    return unique


# ==========================================================
# Sort Latest First
# ==========================================================

def sort_jobs(jobs):

    def sort_key(job):

        return safe(
            job.get(
                "publish_date",
                datetime.today().strftime("%Y-%m-%d")
            )
        )

    return sorted(
        jobs,
        key=sort_key,
        reverse=True
    )


# ==========================================================
# Optimize Category
# ==========================================================

def optimize_category_jobs(jobs):

    jobs = remove_duplicate_jobs(jobs)

    jobs = sort_jobs(jobs)

    return jobs[:MAX_POSTS_PER_CATEGORY]


# ==========================================================
# Optimize All Categories
# ==========================================================

def optimize_categories(grouped_jobs):

    optimized = {}

    for page_name, jobs in grouped_jobs.items():

        optimized[page_name] = optimize_category_jobs(jobs)

    return optimized


# ==========================================================
# Category Statistics
# ==========================================================

def category_statistics(grouped_jobs):
    logger.info("=" * 60)
    logger.info("Category Generator Statistics")
    logger.info("=" * 60)

    total = 0

    for page_name in sorted(grouped_jobs.keys()):
        count = len(grouped_jobs[page_name])
        total += count

        logger.info(
            "%-30s : %3d",
            page_name,
            count
        )

    logger.info("=" * 60)
    logger.info("Total Categorized Posts : %d", total)
    logger.info("=" * 60)



logger.info(
    "Category Generator V5 Part 5 Loaded Successfully"
)
# ==========================================================
# Category Generator V5
# Part 6 : Final Build + Validation + Runner
# ==========================================================

# ==========================================================
# Validate Category Files
# ==========================================================

def validate_category_files():
    """
    Validate every category page registered in CATEGORY_FILES.

    Missing pages are logged but do not stop the complete build.
    This is intentionally dynamic so newly added UK/state pages are
    automatically included in validation.
    """

    existing = 0
    missing = 0

    logger.info("=" * 60)
    logger.info("Category File Validation")
    logger.info("=" * 60)

    for page_name, page in CATEGORY_FILES.items():
        if page.exists():
            existing += 1
        else:
            missing += 1
            logger.warning(
                "Category Page Missing : %s -> %s",
                page_name,
                page
            )

    logger.info(
        "Category Files : %d existing / %d missing",
        existing,
        missing
    )
    logger.info("=" * 60)

    return missing == 0


# ==========================================================
# Build Categories
# ==========================================================

def build_categories(jobs):

    logger.info(
        "Starting Category Generation..."
    )

    jobs = filter_category_jobs(jobs)
    grouped = group_jobs(jobs)

    # Log the three main location buckets prominently.
    logger.info(
        "LOCATION ROUTING | Uttarakhand=%d | Central=%d | Other State=%d",
        len(grouped.get("uttarakhand-jobs", [])),
        len(grouped.get("central-government-jobs", [])),
        len(grouped.get("other-state-jobs", [])),
    )

    logger.info(
        "UK SPECIFIC | UKPSC=%d | UKSSSC=%d | High Court=%d | Forest=%d | Police=%d",
        len(grouped.get("ukpsc", [])),
        len(grouped.get("uksssc", [])),
        len(grouped.get("high-court", [])),
        len(grouped.get("forest", [])),
        len(grouped.get("police", [])),
    )

    grouped = optimize_categories(grouped)

    category_statistics(grouped)

    updated = update_all_categories(grouped)

    logger.info(
        "Updated %d Category Pages",
        updated
    )

    return updated


# ==========================================================
# Complete Build
# ==========================================================

def build(jobs):

    validate_category_files()

    result = build_categories(jobs)

    logger.info(
        "Category Generator Completed Successfully."
    )

    return result


# ==========================================================
# Main Runner
# ==========================================================

def run(jobs):

    try:

        return build(jobs)

    except Exception as error:

        logger.exception(
            "Category Generator Error : %s",
            error
        )

        return 0


logger.info("=" * 60)
logger.info("Category Generator V5 Loaded Successfully")
logger.info("=" * 60)
