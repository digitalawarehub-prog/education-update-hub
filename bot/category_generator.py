# ==========================================================
# Education Update Hub - Category Generator FINAL
# ==========================================================

import re
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("CategoryGeneratorFinal")

ROOT_DIR = Path(__file__).resolve().parent.parent

CATEGORY_FILES = {'latest-jobs': 'latest-jobs.html', 'banking-jobs': 'banking-jobs.html', 'railway-jobs': 'railway-jobs.html', 'upsc': 'upsc.html', 'ssc': 'ssc.html', 'teacher-recruitment': 'teacher-recruitment.html', 'ctet': 'ctet.html', 'utet': 'utet.html', 'deled': 'deled.html', 'admit-card': 'admit-card.html', 'result': 'result.html', 'answer-key': 'answer-key.html', 'scholarship': 'scholarship.html', 'syllabus': 'syllabus.html', 'teaching-exams': 'teaching-exams.html', 'entrance-exams': 'entrance-exams.html', 'government-schemes': 'government-schemes.html', 'uttarakhand-jobs': 'uttarakhand-jobs.html', 'central-government-jobs': 'central-government-jobs.html', 'other-state-jobs': 'other-state-jobs.html', 'andhra-pradesh-jobs': 'andhra-pradesh-jobs.html', 'arunachal-pradesh-jobs': 'arunachal-pradesh-jobs.html', 'assam-jobs': 'assam-jobs.html', 'chhattisgarh-jobs': 'chhattisgarh-jobs.html', 'goa-jobs': 'goa-jobs.html', 'gujarat-jobs': 'gujarat-jobs.html', 'haryana-jobs': 'haryana-jobs.html', 'himachal-pradesh-jobs': 'himachal-pradesh-jobs.html', 'jharkhand-jobs': 'jharkhand-jobs.html', 'karnataka-jobs': 'karnataka-jobs.html', 'kerala-jobs': 'kerala-jobs.html', 'maharashtra-jobs': 'maharashtra-jobs.html', 'manipur-jobs': 'manipur-jobs.html', 'meghalaya-jobs': 'meghalaya-jobs.html', 'mizoram-jobs': 'mizoram-jobs.html', 'nagaland-jobs': 'nagaland-jobs.html', 'odisha-jobs': 'odisha-jobs.html', 'punjab-jobs': 'punjab-jobs.html', 'sikkim-jobs': 'sikkim-jobs.html', 'tamil-nadu-jobs': 'tamil-nadu-jobs.html', 'telangana-jobs': 'telangana-jobs.html', 'tripura-jobs': 'tripura-jobs.html', 'west-bengal-jobs': 'west-bengal-jobs.html', 'up-government-jobs': 'up-government-jobs.html', 'bihar-jobs': 'bihar-jobs.html', 'rajasthan-jobs': 'rajasthan-jobs.html', 'mp-jobs': 'mp-jobs.html', 'forest': 'forest.html', 'police': 'police.html'}

START_MARKER = "<!-- AUTO_CATEGORY_START -->"
END_MARKER = "<!-- AUTO_CATEGORY_END -->"

