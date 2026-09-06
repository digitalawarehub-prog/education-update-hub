# ==========================================================
# Category Generator V5
# Part 1 : Imports + Configuration + Helpers
# ==========================================================

import re
import html
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("CategoryGeneratorV5")

ROOT_DIR = Path(__file__).resolve().parent.parent

# ==========================================================
# Category Pages
# ==========================================================

CATEGORY_FILES = {
    # Core categories
    "latest-jobs": ROOT_DIR / "latest-jobs.html",
    "banking": ROOT_DIR / "banking.html",
    "railway": ROOT_DIR / "railway.html",
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
    "Category Generator V5 Part 1 Loaded Successfully"
)
# ==========================================================
# Category Generator V5
# Part 2 : Category Card Builder
# ==========================================================

def _post_link(job):
    link = safe(job.get("html_file"))
    if link:
        return link.replace("\\", "/")
    slug = safe(job.get("slug")) or slugify(safe(job.get("title")))
    return f"generated/posts/{slug}.html"

def _category_button(page_name):
    p = safe(page_name).lower()
    mapping = {
        "latest-jobs":"📋 भर्ती विवरण देखें →", "banking":"🏦 बैंकिंग भर्ती देखें →",
        "railway":"🚆 रेलवे भर्ती देखें →", "upsc":"🎯 UPSC भर्ती देखें →", "ssc":"📝 SSC भर्ती देखें →",
        "teacher-recruitment":"👨‍🏫 शिक्षक भर्ती देखें →", "ctet":"📘 CTET विवरण देखें →",
        "utet":"📗 UTET विवरण देखें →", "deled":"🎓 D.El.Ed विवरण देखें →",
        "admit-card":"🎫 प्रवेश पत्र देखें →", "result":"📊 रिजल्ट देखें →",
        "answer-key":"📄 उत्तर कुंजी देखें →", "scholarship":"🎓 छात्रवृत्ति देखें →",
        "syllabus":"📚 सिलेबस देखें →", "teaching-exams":"🧑‍🏫 परीक्षा विवरण देखें →",
        "entrance-exams":"🎓 प्रवेश परीक्षा देखें →", "government-schemes":"🏛️ योजना विवरण देखें →",
        "uttarakhand-jobs":"🏔️ उत्तराखंड भर्ती देखें →", "central-government-jobs":"🇮🇳 केंद्र सरकार भर्ती देखें →",
        "other-state-jobs":"📍 राज्य भर्ती देखें →", "ukpsc":"🏔️ UKPSC भर्ती देखें →",
        "uksssc":"🏔️ UKSSSC भर्ती देखें →", "high-court":"⚖️ हाई कोर्ट अपडेट देखें →",
        "forest":"🌲 वन विभाग भर्ती देखें →", "police":"👮 पुलिस भर्ती देखें →",
    }
    if p in mapping: return mapping[p]
    if p.endswith("-jobs"): return f"📍 {p[:-5].replace('-', ' ').title()} भर्ती देखें →"
    return "📋 विवरण देखें →"

def build_category_card(job, page_name=None):
    """Only clickable title + one category-specific button. No card/image/meta."""
    title = safe(job.get("title"), "सरकारी अपडेट")
    link = _post_link(job)
    button = _category_button(page_name or category(job))
    return f"""
<div class=\"category-post-row\">
  <a class=\"category-post-title\" href=\"{html.escape(link, quote=True)}\">{html.escape(title)}</a>
  <a class=\"category-post-button\" href=\"{html.escape(link, quote=True)}\">{button}</a>
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

    slug = slugify(title)

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

    text = " ".join([
        safe(job.get("title")),
        safe(job.get("department")),
        safe(job.get("description")),
        safe(job.get("url")),
        safe(job.get("source")),
        safe(job.get("state")),
        safe(job.get("organization")),
        safe(job.get("category")),
        safe(job.get("content")),
    ]).lower()

    matched = []

    def add(page):
        if page in CATEGORY_FILES and page not in matched:
            matched.append(page)

    # ----------------------------------------------------------
    # Location signals
    # ----------------------------------------------------------

    uk_signals = [
        "uttarakhand", "उत्तराखंड", "ukpsc", "uksssc", "ukmssb",
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
            "uksssc", "uttarakhand subordinate service selection commission",
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
            "uttarakhand forest guard", "uttarakhand forester"
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

    is_uk = any(signal in text for signal in uk_signals)

    if is_uk:
        # Always place Uttarakhand jobs in the common UK bucket.
        add("uttarakhand-jobs")

        # Also place them in their specific UK organization page.
        for page, signals in uk_specific.items():
            if any(signal in text for signal in signals):
                add(page)
                break

    else:
        # Never use generic ".gov.in" as a Central signal.
        is_central = any(signal in text for signal in central_signals)

        if is_central:
            add("central-government-jobs")
        else:
            matched_state_page = None

            for page, signals in state_specific.items():
                if any(signal in text for signal in signals):
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

        # Do not allow an explicitly state-specific category to
        # override the already detected location routing.
        if category_page == "uttarakhand-jobs":
            add("uttarakhand-jobs")
        elif category_page == "central-government-jobs":
            add("central-government-jobs")
        elif category_page == "other-state-jobs":
            add("other-state-jobs")
        else:
            add(category_page)

    # ----------------------------------------------------------
    # 3. Keyword fallback for content category
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
            if any(
                keyword.lower() in text
                for keyword in CATEGORY_RULES.get(page, [])
            ):
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

    category_css = """
<style id="category-list-final-v1">
.category-post-list{margin:20px 0 40px}.category-post-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:18px;align-items:center;padding:17px 4px;border-bottom:1px solid #e6ebf2}.category-post-title{color:#164a83!important;font-size:17px;line-height:1.55;font-weight:700;text-decoration:none!important}.category-post-title:hover{text-decoration:underline!important}.category-post-button{display:inline-flex!important;align-items:center;justify-content:center;min-width:185px;min-height:44px;padding:10px 16px;border-radius:8px;background:#1769e0;color:#fff!important;font-size:14px;font-weight:700;text-decoration:none!important;box-shadow:0 3px 8px rgba(0,0,0,.12)}.category-post-button:hover{filter:brightness(.95);transform:translateY(-1px)}@media(max-width:700px){.category-post-row{grid-template-columns:1fr;gap:10px;padding:15px 0}.category-post-title{font-size:16px}.category-post-button{width:100%;min-width:0}}
</style>
"""
    if 'id="category-list-final-v1"' not in html and '</head>' in html:
        html = html.replace('</head>', category_css + '</head>', 1)

    # ======================================================
    # Auto Migration (Manual -> Automation)
    # ======================================================

    if START_MARKER not in html or END_MARKER not in html:

        # ======================================================
        # Force Automation Layout
        # ======================================================

        block = """
<div class="category-post-list">
<!-- AUTO_CATEGORY_START -->
<!-- AUTO_CATEGORY_END -->
</div>
"""
        pos = html.find('<div id="footer">')
        if pos == -1: pos = html.lower().find('</main>')
        if pos == -1: pos = html.lower().find('</body>')
        if pos == -1:
            logger.warning("Unable to locate insertion point : %s", page.name)
            return False
        html = html[:pos] + block + html[pos:]

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
