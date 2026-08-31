# ==========================================================
# Category Generator V4
# Part 1 : Imports + Configuration + Helpers
# ==========================================================

import re
import logging
from pathlib import Path
from datetime import datetime
from url_utils import post_relative_url

logger = logging.getLogger("CategoryGeneratorV4")

ROOT_DIR = Path(__file__).resolve().parent.parent

# ==========================================================
# Category Pages
# ==========================================================

def _category_file(preferred_name, legacy_name=None):
    """Resolve category page without changing existing deployments.

    Newer builds use *-jobs.html names for Banking/Railway. Older deployments
    may still have banking.html/railway.html, so prefer the current filename
    when it exists and fall back to the legacy filename only when necessary.
    """
    preferred = ROOT_DIR / preferred_name
    if preferred.exists() or not legacy_name:
        return preferred
    legacy = ROOT_DIR / legacy_name
    return legacy if legacy.exists() else preferred

CATEGORY_FILES = {

    "banking":
        _category_file("banking-jobs.html", "banking.html"),

    "railway":
        _category_file("railway-jobs.html", "railway.html"),

    "upsc":
        ROOT_DIR / "upsc.html",

    "ssc":
        ROOT_DIR / "ssc.html",

    "teacher-recruitment":
        ROOT_DIR / "teacher-recruitment.html",

    "ctet":
        ROOT_DIR / "ctet.html",

    "utet":
        ROOT_DIR / "utet.html",

    "deled":
        ROOT_DIR / "deled.html",

    "admit-card":
        ROOT_DIR / "admit-card.html",

    "result":
        ROOT_DIR / "result.html",

    "answer-key":
        ROOT_DIR / "answer-key.html",

    "scholarship":
        ROOT_DIR / "scholarship.html",

    "uttarakhand-jobs":
        ROOT_DIR / "uttarakhand-jobs.html",

    "central-government-jobs":
        ROOT_DIR / "central-government-jobs.html",

    "other-state-jobs":
        ROOT_DIR / "other-state-jobs.html",

    "andhra-pradesh-jobs":
        ROOT_DIR / "andhra-pradesh-jobs.html",

    "arunachal-pradesh-jobs":
        ROOT_DIR / "arunachal-pradesh-jobs.html",

    "assam-jobs":
        ROOT_DIR / "assam-jobs.html",

    "chhattisgarh-jobs":
        ROOT_DIR / "chhattisgarh-jobs.html",

    "goa-jobs":
        ROOT_DIR / "goa-jobs.html",

    "gujarat-jobs":
        ROOT_DIR / "gujarat-jobs.html",

    "haryana-jobs":
        ROOT_DIR / "haryana-jobs.html",

    "himachal-pradesh-jobs":
        ROOT_DIR / "himachal-pradesh-jobs.html",

    "jharkhand-jobs":
        ROOT_DIR / "jharkhand-jobs.html",

    "karnataka-jobs":
        ROOT_DIR / "karnataka-jobs.html",

    "kerala-jobs":
        ROOT_DIR / "kerala-jobs.html",

    "maharashtra-jobs":
        ROOT_DIR / "maharashtra-jobs.html",

    "manipur-jobs":
        ROOT_DIR / "manipur-jobs.html",

    "meghalaya-jobs":
        ROOT_DIR / "meghalaya-jobs.html",

    "mizoram-jobs":
        ROOT_DIR / "mizoram-jobs.html",

    "nagaland-jobs":
        ROOT_DIR / "nagaland-jobs.html",

    "odisha-jobs":
        ROOT_DIR / "odisha-jobs.html",

    "punjab-jobs":
        ROOT_DIR / "punjab-jobs.html",

    "sikkim-jobs":
        ROOT_DIR / "sikkim-jobs.html",

    "tamil-nadu-jobs":
        ROOT_DIR / "tamil-nadu-jobs.html",

    "telangana-jobs":
        ROOT_DIR / "telangana-jobs.html",

    "tripura-jobs":
        ROOT_DIR / "tripura-jobs.html",

    "west-bengal-jobs":
        ROOT_DIR / "west-bengal-jobs.html",

    "up-government-jobs":
        ROOT_DIR / "up-government-jobs.html",

    "bihar-jobs":
        ROOT_DIR / "bihar-jobs.html",

    "rajasthan-jobs":
        ROOT_DIR / "rajasthan-jobs.html",

    "mp-jobs":
        ROOT_DIR / "mp-jobs.html",

    "forest":
        ROOT_DIR / "forest.html",

    "police":
        ROOT_DIR / "police.html",


    "andhra-pradesh-jobs":
        ROOT_DIR / "andhra-pradesh-jobs.html",

    "arunachal-pradesh-jobs":
        ROOT_DIR / "arunachal-pradesh-jobs.html",

    "assam-jobs":
        ROOT_DIR / "assam-jobs.html",

    "chhattisgarh-jobs":
        ROOT_DIR / "chhattisgarh-jobs.html",

    "goa-jobs":
        ROOT_DIR / "goa-jobs.html",

    "gujarat-jobs":
        ROOT_DIR / "gujarat-jobs.html",

    "haryana-jobs":
        ROOT_DIR / "haryana-jobs.html",

    "himachal-pradesh-jobs":
        ROOT_DIR / "himachal-pradesh-jobs.html",

    "jharkhand-jobs":
        ROOT_DIR / "jharkhand-jobs.html",

    "karnataka-jobs":
        ROOT_DIR / "karnataka-jobs.html",

    "kerala-jobs":
        ROOT_DIR / "kerala-jobs.html",

    "maharashtra-jobs":
        ROOT_DIR / "maharashtra-jobs.html",

    "manipur-jobs":
        ROOT_DIR / "manipur-jobs.html",

    "meghalaya-jobs":
        ROOT_DIR / "meghalaya-jobs.html",

    "mizoram-jobs":
        ROOT_DIR / "mizoram-jobs.html",

    "nagaland-jobs":
        ROOT_DIR / "nagaland-jobs.html",

    "odisha-jobs":
        ROOT_DIR / "odisha-jobs.html",

    "punjab-jobs":
        ROOT_DIR / "punjab-jobs.html",

    "sikkim-jobs":
        ROOT_DIR / "sikkim-jobs.html",

    "tamil-nadu-jobs":
        ROOT_DIR / "tamil-nadu-jobs.html",

    "telangana-jobs":
        ROOT_DIR / "telangana-jobs.html",

    "tripura-jobs":
        ROOT_DIR / "tripura-jobs.html",

    "west-bengal-jobs":
        ROOT_DIR / "west-bengal-jobs.html",

    "up-government-jobs":
        ROOT_DIR / "up-government-jobs.html",

    "bihar-jobs":
        ROOT_DIR / "bihar-jobs.html",

    "rajasthan-jobs":
        ROOT_DIR / "rajasthan-jobs.html",

    "mp-jobs":
        ROOT_DIR / "mp-jobs.html",

    "forest":
        ROOT_DIR / "forest.html",

    "police":
        ROOT_DIR / "police.html",


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


def slugify(title):

    title = safe(title).lower()

    title = re.sub(
        r"[^a-z0-9]+",
        "-",
        title
    )

    title = re.sub(
        r"-+",
        "-",
        title
    )

    return title.strip("-")


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
    "Category Generator V4 Part 1 Loaded Successfully"
)
# ==========================================================
# Category Generator V4
# Part 2 : Category Card Builder
# ==========================================================

