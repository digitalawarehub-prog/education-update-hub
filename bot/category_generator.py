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

def escape_html(value):
    import html
    return html.escape(str(value or ""))


def safe(value, default=""):

    if value is None:
        return default

    return str(value).strip()


def slugify(title, job=None):
    return canonical_slug(title, job)


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

def _category_post_type(job):
    title = safe(job.get('title')).lower()
    # Title-level signals override stale legacy post_type values.
    if any(x in title for x in ('admit card','admit-card','hall ticket','hall-ticket','call letter','प्रवेश पत्र')): return 'admit-card'
    if 'answer key' in title or 'उत्तर कुंजी' in title: return 'answer-key'
    if re.search(r'\b(result|merit list|score ?card)\b|परिणाम', title, re.I): return 'result'
    if 'syllabus' in title or 'पाठ्यक्रम' in title: return 'syllabus'
    if 'scholarship' in title or 'छात्रवृत्ति' in title: return 'scholarship'
    p = safe(job.get('post_type')).lower().strip()
    if p in {'admit-card','answer-key','result','syllabus','scholarship','notice','recruitment'}: return p
    return 'recruitment'


def _category_card_meta(job, page_name):
    ptype = _category_post_type(job)
    data = {
        'admit-card': ('🎫 Admit Card','प्रवेश पत्र और परीक्षा तिथि'),
        'result': ('📊 Result','परिणाम और अगला चरण'),
        'answer-key': ('📝 Answer Key','उत्तर कुंजी और objection'),
        'syllabus': ('📚 Syllabus','परीक्षा पैटर्न और पाठ्यक्रम'),
        'scholarship': ('🎓 Scholarship','पात्रता, लाभ और आवेदन'),
    }
    if ptype in data: return data[ptype]
    if page_name == 'government-schemes': return ('🏛️ Government Scheme','योजना, पात्रता और लाभ')
    if page_name in {'teaching-exams','ctet','utet','deled'}: return ('👨‍🏫 Teaching Exam','Eligibility, pattern और dates')
    return ('💼 Recruitment','Vacancy, qualification, salary और dates')


def build_category_card(job, page_name=None):
    title = safe(job.get('title'))
    description = safe(job.get('description'),'पूरी जानकारी देखने के लिए पोस्ट खोलें।')
    last_date = safe(job.get('last_date'))
    if not last_date or last_date.casefold() in {'check notification','not available','not mentioned','official notification'}:
        last_date = 'आधिकारिक सूचना में देखें'
    link = '/' + post_relative_url(job).lstrip('/')
    tag, sub = _category_card_meta(job, page_name)
    ptype = _category_post_type(job)
    action = {'admit-card':'🎫 Admit Card देखें','result':'📊 Result देखें','answer-key':'📝 Answer Key देखें','syllabus':'📚 Syllabus देखें','scholarship':'🎓 Scholarship देखें','notice':'📄 सूचना देखें'}.get(ptype,'🔎 पूरी जानकारी देखें')
    return f"""
<article class="card category-post-card category-{escape_html(ptype)}">
  <div class="post-content">
    <div class="category-card-top"><span class="category-tag">{escape_html(tag)}</span><span class="category-card-type">{escape_html(sub)}</span></div>
    <h3><a href="{escape_html(link)}">{escape_html(title)}</a></h3>
    <p>{escape_html(description[:420])}</p>
    <div class="category-card-info"><span>📅 {escape_html(last_date)}</span></div>
    <a class="read-more-btn" href="{escape_html(link)}">{escape_html(action)} →</a>
  </div>
</article>
"""

# ==========================================================
# Sidebar List Item
# ==========================================================

def build_sidebar_item(job):
    title = safe(job.get("title"))
    link = "/" + post_relative_url(job).lstrip("/")
    return f'<li><a href="{escape_html(link)}">{escape_html(title)}</a></li>'

# ==========================================================
# Featured Card
# ==========================================================