CATEGORY_RULES = {'banking': ['bank', 'ibps', 'sbi', 'rbi', 'pnb', 'canara', 'boi', 'union bank', 'bank of baroda'], 'railway': ['railway', 'rrb', 'rrc', 'metro rail'], 'upsc': ['upsc', 'nda', 'cds', 'civil services', 'ies', 'ifs'], 'ssc': ['ssc', 'cgl', 'chsl', 'mts', 'gd', 'stenographer', 'selection post'], 'teacher-recruitment': ['teacher', 'lecturer', 'assistant professor', 'principal', 'tgt', 'pgt', 'education department'], 'ctet': ['ctet'], 'utet': ['utet', 'uktet'], 'deled': ['d.el.ed', 'deled', 'btc'], 'admit-card': ['admit card', 'hall ticket', 'call letter'], 'result': ['result', 'merit list', 'score card', 'scorecard'], 'answer-key': ['answer key', 'provisional answer key', 'final answer key'], 'scholarship': ['scholarship', 'nsp', 'fellowship', 'financial assistance'], 'uttarakhand-jobs': ['ukpsc', 'uttarakhand', 'ubse', 'uksssc', 'ukmssb'], 'central-government-jobs': ['central government', 'ministry', 'government of india', 'psu'], 'latest-jobs': ['recruitment', 'vacancy', 'notification', 'apply online', 'job'], 'syllabus': ['syllabus', 'exam pattern'], 'government-schemes': ['scheme', 'yojana', 'government scheme'], 'teaching-exams': ['ctet', 'utet', 'tet', 'teacher eligibility'], 'entrance-exams': ['neet', 'jee', 'cuet', 'gate', 'cat'], 'andhra-pradesh-jobs': ['andhra pradesh', 'andhra', 'ap govt', 'ap government'], 'arunachal-pradesh-jobs': ['arunachal pradesh', 'arunachal'], 'assam-jobs': ['assam government', 'assam govt', 'assam', 'apsc'], 'chhattisgarh-jobs': ['chhattisgarh', 'chhattisgarh government', 'cg govt', 'cgpsc'], 'goa-jobs': ['goa government', 'goa govt', 'goa'], 'gujarat-jobs': ['gujarat government', 'gujarat govt', 'gujarat', 'gpsc'], 'haryana-jobs': ['haryana government', 'haryana govt', 'haryana', 'hpsc'], 'himachal-pradesh-jobs': ['himachal pradesh', 'himachal govt', 'himachal government', 'hppsc'], 'jharkhand-jobs': ['jharkhand', 'jharkhand government', 'jharkhand govt', 'jpsc'], 'karnataka-jobs': ['karnataka', 'karnataka government', 'karnataka govt', 'kpsc'], 'kerala-jobs': ['kerala', 'kerala government', 'kerala govt', 'kerala psc', 'kpsc kerala'], 'maharashtra-jobs': ['maharashtra', 'maharashtra government', 'maharashtra govt', 'mpsc'], 'manipur-jobs': ['manipur', 'manipur government', 'manipur govt', 'mpsc manipur'], 'meghalaya-jobs': ['meghalaya', 'meghalaya government', 'meghalaya govt', 'mpsc meghalaya'], 'mizoram-jobs': ['mizoram', 'mizoram government', 'mizoram govt', 'mpsc mizoram'], 'nagaland-jobs': ['nagaland', 'nagaland government', 'nagaland govt', 'npsc'], 'odisha-jobs': ['odisha', 'odisha government', 'odisha govt', 'opsc', 'odisha police'], 'punjab-jobs': ['punjab', 'punjab government', 'punjab govt', 'ppsc'], 'sikkim-jobs': ['sikkim', 'sikkim government', 'sikkim govt', 'spsc'], 'tamil-nadu-jobs': ['tamil nadu', 'tamilnadu', 'tamil nadu government', 'tn govt', 'tnpsc'], 'telangana-jobs': ['telangana', 'telangana government', 'telangana govt', 'tspsc'], 'tripura-jobs': ['tripura', 'tripura government', 'tripura govt', 'tpsc'], 'west-bengal-jobs': ['west bengal', 'west bengal government', 'west bengal govt', 'wbpsc'], 'up-government-jobs': ['uttar pradesh', 'up government', 'up govt', 'upsssc', 'uppsc', 'up police'], 'bihar-jobs': ['bihar government', 'bihar govt', 'bihar', 'bpsc', 'bihar police'], 'rajasthan-jobs': ['rajasthan government', 'rajasthan govt', 'rajasthan', 'rpsc', 'rajasthan police'], 'mp-jobs': ['madhya pradesh', 'madhya pradesh government', 'mp government', 'mp govt', 'mppsc', 'mp police'], 'forest': ['forest department', 'forest guard', 'forester', 'forest ranger'], 'police': ['police recruitment', 'police constable', 'sub inspector', 'head constable', 'police vacancy']}