def _safe_external_url(value):
    value = safe(value)
    if not value or value == "#":
        return ""
    low = value.lower().split("?",1)[0]
    if low.endswith((".pdf", ".pdf/")) or ".pdf" in low:
        return ""
    return value


def _category_action_for_card(job, page_name=None):
    """Return a uniform internal category action.

    Category-page buttons must always open the generated post first.
    The generated post contains the official application/admit-card/result
    links. This prevents category buttons from accidentally opening a PDF,
    source page, or '#' when an action field is missing.
    """
    ptype = safe(job.get("post_type")).lower()
    category = safe(job.get("category")).lower()
    title = safe(job.get("title")).lower()
    post_link = post_relative_url(job)

    if ptype in {"admit_card", "admit-card", "admit"} or page_name == "admit-card" or "admit card" in title:
        return "🎫 प्रवेश पत्र देखें", post_link, "admit-card-btn"
    if ptype in {"result", "results"} or page_name == "result" or "result" in category or "result" in title:
        return "📊 परिणाम देखें", post_link, "result-card-btn"
    if ptype in {"answer_key", "answer-key"} or page_name == "answer-key" or "answer key" in title:
        return "📄 उत्तर कुंजी देखें", post_link, "answer-key-card-btn"
    if ptype in {"syllabus", "exam_syllabus"} or page_name == "syllabus" or "syllabus" in title:
        return "📚 पाठ्यक्रम देखें", post_link, "syllabus-card-btn"

    if ptype == "recruitment" or page_name in {"latest-jobs", "banking", "railway", "upsc", "ssc", "teacher-recruitment", "uttarakhand-jobs", "central-government-jobs", "other-state-jobs"} or category in {"recruitment", "latest jobs"}:
        return "भर्ती विवरण देखें", post_link, "apply-card-btn"

    return "पोस्ट देखें", post_link, "post-card-btn"