def build_featured_card(job):
    title = safe(job.get("title"))
    link = "/" + post_relative_url(job).lstrip("/")
    return f'<div class="featured-post"><a href="{escape_html(link)}"><h2>{escape_html(title)}</h2></a></div>'

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
        "bank", "banking", "ibps", "sbi", "rbi", "pnb", "canara", "boi",
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
        "teacher", "lecturer", "assistant professor", "professor", "principal",
        "tgt", "pgt", "education department", "polytechnic"
    ],
    "ctet": ["ctet"],
    "utet": ["utet", "uktet"],
    "deled": ["d.el.ed", "deled", "btc"],
    "admit-card": ["admit card", "hall ticket", "hall-ticket", "call letter"],
    "result": ["result", "merit list", "score card", "scorecard"],
    "answer-key": ["answer key", "provisional answer key", "final answer key"],
    "scholarship": ["scholarship", "nsp", "fellowship", "financial assistance"],
    "uttarakhand-jobs": [
        "uttarakhand", "उत्तराखंड", "उत्तराखण्ड", "ukpsc", "uksssc", "ukmssb", "ukssscrecruitment.in",
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
    "forest": ["forest department", "forest guard", "forester", "forest ranger", "forest service", "वन विभाग", "वन रक्षक"],
    "police": ["police recruitment", "police constable", "sub inspector", "head constable", "police vacancy"],
}


# ==========================================================
# Detect Category
# ==========================================================

def _keyword_present(text, keyword):
    """Match category signals without substring collisions (e.g. SSC in UKSSSC)."""
    text = safe(text).lower()
    keyword = safe(keyword).lower()
    if not keyword:
        return False
    if any("\u0900" <= ch <= "\u097f" for ch in keyword):
        return keyword in text
    # Multi-word/URL-like signals may contain punctuation; boundary matching
    # still prevents short tokens such as `ssc` matching inside `uksssc`.
    if re.fullmatch(r"[a-z0-9]+", keyword):
        return re.search(r"(?<![a-z0-9])" + re.escape(keyword) + r"(?![a-z0-9])", text) is not None
    return keyword in text

def _any_keyword(text, keywords):
    return any(_keyword_present(text, item) for item in keywords)


