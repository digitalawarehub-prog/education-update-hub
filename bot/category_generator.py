# ==========================================================
# Category Generator V4
# Part 1 : Imports + Configuration + Helpers
# ==========================================================

import re
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("CategoryGeneratorV4")

ROOT_DIR = Path(__file__).resolve().parent.parent

# ==========================================================
# Category Pages
# ==========================================================

CATEGORY_FILES = {

    "banking":
        ROOT_DIR / "banking.html",

    "railway":
        ROOT_DIR / "railway.html",

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

    # Uttarakhand submenu categories used by header
    "ukpsc":
        ROOT_DIR / "ukpsc.html",

    "uksssc":
        ROOT_DIR / "uksssc.html",

    "high-court":
        ROOT_DIR / "high-court.html",

    "forest":
        ROOT_DIR / "forest.html",

    "police":
        ROOT_DIR / "police.html",

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

def build_category_card(job, page_name=None):
    title = safe(job.get("title"))
    image = get_image(job)
    slug = safe(job.get("slug")) or slugify(title)
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

    link = safe(
        job.get("html_file"),
        f"generated/posts/{slug}.html"
    )

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
        "ukmssb",
        "uttarakhand government"
    ],

    "ukpsc": [
        "ukpsc",
        "uttarakhand public service commission",
        "uttarakhand pcs"
    ],

    "uksssc": [
        "uksssc",
        "uttarakhand subordinate service selection commission"
    ],

    "high-court": [
        "high court",
        "uttarakhand high court",
        "nainital high court",
        "high court of uttarakhand"
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
    Strict category routing.

    1. An explicit scraper category always wins.
    2. If category is Other State Jobs, detect one specific state when
       a clear state signal exists.
    3. Keyword fallback is used only when the scraper did not provide
       a meaningful category.
    """
    raw_category = safe(job.get("category")).lower().strip()

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

    # Direct category routing. Parent categories also receive the post,
    # while matching submenu/state pages receive a copy as well.
    if raw_category in category_map:
        page = category_map[raw_category]

        if page not in CATEGORY_FILES:
            return ["other-state-jobs"]

        text = " ".join([
            safe(job.get("title")),
            safe(job.get("department")),
            safe(job.get("description")),
            safe(job.get("state"))
        ]).lower()

        # Uttarakhand parent + matching header submenu.
        if page == "uttarakhand-jobs":
            pages = ["uttarakhand-jobs"]
            submenu_rules = [
                ("ukpsc", CATEGORY_RULES.get("ukpsc", [])),
                ("uksssc", CATEGORY_RULES.get("uksssc", [])),
                ("high-court", CATEGORY_RULES.get("high-court", [])),
                ("forest", CATEGORY_RULES.get("forest", [])),
                ("police", CATEGORY_RULES.get("police", [])),
            ]
            for submenu, keywords in submenu_rules:
                if submenu in CATEGORY_FILES and any(k.lower() in text for k in keywords):
                    pages.append(submenu)
            return list(dict.fromkeys(pages))

        # Generic Other State parent + the matching state page.
        if page == "other-state-jobs":
            pages = ["other-state-jobs"]
            state_pages = [
                ("up-government-jobs", ["uttar pradesh", "up government", "up govt", "uppsc", "upsssc", "up police"]),
                ("bihar-jobs", ["bihar", "bpsc", "bihar police"]),
                ("rajasthan-jobs", ["rajasthan", "rpsc", "rajasthan police"]),
                ("mp-jobs", ["madhya pradesh", "mp government", "mp govt", "mppsc", "mp police"]),
                ("andhra-pradesh-jobs", ["andhra pradesh", "andhra", "ap government", "ap govt", "apsc"]),
                ("arunachal-pradesh-jobs", ["arunachal pradesh", "arunachal"]),
                ("assam-jobs", ["assam government", "assam govt", "assam", "apsc"]),
                ("chhattisgarh-jobs", ["chhattisgarh", "cgpsc", "cg govt"]),
                ("goa-jobs", ["goa government", "goa govt", "goa"]),
                ("gujarat-jobs", ["gujarat", "gpsc"]),
                ("haryana-jobs", ["haryana", "hpsc"]),
                ("himachal-pradesh-jobs", ["himachal pradesh", "hppsc"]),
                ("jharkhand-jobs", ["jharkhand", "jpsc"]),
                ("karnataka-jobs", ["karnataka", "kpsc"]),
                ("kerala-jobs", ["kerala", "kerala psc"]),
                ("maharashtra-jobs", ["maharashtra", "mpsc"]),
                ("manipur-jobs", ["manipur"]),
                ("meghalaya-jobs", ["meghalaya"]),
                ("mizoram-jobs", ["mizoram"]),
                ("nagaland-jobs", ["nagaland", "npsc"]),
                ("odisha-jobs", ["odisha", "opsc", "odisha police"]),
                ("punjab-jobs", ["punjab", "ppsc"]),
                ("sikkim-jobs", ["sikkim", "spsc"]),
                ("tamil-nadu-jobs", ["tamil nadu", "tamilnadu", "tnpsc"]),
                ("telangana-jobs", ["telangana", "tspsc"]),
                ("tripura-jobs", ["tripura", "tpsc"]),
                ("west-bengal-jobs", ["west bengal", "wbpsc"]),
            ]
            for state_page, keywords in state_pages:
                if state_page in CATEGORY_FILES and any(k in text for k in keywords):
                    pages.append(state_page)
                    break
            return list(dict.fromkeys(pages))

        return [page]

    # No useful explicit category: detect submenu/state signals first,
    # then fall back to the existing priority routing.
    text = " ".join([
        safe(job.get("title")),
        safe(job.get("department")),
        safe(job.get("description")),
        safe(job.get("state"))
    ]).lower()

    uk_submenus = [
        ("ukpsc", CATEGORY_RULES.get("ukpsc", [])),
        ("uksssc", CATEGORY_RULES.get("uksssc", [])),
        ("high-court", CATEGORY_RULES.get("high-court", [])),
        ("forest", CATEGORY_RULES.get("forest", [])),
        ("police", CATEGORY_RULES.get("police", [])),
    ]
    for submenu, keywords in uk_submenus:
        if submenu in CATEGORY_FILES and any(k.lower() in text for k in keywords):
            return ["uttarakhand-jobs", submenu]

    state_pages = [
        ("up-government-jobs", ["uttar pradesh", "up government", "up govt", "uppsc", "upsssc", "up police"]),
        ("bihar-jobs", ["bihar", "bpsc", "bihar police"]),
        ("rajasthan-jobs", ["rajasthan", "rpsc", "rajasthan police"]),
        ("mp-jobs", ["madhya pradesh", "mp government", "mp govt", "mppsc", "mp police"]),
        ("andhra-pradesh-jobs", ["andhra pradesh", "andhra", "ap government", "ap govt", "apsc"]),
        ("arunachal-pradesh-jobs", ["arunachal pradesh", "arunachal"]),
        ("assam-jobs", ["assam government", "assam govt", "assam", "apsc"]),
        ("chhattisgarh-jobs", ["chhattisgarh", "cgpsc", "cg govt"]),
        ("goa-jobs", ["goa government", "goa govt", "goa"]),
        ("gujarat-jobs", ["gujarat", "gpsc"]),
        ("haryana-jobs", ["haryana", "hpsc"]),
        ("himachal-pradesh-jobs", ["himachal pradesh", "hppsc"]),
        ("jharkhand-jobs", ["jharkhand", "jpsc"]),
        ("karnataka-jobs", ["karnataka", "kpsc"]),
        ("kerala-jobs", ["kerala", "kerala psc"]),
        ("maharashtra-jobs", ["maharashtra", "mpsc"]),
        ("manipur-jobs", ["manipur"]),
        ("meghalaya-jobs", ["meghalaya"]),
        ("mizoram-jobs", ["mizoram"]),
        ("nagaland-jobs", ["nagaland", "npsc"]),
        ("odisha-jobs", ["odisha", "opsc", "odisha police"]),
        ("punjab-jobs", ["punjab", "ppsc"]),
        ("sikkim-jobs", ["sikkim", "spsc"]),
        ("tamil-nadu-jobs", ["tamil nadu", "tamilnadu", "tnpsc"]),
        ("telangana-jobs", ["telangana", "tspsc"]),
        ("tripura-jobs", ["tripura", "tpsc"]),
        ("west-bengal-jobs", ["west bengal", "wbpsc"]),
    ]
    for state_page, keywords in state_pages:
        if state_page in CATEGORY_FILES and any(k in text for k in keywords):
            return ["other-state-jobs", state_page]

    priority = [
        "admit-card", "answer-key", "result", "scholarship", "syllabus",
        "ctet", "utet", "deled", "teaching-exams", "entrance-exams",
        "uttarakhand-jobs", "banking", "railway", "upsc", "ssc",
        "forest", "police", "central-government-jobs", "latest-jobs"
    ]

    for page in priority:
        for keyword in CATEGORY_RULES.get(page, []):
            if keyword.lower() in text:
                return [page]

    return ["other-state-jobs"]

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

    # Remove expired applications and scraper navigation noise first.
    jobs = filter_category_jobs(jobs)

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