def build_category_card(job, page_name=None):
    """Compact category list row. Titles open the generated post; action opens its official action URL."""
    title = safe(job.get("title"))
    link = post_relative_url(job)
    last_date = safe(job.get("last_date"))
    if not re.search(r"20\d{2}", last_date):
        last_date = ""

    action_label, action_link, action_class = _category_action_for_card(job, page_name)
    category_labels = {
        "latest-jobs":"Latest Jobs", "banking":"Banking Jobs", "railway":"Railway Jobs", "upsc":"UPSC", "ssc":"SSC",
        "teacher-recruitment":"Teacher Recruitment", "ctet":"CTET", "utet":"UTET", "deled":"D.El.Ed",
        "admit-card":"Admit Card", "result":"Results", "answer-key":"Answer Key", "scholarship":"Scholarship",
        "syllabus":"Syllabus", "teaching-exams":"Teaching Exams", "entrance-exams":"Entrance Exams",
        "government-schemes":"Government Schemes", "uttarakhand-jobs":"Uttarakhand Jobs",
        "central-government-jobs":"Central Government Jobs", "other-state-jobs":"Other State Jobs",
        "up-government-jobs":"UP Jobs", "bihar-jobs":"Bihar Jobs", "rajasthan-jobs":"Rajasthan Jobs", "mp-jobs":"MP Jobs",
        "forest":"Forest Jobs", "police":"Police Jobs",
    }
    state_labels={key:key.replace('-jobs','').replace('-',' ').title() for key in CATEGORY_FILES if key.endswith('-jobs')}
    category_labels.update(state_labels)
    label=category_labels.get(page_name, safe(job.get('category'),'Latest Jobs'))

    # Category action buttons are intentionally fixed-size and always clickable.
    date_html = f'<span class="category-date">📅 {last_date}</span>' if last_date else ''

    return f"""
<div class="category-row" style="display:grid;grid-template-columns:minmax(0,1fr) 86px 132px;gap:12px;align-items:center;padding:14px 4px;border-bottom:1px solid #e6e9ef;background:#fff;box-sizing:border-box;">
    <div class="category-row-title" style="min-width:0;">
        <span class="category-tag" style="display:none;">{label}</span>
        <h3 style="margin:0;font-size:15px;line-height:1.45;"><a href="{link}" style="text-decoration:none;color:#164a7b;">{title}</a></h3>
    </div>
    <div class="category-row-date" style="font-size:12px;color:#777;white-space:nowrap;text-align:center;">{date_html}</div>
    <div class="category-row-action" style="width:132px;">
        <a class="{action_class}" style="display:flex;width:132px;height:42px;align-items:center;justify-content:center;padding:0 6px;border-radius:8px;background:#1677f2;color:#fff;text-decoration:none;font-weight:700;font-size:12px;line-height:1.15;text-align:center;box-sizing:border-box;" href="{action_link}">{action_label} →</a>
    </div>
</div>
"""