def detect_categories(job):
    """
    Location-aware category routing.

    A post can belong to:
      1. Its main content category (Latest Jobs / Result / Admit Card etc.)
      2. One main location bucket:
         - Uttarakhand
         - Central Government
         - Other State
      3. One specific organization/state page where applicable.

    IMPORTANT:
    - Uttarakhand is checked before Central/Other State.
    - Generic ".gov.in" is NOT treated as Central because every state
      government can also use a .gov.in domain.
    - A state-specific post is never routed to Uttarakhand unless it
      actually contains a Uttarakhand signal.
    """

    raw_category = safe(job.get("category")).lower().strip()

    # Do NOT use scraper `department` as a category signal. Several source
    # pages incorrectly label unrelated notices as "Banking", which was
    # causing Tripura/MP/Uttarakhand posts to enter Banking. Likewise the
    # generic `category` field is often just "Recruitment".
    text = " ".join([
        safe(job.get("title")),
        safe(job.get("description")),
        safe(job.get("url")),
        safe(job.get("source")),
        safe(job.get("official_website")),
        safe(job.get("apply_link")),
        safe(job.get("state")),
        safe(job.get("organization")),
        safe(job.get("content")),
    ]).lower()

    # Infer state/commission from the source domain when the scraped title has
    # no location name. This fixes JPSC/MPPSC/UKSSSC posts being misclassified.
    domain_state_signals = {
        "uksssc.co.in": ["uttarakhand", "uksssc"],
        "sssc.uk.gov.in": ["uttarakhand", "uksssc"],
        "psc.uk.gov.in": ["uttarakhand", "ukpsc"],
        "highcourtofuttarakhand.gov.in": ["uttarakhand", "high court of uttarakhand"],
        "jpsc.gov.in": ["jharkhand", "jpsc"],
        "mppsc.mp.gov.in": ["madhya pradesh", "mppsc"],
        "mponline.gov.in": ["madhya pradesh"],
        "uppsc.up.nic.in": ["uttar pradesh", "uppsc"],
        "upsssc.gov.in": ["uttar pradesh", "upsssc"],
        "rpsc.rajasthan.gov.in": ["rajasthan", "rpsc"],
        "bpsc.bih.nic.in": ["bihar", "bpsc"],
    }
    for domain, signals in domain_state_signals.items():
        if domain in text:
            text += " " + " ".join(signals)

    # Banking detection must not trust generic IBPS registration URLs.
    # Many non-banking recruitments are hosted on ibpsreg.ibps.in.
    banking_text = " ".join([
        safe(job.get("title")),
        safe(job.get("description")),
        safe(job.get("source")),
        safe(job.get("state")),
        safe(job.get("organization")),
        safe(job.get("content")),
    ]).lower()

    # Content-type routing must be based on the post itself, not the entire
    # notification PDF. A recruitment advertisement often contains words such
    # as "call letter", "result", "exam" and "admit" in instructions, which
    # previously polluted Recruitment pages into Admit Card/Result pages.
    primary_content_text = " ".join([
        safe(job.get("title")),
        safe(job.get("description")),
        safe(job.get("url")),
        safe(job.get("source")),
        safe(job.get("state")),
        safe(job.get("organization")),
    ]).lower()

    matched = []

    identity_text = " ".join([
        safe(job.get("title")), safe(job.get("description")), safe(job.get("url")),
        safe(job.get("source")), safe(job.get("organization")), safe(job.get("department")),
        safe(job.get("official_website")), safe(job.get("state"))
    ]).lower()
    state_psc_signals = (
        "jpsc", "jharkhand public service commission", "mppsc", "madhya pradesh public service commission",
        "uppsc", "uttar pradesh public service commission", "rpsc", "rajasthan public service commission",
        "bpsc", "bihar public service commission", "hpsc", "haryana public service commission",
        "hppsc", "himachal pradesh public service commission", "gpsc", "gujarat public service commission",
        "kpsc", "karnataka public service commission", "tnpsc", "tamil nadu public service commission",
        "tspsc", "telangana state public service commission", "opsc", "odisha public service commission",
        "ppsc", "punjab public service commission", "wbpsc", "west bengal public service commission",
        "ukpsc", "uttarakhand public service commission"
    )
    is_state_psc = any(x in identity_text for x in state_psc_signals)
    is_upsc_identity = bool(re.search(r"\bupsc\b", identity_text) or "union public service commission" in identity_text or "upsc.gov.in" in identity_text)

    def add(page):
        if page in CATEGORY_FILES and page not in matched:
            matched.append(page)

    # ----------------------------------------------------------
    # Location signals
    # ----------------------------------------------------------

    uk_signals = [
        "uttarakhand", "उत्तराखंड", "उत्तराखण्ड", "ukpsc", "uksssc", "ukmssb", "ukssscrecruitment.in",
        "ubse", "uktet", "uk.gov.in", "psc.uk.gov.in", "sssc.uk.gov.in",
        "high court of uttarakhand", "uttarakhand high court",
        "uttarakhand police", "uttarakhand forest"
    ]

    central_signals = [
        "central government", "government of india", "union government",
        "ministry of", "upsc", "ssc", "ibps", "sbi", "rbi",
        "railway", "rrb", "rrc", "lic", "nicl", "defence",
        "indian army", "indian navy", "air force", "psu"
    ]

    # Specific Uttarakhand pages
    uk_specific = {
        "ukpsc": [
            "ukpsc", "uttarakhand public service commission",
            "psc.uk.gov.in"
        ],
        "uksssc": [
            "uksssc", "ukssscrecruitment.in", "uttarakhand subordinate service selection commission",
            "sssc.uk.gov.in"
        ],
        "high-court": [
            "uttarakhand high court",
            "high court of uttarakhand",
            "highcourtuttarakhand",
            "highcourtofuttarakhand"
        ],
        "forest": [
            "uttarakhand forest", "uttarakhand forest department",
            "uttarakhand forest guard", "uttarakhand forester", "uttarakhand forest service"
        ],
        "police": [
            "uttarakhand police", "uk police",
            "uttarakhand police constable", "uttarakhand police si"
        ],
    }

    # Specific Other State pages
    state_specific = {
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
        "andhra-pradesh-jobs": [
            "andhra pradesh", "andhra", "ap government", "ap govt"
        ],
        "arunachal-pradesh-jobs": ["arunachal pradesh", "arunachal"],
        "assam-jobs": ["assam", "apsc"],
        "chhattisgarh-jobs": ["chhattisgarh", "cgpsc", "cg govt"],
        "goa-jobs": ["goa government", "goa govt", "goa"],
        "gujarat-jobs": ["gujarat", "gpsc"],
        "haryana-jobs": ["haryana", "hpsc"],
        "himachal-pradesh-jobs": ["himachal pradesh", "hppsc"],
        "jharkhand-jobs": ["jharkhand", "jpsc"],
        "karnataka-jobs": ["karnataka", "kpsc"],
        "kerala-jobs": ["kerala", "kerala psc", "kpsc kerala"],
        "maharashtra-jobs": ["maharashtra", "mpsc"],
        "manipur-jobs": ["manipur", "mpsc manipur"],
        "meghalaya-jobs": ["meghalaya", "mpsc meghalaya"],
        "mizoram-jobs": ["mizoram", "mpsc mizoram"],
        "nagaland-jobs": ["nagaland", "npsc"],
        "odisha-jobs": ["odisha", "opsc", "odisha police"],
        "punjab-jobs": ["punjab", "ppsc"],
        "sikkim-jobs": ["sikkim", "spsc"],
        "tamil-nadu-jobs": ["tamil nadu", "tamilnadu", "tnpsc"],
        "telangana-jobs": ["telangana", "tspsc"],
        "tripura-jobs": ["tripura", "tpsc"],
        "west-bengal-jobs": ["west bengal", "wbpsc"],
    }

    # ----------------------------------------------------------
    # 1. Location routing — highest priority
    # ----------------------------------------------------------

    is_uk = _any_keyword(text, uk_signals)

    if is_uk:
        # Always place Uttarakhand jobs in the common UK bucket.
        add("uttarakhand-jobs")

        # Also place them in their specific UK organization page.
        for page, signals in uk_specific.items():
            if _any_keyword(text, signals):
                add(page)
                break

    else:
        # Never use generic ".gov.in" as a Central signal.
        is_central = _any_keyword(text, central_signals) and not is_state_psc

        if is_central:
            add("central-government-jobs")
        else:
            matched_state_page = None

            for page, signals in state_specific.items():
                if _any_keyword(text, signals):
                    matched_state_page = page
                    break

            if matched_state_page:
                # Every state job gets the common Other State bucket
                # plus its own state page.
                add("other-state-jobs")
                add(matched_state_page)
            elif raw_category in ("other state jobs", "other state job"):
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
        category_page = category_map[raw_category]

        # Scrapers often label UKSSSC/UKPSC notices as generic SSC/UPSC.
        # Never let those generic labels pollute Central/SSC/UPSC pages.
        if (is_uk or is_state_psc) and category_page in {"ssc", "upsc", "central-government-jobs"}:
            category_page = None
        if category_page == "upsc" and not is_upsc_identity:
            category_page = None

        if category_page == "uttarakhand-jobs":
            # Do not trust a stale scraper label; require actual UK signals.
            if is_uk:
                add("uttarakhand-jobs")
        elif category_page == "central-government-jobs":
            if is_central:
                add("central-government-jobs")
        elif category_page == "other-state-jobs":
            if matched_state_page or (not is_central and not is_uk):
                add("other-state-jobs")
        elif category_page:
            add(category_page)

    # ----------------------------------------------------------
    # 3. Independent content routing
    # ----------------------------------------------------------
    # A post can belong to both a location bucket and a content bucket.
    # Do not stop after adding Latest Jobs/Recruitment; otherwise Railway,
    # Banking, Answer Key, Admit Card, Teaching and Scheme pages stay empty.
    direct_content_rules = {
        "banking": CATEGORY_RULES.get("banking", []),
        "railway": CATEGORY_RULES.get("railway", []),
        "upsc": CATEGORY_RULES.get("upsc", []),
        "ssc": CATEGORY_RULES.get("ssc", []),
        "admit-card": CATEGORY_RULES.get("admit-card", []),
        "answer-key": CATEGORY_RULES.get("answer-key", []),
        "result": CATEGORY_RULES.get("result", []),
        "scholarship": CATEGORY_RULES.get("scholarship", []),
        "syllabus": CATEGORY_RULES.get("syllabus", []),
        "teaching-exams": CATEGORY_RULES.get("teaching-exams", []),
        "entrance-exams": CATEGORY_RULES.get("entrance-exams", []),
        "government-schemes": CATEGORY_RULES.get("government-schemes", []),
    }
    for page, signals in direct_content_rules.items():
        if (is_uk or is_state_psc) and page in {"ssc", "upsc"}:
            continue
        if page == "upsc" and not is_upsc_identity:
            continue
        if page == "banking":
            signal_text = banking_text
        else:
            signal_text = primary_content_text
        if _any_keyword(signal_text, signals):
            add(page)

    # ----------------------------------------------------------
    # 4. Keyword fallback for content category
    # ----------------------------------------------------------

    content_pages = {
        "latest-jobs", "result", "admit-card", "answer-key",
        "scholarship", "syllabus", "teaching-exams",
        "entrance-exams", "banking", "railway", "upsc", "ssc",
        "ctet", "utet", "deled", "forest", "police"
    }

    if not any(page in matched for page in content_pages):
        priority = [
            "admit-card", "answer-key", "result", "scholarship",
            "syllabus", "ctet", "utet", "deled", "teaching-exams",
            "entrance-exams", "banking", "railway", "upsc", "ssc",
            "forest", "police", "latest-jobs"
        ]

        for page in priority:
            if page == "upsc" and (is_state_psc or not is_upsc_identity):
                continue
            if page == "banking":
                signal_text = banking_text
            else:
                signal_text = primary_content_text
            if _any_keyword(signal_text, CATEGORY_RULES.get(page, [])):
                add(page)
                break

    # ----------------------------------------------------------
    # 4. Safe fallback
    # ----------------------------------------------------------

    # A post that is not Central/UK and has no identifiable state
    # remains available in Other State only when its category says so.
    # For ordinary recruitment posts, Latest Jobs is the safer fallback.
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
    m=re.match(r"^(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})[T ]",text)
    if m:
        try:return datetime(int(m.group(1)),int(m.group(2)),int(m.group(3))).date()
        except ValueError:pass
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
    title=re.sub(r"\s+"," ",str(job.get("title","" )).strip()).lower()
    if not title or title in NOISE_TITLES:return False
    today=datetime.now().date()
    deadline=_fresh_deadline(job)
    if deadline:return deadline>=today
    year=_fresh_year(job)
    if year is not None and year>=today.year:return True
    # Admit cards, results and other post-exam updates often have no deadline.
    # Their scraper timestamp is the reliable freshness signal.
    for key in ("scraped_at","publish_date","published_date","date_published","posted_date","notification_date","date"):
        dt=_fresh_parse_date(job.get(key))
        if dt:return dt>=today-timedelta(days=90)
    return False