CATEGORY_MAP = {'latest jobs': 'latest-jobs', 'latest updates': 'latest-jobs', 'recruitment': 'latest-jobs', 'result': 'result', 'results': 'result', 'admit card': 'admit-card', 'answer key': 'answer-key', 'scholarship': 'scholarship', 'syllabus': 'syllabus', 'teaching exams': 'teaching-exams', 'entrance exams': 'entrance-exams', 'government schemes': 'government-schemes', 'banking jobs': 'banking-jobs', 'bank jobs': 'banking-jobs', 'railway jobs': 'railway-jobs', 'uttarakhand jobs': 'uttarakhand-jobs', 'central jobs': 'central-government-jobs', 'central government jobs': 'central-government-jobs', 'other state jobs': 'other-state-jobs', 'upsc': 'upsc', 'ssc': 'ssc', 'ctet': 'ctet', 'utet': 'utet', 'deled': 'deled', 'forest': 'forest', 'forest jobs': 'forest', 'police': 'police', 'police jobs': 'police', 'teacher recruitment': 'teacher-recruitment', 'andhra pradesh jobs': 'andhra-pradesh-jobs', 'arunachal pradesh jobs': 'arunachal-pradesh-jobs', 'assam jobs': 'assam-jobs', 'chhattisgarh jobs': 'chhattisgarh-jobs', 'goa jobs': 'goa-jobs', 'gujarat jobs': 'gujarat-jobs', 'haryana jobs': 'haryana-jobs', 'himachal pradesh jobs': 'himachal-pradesh-jobs', 'jharkhand jobs': 'jharkhand-jobs', 'karnataka jobs': 'karnataka-jobs', 'kerala jobs': 'kerala-jobs', 'maharashtra jobs': 'maharashtra-jobs', 'manipur jobs': 'manipur-jobs', 'meghalaya jobs': 'meghalaya-jobs', 'mizoram jobs': 'mizoram-jobs', 'nagaland jobs': 'nagaland-jobs', 'odisha jobs': 'odisha-jobs', 'punjab jobs': 'punjab-jobs', 'sikkim jobs': 'sikkim-jobs', 'tamil nadu jobs': 'tamil-nadu-jobs', 'telangana jobs': 'telangana-jobs', 'tripura jobs': 'tripura-jobs', 'west bengal jobs': 'west-bengal-jobs', 'up government jobs': 'up-government-jobs', 'bihar jobs': 'bihar-jobs', 'rajasthan jobs': 'rajasthan-jobs', 'mp jobs': 'mp-jobs'}

MAX_POSTS_PER_CATEGORY = 50


def safe(value, default=""):
    if value is None:
        return default
    return str(value).strip()


def slugify(title):
    raw = safe(title).lower()
    slug = re.sub(r"[^a-z0-9]+", "-", raw)
    slug = re.sub(r"-+", "-", slug).strip("-")
    if slug:
        return slug
    return "post-" + str(abs(hash(raw))) if raw else "post"


def job_slug(job):
    return safe(job.get("slug")) or slugify(job.get("title", ""))


def job_url(job):
    value = safe(job.get("html_file"))
    if value:
        return "/" + value.lstrip("/")
    return f"/generated/posts/{job_slug(job)}.html"


def get_image(job):
    return (
        safe(job.get("featured_image"))
        or safe(job.get("thumbnail"))
        or safe(job.get("image"))
        or "images/default-job.png"
    )