# ==========================================================
# Sidebar List Item
# ==========================================================

def build_sidebar_item(job):

    title = safe(job.get("title"))

    slug = slugify(title)

    return f"""
<li>

    <a href="{post_relative_url(job)}">

        {title}

    </a>

</li>
"""


# ==========================================================
# Featured Card
# ==========================================================

def build_featured_card(job):

    title = safe(job.get("title"))

    slug = slugify(title)

    image = get_image(job)

    return f"""
<div class="featured-post">

    <a href="{post_relative_url(job)}">

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
    "Category Generator V4 Part 2 Loaded Successfully"
)
# ==========================================================
# Category Generator V4
# Part 3 : Category Detection Engine
# ==========================================================

CATEGORY_RULES = {

    "banking": [
        "bank",
        "ibps",
        "sbi",
        "rbi",
        "pnb",
        "canara",
        "boi",
        "union bank",
        "bank of baroda"
    ],

    "railway": [
        "railway",
        "rrb",
        "rrc",
        "metro rail"
    ],

    "upsc": [
        "upsc",
        "nda",
        "cds",
        "civil services",
        "ies",
        "ifs"
    ],

    "ssc": [
        "ssc",
        "cgl",
        "chsl",
        "mts",
        "gd",
        "stenographer",
        "selection post"
    ],

    "teacher-recruitment": [
        "teacher",
        "lecturer",
        "assistant professor",
        "principal",
        "tgt",
        "pgt",
        "education department"
    ],

    "ctet": [
        "ctet"
    ],

    "utet": [
        "utet",
        "uktet"
    ],

    "deled": [
        "d.el.ed",
        "deled",
        "btc"
    ],

    "admit-card": [
        "admit card",
        "hall ticket",
        "call letter"
    ],

    "result": [
        "result",
        "merit list",
        "score card",
        "scorecard"
    ],

    "answer-key": [
        "answer key",
        "provisional answer key",
        "final answer key"
    ],

    "scholarship": [
        "scholarship",
        "nsp",
        "fellowship",
        "financial assistance"
    ],

    "uttarakhand-jobs": [
        "ukpsc",
        "uttarakhand",
        "ubse",
        "uksssc",
        "ukmssb"
    ],

    "central-government-jobs": [
        "central government",
        "ministry",
        "government of india",
        "psu"
    ],
    "latest-jobs": [
        "recruitment",
        "vacancy",
        "notification",
        "apply online",
        "job"
    ],

    "syllabus": [
        "syllabus",
        "exam pattern"
    ],

    "government-schemes": [
        "scheme",
        "yojana",
        "government scheme"
    ],

    "teaching-exams": [
        "ctet",
        "utet",
        "tet",
        "teacher eligibility"
    ],

    "entrance-exams": [
        "neet",
        "jee",
        "cuet",
        "gate",
        "cat"
    ],

    "andhra-pradesh-jobs": [
        "andhra pradesh",
        "andhra",
        "ap govt",
        "ap government",
    ],

    "arunachal-pradesh-jobs": [
        "arunachal pradesh",
        "arunachal",
    ],

    "assam-jobs": [
        "assam government",
        "assam govt",
        "assam",
        "apsc",
    ],

    "chhattisgarh-jobs": [
        "chhattisgarh",
        "chhattisgarh government",
        "cg govt",
        "cgpsc",
    ],

    "goa-jobs": [
        "goa government",
        "goa govt",
        "goa",
    ],

    "gujarat-jobs": [
        "gujarat government",
        "gujarat govt",
        "gujarat",
        "gpsc",
    ],

    "haryana-jobs": [
        "haryana government",
        "haryana govt",
        "haryana",
        "hpsc",
    ],

    "himachal-pradesh-jobs": [
        "himachal pradesh",
        "himachal govt",
        "himachal government",
        "hppsc",
    ],

    "jharkhand-jobs": [
        "jharkhand",
        "jharkhand government",
        "jharkhand govt",
        "jpsc",
    ],

    "karnataka-jobs": [
        "karnataka",
        "karnataka government",
        "karnataka govt",
        "kpsc",
    ],

    "kerala-jobs": [
        "kerala",
        "kerala government",
        "kerala govt",
        "kerala psc",
        "kpsc kerala",
    ],

    "maharashtra-jobs": [
        "maharashtra",
        "maharashtra government",
        "maharashtra govt",
        "mpsc",
    ],

    "manipur-jobs": [
        "manipur",
        "manipur government",
        "manipur govt",
        "mpsc manipur",
    ],

    "meghalaya-jobs": [
        "meghalaya",
        "meghalaya government",
        "meghalaya govt",
        "mpsc meghalaya",
    ],

    "mizoram-jobs": [
        "mizoram",
        "mizoram government",
        "mizoram govt",
        "mpsc mizoram",
    ],

    "nagaland-jobs": [
        "nagaland",
        "nagaland government",
        "nagaland govt",
        "npsc",
    ],

    "odisha-jobs": [
        "odisha",
        "odisha government",
        "odisha govt",
        "opsc",
        "odisha police",
    ],

    "punjab-jobs": [
        "punjab",
        "punjab government",
        "punjab govt",
        "ppsc",
    ],

    "sikkim-jobs": [
        "sikkim",
        "sikkim government",
        "sikkim govt",
        "spsc",
    ],

    "tamil-nadu-jobs": [
        "tamil nadu",
        "tamilnadu",
        "tamil nadu government",
        "tn govt",
        "tnpsc",
    ],

    "telangana-jobs": [
        "telangana",
        "telangana government",
        "telangana govt",
        "tspsc",
    ],

    "tripura-jobs": [
        "tripura",
        "tripura government",
        "tripura govt",
        "tpsc",
    ],

    "west-bengal-jobs": [
        "west bengal",
        "west bengal government",
        "west bengal govt",
        "wbpsc",
    ],

    "up-government-jobs": [
        "uttar pradesh",
        "up government",
        "up govt",
        "upsssc",
        "uppsc",
        "up police",
    ],

    "bihar-jobs": [
        "bihar government",
        "bihar govt",
        "bihar",
        "bpsc",
        "bihar police",
    ],

    "rajasthan-jobs": [
        "rajasthan government",
        "rajasthan govt",
        "rajasthan",
        "rpsc",
        "rajasthan police",
    ],

    "mp-jobs": [
        "madhya pradesh",
        "madhya pradesh government",
        "mp government",
        "mp govt",
        "mppsc",
        "mp police",
    ],

    "forest": [
        "forest department",
        "forest guard",
        "forester",
        "forest ranger",
    ],

    "police": [
        "police recruitment",
        "police constable",
        "sub inspector",
        "head constable",
        "police vacancy",
    ],

    }


# ==========================================================
# Detect Category
# ==========================================================

def detect_categories(job):
    """
    Location-aware category routing.

    A post can belong to both:
      - its normal content category (Latest Jobs / Result / Admit Card etc.)
      - one location category (Uttarakhand / Central / Other State)

    Location detection is deliberately checked before generic words such as
    "government", "job", "recruitment" and "notification".
    """

    raw_category = safe(job.get("category")).lower().strip()

    text = " ".join([
        safe(job.get("title")),
        safe(job.get("department")),
        safe(job.get("description")),
        safe(job.get("url")),
        safe(job.get("source")),
        safe(job.get("state")),
        safe(job.get("organization")),
        raw_category,
    ]).lower()

    matched = []

    def add(page):
        if page in CATEGORY_FILES and page not in matched:
            matched.append(page)

    # ----------------------------------------------------------
    # 1. Location routing — highest priority
    # ----------------------------------------------------------

    uk_signals = [
        "uttarakhand",
        "उत्तराखंड",
        "ukpsc",
        "uksssc",
        "ukmssb",
        "ubse",
        "uktet",
        "uk.gov.in",
        "psc.uk.gov.in",
        "sssc.uk.gov.in",
    ]

    central_signals = [
        "central government",
        "government of india",
        "union government",
        "ministry of",
        "upsc",
        "ssc",
        "ibps",
        "sbi",
        "rbi",
        "railway",
        "rrb",
        "rrc",
        "lic",
        "nicl",
        "defence",
        "indian army",
        "indian navy",
        "air force",
        "psu",
        ".gov.in",
    ]

    state_signals = [
        "andhra pradesh", "arunachal pradesh", "assam",
        "bihar", "chhattisgarh", "goa", "gujarat", "haryana",
        "himachal pradesh", "jharkhand", "karnataka", "kerala",
        "madhya pradesh", "maharashtra", "manipur", "meghalaya",
        "mizoram", "nagaland", "odisha", "punjab", "rajasthan",
        "sikkim", "tamil nadu", "telangana", "tripura",
        "uttar pradesh", "west bengal", "delhi government",
        "jammu and kashmir", "ladakh",
        "uppsc", "upsssc", "bpsc", "rpsc", "mppsc", "hpsc",
        "hppsc", "jpsc", "kpsc", "mpsc", "ppsc", "opsc",
        "tnpsc", "tspsc", "wbpsc",
    ]

    # Location routing must use explicit state/central signals first.
    # A generic ".gov.in" URL is NOT enough to classify a post as Central
    # Government because almost every State Government portal also uses it.
    if any(signal in text for signal in uk_signals):
        add("uttarakhand-jobs")

    elif any(signal in text for signal in state_signals):
        # Keep generic Other State page as the common state bucket.
        add("other-state-jobs")

        # Also route to a specific state page where available.
        state_pages = {
            "up-government-jobs": [
                "uttar pradesh", "up government", "up govt",
                "uppsc", "upsssc", "up police"
            ],
            "bihar-jobs": ["bihar", "bpsc", "bihar police"],
            "rajasthan-jobs": ["rajasthan", "rpsc", "rajasthan police"],
            "mp-jobs": [
                "madhya pradesh", "mp government", "mp govt",
                "mppsc", "mp police"
            ],
            "andhra-pradesh-jobs": ["andhra pradesh", "andhra", "ap government"],
            "arunachal-pradesh-jobs": ["arunachal pradesh", "arunachal"],
            "assam-jobs": ["assam", "apsc"],
            "chhattisgarh-jobs": ["chhattisgarh", "cgpsc", "cg govt"],
            "goa-jobs": ["goa government", "goa govt"],
            "gujarat-jobs": ["gujarat", "gpsc"],
            "haryana-jobs": ["haryana", "hpsc"],
            "himachal-pradesh-jobs": ["himachal pradesh", "hppsc"],
            "jharkhand-jobs": ["jharkhand", "jpsc"],
            "karnataka-jobs": ["karnataka", "kpsc"],
            "kerala-jobs": ["kerala", "kerala psc"],
            "maharashtra-jobs": ["maharashtra", "mpsc"],
            "manipur-jobs": ["manipur"],
            "meghalaya-jobs": ["meghalaya"],
            "mizoram-jobs": ["mizoram"],
            "nagaland-jobs": ["nagaland", "npsc"],
            "odisha-jobs": ["odisha", "opsc", "odisha police"],
            "punjab-jobs": ["punjab", "ppsc"],
            "sikkim-jobs": ["sikkim", "spsc"],
            "tamil-nadu-jobs": ["tamil nadu", "tamilnadu", "tnpsc"],
            "telangana-jobs": ["telangana", "tspsc"],
            "tripura-jobs": ["tripura", "tpsc"],
            "west-bengal-jobs": ["west bengal", "wbpsc"],
        }

        for page, signals in state_pages.items():
            if any(signal in text for signal in signals):
                add(page)
                break

    elif any(signal in text for signal in central_signals):
        add("central-government-jobs")

    else:
        # Explicit generic Other State category remains available.
        if raw_category in ("other state jobs", "other state job"):
            add("other-state-jobs")

    # ----------------------------------------------------------
    # 2. Normal content/category routing
    # ----------------------------------------------------------

    category_map = {
        "latest jobs": "latest-jobs",
        "latest job": "latest-jobs",
        "recruitment": "latest-jobs",
        "result": "result",
        "results": "result",
        "admit card": "admit-card",
        "admit cards": "admit-card",
        "answer key": "answer-key",
        "answer keys": "answer-key",
        "scholarship": "scholarship",
        "syllabus": "syllabus",
        "teaching exams": "teaching-exams",
        "teaching exam": "teaching-exams",
        "entrance exams": "entrance-exams",
        "entrance exam": "entrance-exams",
        "government schemes": "government-schemes",
        "government scheme": "government-schemes",
        "banking jobs": "banking",
        "banking": "banking",
        "railway jobs": "railway",
        "railway": "railway",
        "uttarakhand jobs": "uttarakhand-jobs",
        "central jobs": "central-government-jobs",
        "central government jobs": "central-government-jobs",
        "other state jobs": "other-state-jobs",
        "up government jobs": "up-government-jobs",
        "up jobs": "up-government-jobs",
        "bihar jobs": "bihar-jobs",
        "rajasthan jobs": "rajasthan-jobs",
        "mp jobs": "mp-jobs",
        "forest": "forest",
        "forest jobs": "forest",
        "police": "police",
        "police jobs": "police",
        "upsc": "upsc",
        "ssc": "ssc",
        "ctet": "ctet",
        "utet": "utet",
        "deled": "deled",
    }

    if raw_category in category_map:
        add(category_map[raw_category])

    # ----------------------------------------------------------
    # 3. Keyword fallback for content category
    # ----------------------------------------------------------
    # Never infer Government Schemes from a recruitment/latest-jobs record.
    # Scheme pages are opt-in: the source category or a clear scheme/yojana
    # title must say so. This fixes recruitment posts leaking into schemes.
    if raw_category not in {"government schemes", "government scheme"}:
        blocked = {"government-schemes"}
    else:
        blocked = set()

    if not any(page in matched for page in [
        "latest-jobs", "result", "admit-card", "answer-key",
        "scholarship", "syllabus", "teaching-exams",
        "entrance-exams", "banking", "railway", "upsc", "ssc",
        "ctet", "utet", "deled", "forest", "police", "government-schemes"
    ]):
        priority = [
            "admit-card", "answer-key", "result", "scholarship",
            "syllabus", "ctet", "utet", "deled", "teaching-exams",
            "entrance-exams", "banking", "railway", "upsc", "ssc",
            "forest", "police", "latest-jobs"
        ]
        for page in priority:
            if page in blocked:
                continue
            if any(keyword.lower() in text for keyword in CATEGORY_RULES.get(page, [])):
                add(page)
                break

    # Explicit scheme category is kept only for scheme/yojana content.
    if raw_category in {"government schemes", "government scheme"}:
        if any(k in text for k in ("scheme", "yojana", "योजना")):
            add("government-schemes")
        else:
            # Badly labelled records must not enter the scheme page.
            matched = [p for p in matched if p != "government-schemes"]

    # ----------------------------------------------------------
    # 4. Safe fallback
    # ----------------------------------------------------------

    if not matched:
        add("other-state-jobs")

    return matched

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
# Category Generator V4
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
        # Robust Auto Migration (Manual -> Automation)
        # ======================================================
        # Older pages can use different wrappers/classes. Detect the
        # container that actually holds generated-post links instead of
        # relying on one exact <div class="post-grid"> string.
        migrated = False
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            candidates = []
            for node in soup.find_all(["div", "section", "ul"]):
                count = 0
                for a in node.find_all("a", href=True):
                    href = str(a.get("href") or "")
                    clean = href.split("?", 1)[0].split("#", 1)[0]
                    if "generated/posts/" in clean and clean.endswith(".html"):
                        count += 1
                if count >= 1:
                    candidates.append((count, len(node.find_all()), node))

            if candidates:
                # Highest number of post links, then smallest DOM container.
                candidates.sort(key=lambda item: (item[0], -item[1]), reverse=True)
                _, _, container = candidates[0]
                container.clear()
                container.append(soup.new_string("\n" + START_MARKER + "\n" + END_MARKER + "\n"))
                html = str(soup)
                migrated = True
                logger.info("Auto-migrated post container: %s", page.name)
        except Exception:
            logger.exception("BeautifulSoup category migration failed: %s", page.name)

        # Fallback for pages whose old list has no generated-post links.
        if not migrated:
            start = html.find('<div class="post-grid">')
            if start == -1:
                start = html.find('<div class="post-list">')
            if start == -1:
                start = html.find('<div class="posts-grid">')
            end = html.find('<div id="footer">', start) if start != -1 else -1
            if end == -1 and start != -1:
                end = html.find('<footer', start)

            if start != -1 and end != -1:
                marker_block = (
                    '<div class="category-list">\n\n'
                    + START_MARKER + '\n\n'
                    + END_MARKER + '\n\n</div>\n\n'
                )
                html = html[:start] + marker_block + html[end:]
                migrated = True

        if not migrated:
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
        cards.append(build_category_card(job, page_name))

    if not cards:
        cards.append("""
    <div class="empty-category">
        <h3>No Posts Available</h3>
        <p>New updates will appear here automatically.</p>
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
# Category Generator V4
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

    logger.info(
        "Total Categorized Posts : %d",
        total
    )

    logger.info("=" * 60)