def _category_noise(title, job=None):
    t = re.sub(r"\s+", " ", safe(title)).strip().lower()
    exact = {"view all", "view all results", "view all recruitment", "results", "recruitment", "notification", "advertisement", "apply online", "new registration", "step-1: new registration", "step-1", "recruitment/admission links", "examination", "event key dates"}
    if t in exact or len(t) < 12:
        return True
    bad_text = " ".join(safe((job or {}).get(k)) for k in ("description", "content", "raw_text")).lower()
    for phrase in ("page you’ve requested either does not exist", "page you've requested either does not exist", "go back home previous button", "app store google play facebook", "the page you requested either does not exist"):
        if phrase in bad_text:
            return True
    if any(x in t for x in ("forgot password", "login/register", "login register", "skip to main content")):
        return True
    return False


def _latest_jobs_eligible(job):
    """Latest Jobs contains only recruitment posts with a live application deadline."""
    title = re.sub(r"\s+", " ", safe(job.get("title"))).strip().lower()
    post_type = safe(job.get("post_type")).lower()
    if post_type not in {"recruitment", "job", "jobs", ""} and safe(job.get("category")).lower() not in {"recruitment", "latest jobs", "latest job"}:
        return False
    if any(x in title for x in ("corrigendum", "amendment", "addendum", "notice regarding", "press release", "answer key", "admit card", "result", "syllabus", "scholarship")):
        return False
    deadline = _fresh_deadline(job)
    return bool(deadline and deadline >= datetime.now().date())