def build_category_card(job):
    title = safe(job.get("title"), "Latest Update")
    url = job_url(job)
    image = get_image(job)
    description = safe(
        job.get("description"),
        "Click to read complete details."
    )
    last_date = safe(
        job.get("last_date"),
        "Check Notification"
    )
    category_name = safe(job.get("category"), "Latest Jobs")

    return f"""
<div class="card">
    <a href="{url}">
        <img src="{image}" alt="{title}" loading="lazy">
    </a>
    <div class="post-content">
        <span class="category-tag">{category_name}</span>
        <h3><a href="{url}">{title}</a></h3>
        <p>{description}</p>
        <div class="post-meta">📅 {last_date}</div>
        <a class="read-more-btn" href="{url}">Read More →</a>
    </div>
</div>
"""


def detect_categories(job):
    matched = set()

    raw_category = safe(job.get("category")).lower()
    normalized = raw_category.replace("_", " ").replace("-", " ")
    if normalized in CATEGORY_MAP:
        matched.add(CATEGORY_MAP[normalized])

    text = " ".join(
        safe(job.get(key))
        for key in (
            "title", "department", "description",
            "content", "state", "source", "category"
        )
    ).lower()

    # Strong state/category routing first.
    if (
        "uttarakhand" in text
        or "उत्तराखंड" in text
        or raw_category == "uttarakhand jobs"
        or "ukpsc" in text
        or "uksssc" in text
    ):
        matched.add("uttarakhand-jobs")

    state_names = {
        "andhra-pradesh": ("andhra pradesh", "ap government", "appsc"),
        "arunachal-pradesh": ("arunachal pradesh",),
        "assam": ("assam", "apsc"),
        "chhattisgarh": ("chhattisgarh", "cgpsc"),
        "goa": ("goa",),
        "gujarat": ("gujarat", "gpsc"),
        "haryana": ("haryana", "hpsc"),
        "himachal-pradesh": ("himachal pradesh", "hppsc"),
        "jharkhand": ("jharkhand", "jpsc"),
        "karnataka": ("karnataka", "kpsc"),
        "kerala": ("kerala",),
        "maharashtra": ("maharashtra", "mpsc"),
        "manipur": ("manipur",),
        "meghalaya": ("meghalaya",),
        "mizoram": ("mizoram",),
        "nagaland": ("nagaland", "npsc"),
        "odisha": ("odisha", "opsc"),
        "punjab": ("punjab", "ppsc"),
        "sikkim": ("sikkim", "spsc"),
        "tamil-nadu": ("tamil nadu", "tnpsc"),
        "telangana": ("telangana", "tspsc"),
        "tripura": ("tripura", "tpsc"),
        "west-bengal": ("west bengal", "wbpsc"),
        "up-government": ("uttar pradesh", "up government", "uppsc", "upsssc"),
        "bihar": ("bihar", "bpsc"),
        "rajasthan": ("rajasthan", "rpsc"),
        "mp": ("madhya pradesh", "mppsc"),
    }

    for prefix, words in state_names.items():
        if any(word in text for word in words):
            page = f"{prefix}-jobs"
            if page in CATEGORY_FILES:
                matched.add(page)

    # Generic category rules.
    for page, keywords in CATEGORY_RULES.items():
        if page not in CATEGORY_FILES:
            continue
        for keyword in keywords:
            if str(keyword).lower() in text:
                matched.add(page)
                break

    # Central jobs are a fallback for explicit central/government exams.
    if (
        "central government jobs" in text
        or "central jobs" in text
        or "upsc" in text
        or re.search(r"\bssc\b", text)
        or "rrb" in text
        or "ibps" in text
    ):
        matched.add("central-government-jobs")

    # Every valid job remains visible on Latest Jobs.
    if "latest-jobs" in CATEGORY_FILES:
        matched.add("latest-jobs")

    # If it is clearly state-specific but not Uttarakhand, also include Other State Jobs.
    if (
        "uttarakhand-jobs" not in matched
        and any(page.endswith("-jobs") and page not in {
            "latest-jobs", "central-government-jobs", "other-state-jobs"
        } for page in matched)
    ):
        matched.add("other-state-jobs")

    if not matched:
        matched.add("other-state-jobs")

    return sorted(matched)