logger.info(
    "Category Generator V4 Part 5 Loaded Successfully"
)
# ==========================================================
# Category Generator V4
# Part 6 : Final Build + Validation + Runner
# ==========================================================

# ==========================================================
# Validate Category Files
# ==========================================================

def validate_category_files():

    CATEGORY_FILES = {

    "latest-jobs":
        ROOT_DIR / "latest-jobs.html",

    "banking-jobs":
        ROOT_DIR / "banking-jobs.html",

    "railway-jobs":
        ROOT_DIR / "railway-jobs.html",

    "upsc":
        ROOT_DIR / "upsc.html",

    "ssc":
        ROOT_DIR / "ssc.html",

    "teacher-recruitment":
        ROOT_DIR / "teacher-recruitment.html",

    "ctet":
        ROOT_DIR / "ctet.html",

    "utet":
        ROOT_DIR / "utet.html",

    "deled":
        ROOT_DIR / "deled.html",

    "admit-card":
        ROOT_DIR / "admit-card.html",

    "result":
        ROOT_DIR / "result.html",

    "answer-key":
        ROOT_DIR / "answer-key.html",

    "scholarship":
        ROOT_DIR / "scholarship.html",

    "syllabus":
        ROOT_DIR / "syllabus.html",

    "teaching-exams":
        ROOT_DIR / "teaching-exams.html",

    "entrance-exams":
        ROOT_DIR / "entrance-exams.html",

    "government-schemes":
        ROOT_DIR / "government-schemes.html",

    "uttarakhand-jobs":
        ROOT_DIR / "uttarakhand-jobs.html",

    "central-government-jobs":
        ROOT_DIR / "central-government-jobs.html",

    "other-state-jobs":
        ROOT_DIR / "other-state-jobs.html"
}

# ==========================================================
# Build Categories
# ==========================================================

def build_categories(jobs):

    logger.info(
        "Starting Category Generation..."
    )

    grouped = group_jobs(jobs)

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
logger.info("Category Generator V4 Loaded Successfully")
logger.info("=" * 60)