def filter_category_jobs(jobs):
    publishable = []
    for job in jobs:
        if _category_noise(job.get("title"), job):
            continue
        if not post_exists(job):
            logger.warning("Skipping missing generated post: %s", safe(job.get("title")))
            continue
        publishable.append(job)
    logger.info("CATEGORY FILTER | Input=%d | Publishable=%d | Removed=%d", len(jobs), len(publishable), len(jobs)-len(publishable))
    return publishable

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
            if page == "latest-jobs" and not _latest_jobs_eligible(job):
                continue
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

        end = html.find('<div id="footer">', start if start >= 0 else 0)

        block = """
        <section class="post-grid">
        <!-- AUTO_CATEGORY_START -->
        <!-- AUTO_CATEGORY_END -->
        </section>
        """

        if start != -1 and end != -1:
            html = html[:start] + block + html[end:]
        elif end != -1:
            # Special/manual pages such as CTET, UTET and D.El.Ed do not have
            # a standard post-grid. Put the automation block immediately
            # before the footer instead of leaving the category disconnected.
            html = html[:end] + block + html[end:]
        else:
            logger.warning("Unable to locate post section/footer : %s", page.name)
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
    </div>
    """)

    # ======================================================
    # Replace Automation Section
    # ======================================================

    html = replace_category_section(
        html,
        cards
    )

    # Category pages are LIST pages only. Never allow a post-detail template
    # (job table, share block, FAQ, related posts or post action block) to leak
    # into a category page after a previous template migration.
    html = re.sub(r'<section[^>]+class=["\'][^"\']*faq-section[^"\']*["\'][\s\S]*?</section>', '', html, flags=re.I)
    html = re.sub(r'<section[^>]+class=["\'][^"\']*share-section[^"\']*["\'][\s\S]*?</section>', '', html, flags=re.I)
    html = re.sub(r'<section[^>]+class=["\'][^"\']*related-posts[^"\']*["\'][\s\S]*?</section>', '', html, flags=re.I)
    html = re.sub(r'<section[^>]+class=["\'][^"\']*next-action[^"\']*["\'][\s\S]*?</section>', '', html, flags=re.I)
    html = re.sub(r'<table[^>]+class=["\'][^"\']*job-table[^"\']*["\'][\s\S]*?</table>', '', html, flags=re.I)

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
        # New records get a stable site_published_at. Older records fall back
        # to their source/publication date. Never use scrape time as primary.
        for key in ("site_published_at", "publish_date", "notification_date", "published_date", "date_published", "posted_date", "date"):
            dt = _fresh_parse_date(job.get(key))
            if dt:
                return dt
        return datetime.min.date()
    return sorted(jobs, key=sort_key, reverse=True)


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