def group_jobs(jobs):
    grouped = {page: [] for page in CATEGORY_FILES}
    for job in jobs or []:
        if not isinstance(job, dict):
            continue
        for page in detect_categories(job):
            if page in grouped:
                grouped[page].append(job)
    return grouped


def replace_category_section(content, items):
    start = content.find(START_MARKER)
    end = content.find(END_MARKER)

    if start == -1 or end == -1 or end < start:
        return content

    end += len(END_MARKER)

    auto_section = (
        START_MARKER
        + "\n\n"
        + "\n".join(items)
        + "\n\n"
        + END_MARKER
    )

    # IMPORTANT: insert exactly once.
    return content[:start] + auto_section + content[end:]


def update_category_page(page_name, jobs):
    page = CATEGORY_FILES.get(page_name)
    if not page:
        return False

    if not page.exists():
        logger.warning("Category Page Missing : %s", page.name)
        return False

    html = page.read_text(encoding="utf-8")

    if START_MARKER not in html or END_MARKER not in html:
        start = html.find('<div class="post-grid">')
        if start == -1:
            start = html.find('<div class="post-list">')
        end = html.find('<div id="footer">', start)

        if start != -1 and end != -1:
            html = (
                html[:start]
                + '<div class="post-grid">\n\n'
                + START_MARKER
                + '\n\n'
                + END_MARKER
                + '\n\n</div>\n\n'
                + html[end:]
            )
        else:
            logger.warning("Unable to locate post section : %s", page.name)
            return False

    jobs = sorted(
        jobs or [],
        key=lambda j: safe(
            j.get("publish_date") or j.get("date"),
            "0000-00-00"
        ),
        reverse=True
    )[:MAX_POSTS_PER_CATEGORY]

    seen = set()
    cards = []
    for job in jobs:
        slug = job_slug(job)
        if slug in seen:
            continue
        seen.add(slug)
        cards.append(build_category_card(job))

    if not cards:
        cards = ['<div class="empty-category"><h3>No Posts Available</h3><p>New updates will appear here automatically.</p></div>']

    page.write_text(
        replace_category_section(html, cards),
        encoding="utf-8"
    )

    logger.info("%s Updated (%d Posts)", page.name, len(cards))
    return True


def update_all_categories(grouped_jobs):
    updated = 0
    skipped = 0

    for page_name, jobs in grouped_jobs.items():
        if update_category_page(page_name, jobs):
            updated += 1
        else:
            skipped += 1

    logger.info("Category Pages | Updated=%d Skipped=%d", updated, skipped)
    return updated


def remove_duplicate_jobs(jobs):
    unique = []
    seen = set()
    for job in jobs or []:
        if not isinstance(job, dict):
            continue
        slug = job_slug(job)
        if slug in seen:
            continue
        seen.add(slug)
        unique.append(job)
    return unique


def sort_jobs(jobs):
    return sorted(
        jobs or [],
        key=lambda j: safe(
            j.get("publish_date") or j.get("date"),
            "0000-00-00"
        ),
        reverse=True
    )


def build_categories(jobs):
    jobs = remove_duplicate_jobs(jobs)
    jobs = sort_jobs(jobs)
    grouped = group_jobs(jobs)

    total = sum(len(v) for v in grouped.values())
    logger.info("Total Categorized Posts : %d", total)

    updated = update_all_categories(grouped)

    for page, items in sorted(grouped.items()):
        if items:
            logger.info("CATEGORY | %-28s : %d", page, len(items))

    return updated


def build(jobs):
    return build_categories(jobs)


def run(jobs):
    try:
        return build_categories(jobs)
    except Exception as exc:
        logger.exception("Category Generator Error : %s", exc)
        return 0


logger.info("Category Generator FINAL Loaded Successfully")
