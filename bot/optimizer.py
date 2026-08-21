"""
=========================================================
Education Update Hub
Production Optimizer v4
=========================================================
"""

import hashlib
import logging
import re
from datetime import datetime, timedelta
from filters import classify_post
logger = logging.getLogger("Optimizer")

if not logger.handlers:
    handler = logging.StreamHandler()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

logger.setLevel(logging.INFO)

# ==========================================================
# Category Mapping
# ==========================================================

CATEGORY_MAP = {
    "recruitment": "Recruitment",
    "admit card": "Admit Card",
    "result": "Result",
    "answer key": "Answer Key",
    "syllabus": "Syllabus",
    "scholarship": "Scholarship",
    "exam": "Exam",
}

DEPARTMENT_RULES = {
    "Banking": ["bank", "ibps", "rbi", "nabard", "lic", "sbi", "sidbi", "banking"],
    "Railway": ["railway", "rrb", "rrc", "rail"],
    "Defence": ["army", "navy", "air force", "drdo", "bsf", "crpf", "cisf", "itbp", "defence"],
    "Teaching": ["teacher", "faculty", "lecturer", "professor", "school teacher", "education department"],
    "Medical": ["medical", "doctor", "nurse", "pharmacist", "aiims", "hospital", "health"],
    "Police": ["police", "constable", "inspector", "cop"],
    "Agriculture": ["agriculture", "agricultural", "krishi", "horticulture", "forestry", "icar", "kvk"],
}

SOURCE_DEPARTMENTS = {
    "ssc": "SSC", "upsc": "UPSC", "ibps": "IBPS", "ukpsc": "UKPSC",
    "uksssc": "UKSSSC", "railway": "Railway", "psc": "PSC",
}

logger.info("Optimizer Loaded Successfully")
# ==========================================================
# Text Normalization
# ==========================================================

def normalize_text(text):

    if text is None:
        return ""

    text = str(text).strip().lower()

    text = re.sub(r"\s+", " ", text)

    text = re.sub(r"[^a-z0-9 ]", "", text)

    return text


# ==========================================================
# Generate Unique Job ID
# ==========================================================

def generate_job_id(job):

    # URL + title identify the same source item. Last-date changes must update
    # the existing post instead of creating a duplicate post.
    key = "|".join([
        normalize_text(job.get("title", "")),
        normalize_text(job.get("url", "")),
    ])

    return hashlib.md5(
        key.encode("utf-8")
    ).hexdigest()


# ==========================================================
# Extract Recruitment Year
# ==========================================================

def extract_year(title):

    if not title:
        return ""

    match = re.search(
        r"(20\d{2})",
        str(title)
    )

    if match:
        return match.group(1)

    return ""


# ==========================================================
# Detect Category
# ==========================================================

def detect_category(title, url="", description=""):
    category = classify_post(title, url, description)
    return category or ""


# ==========================================================
# Detect Department
# ==========================================================

def detect_department(job):
    """Derive department from the current record, not stale database values."""
    source = str(job.get("source", "") or "").strip().lower()
    source_map = dict(SOURCE_DEPARTMENTS)
    # PSC adapter names are also valid department/source identifiers.
    for name in ("rpsc", "uppsc", "bpsc", "mppsc", "cgpsc", "jpsc"):
        source_map[name] = name.upper()
    if source in source_map:
        return source_map[source]

    text = " ".join(str(job.get(k, "") or "") for k in ("title", "description", "content", "url")).lower()

    organization_rules = {
        "AIIMS": ["aiims", "all india institute of medical sciences"],
        "ICAR": ["icar"], "IIT": ["iit"], "IIM": ["iim"], "NIT": ["nit"],
        "UPSC": ["upsc"], "SSC": ["ssc"], "IBPS": ["ibps"],
        "UKPSC": ["ukpsc"], "UKSSSC": ["uksssc"],
    }
    for org, needles in organization_rules.items():
        if any(re.search(rf"(?<![a-z]){re.escape(n)}(?![a-z])", text) for n in needles):
            return org

    for department, keywords in DEPARTMENT_RULES.items():
        for word in keywords:
            if re.search(rf"(?<![a-z]){re.escape(word)}(?![a-z])", text):
                return department

    # Only use an existing non-generic value as a last resort.
    existing = str(job.get("department", "") or "").strip()
    if existing and existing.casefold() not in {"government", "latest jobs", "latest updates", "none", "null", "not mentioned"}:
        return existing
    return "Government"


# ==========================================================
# Timestamp
# ==========================================================

def add_timestamp(jobs):

    timestamp = datetime.now().isoformat()

    for job in jobs:

        job["scraped_at"] = timestamp

    return jobs


logger.info("Core Optimizer Functions Loaded")
# ==========================================================
# Generate Smart Tags
# ==========================================================

def generate_tags(job):

    tags = set()

    fields = [

        job.get("title", ""),

        job.get("category", ""),

        job.get("department", ""),

        job.get("source", ""),

        job.get("state", ""),

        extract_year(job.get("title", ""))

    ]

    for field in fields:

        field = str(field)

        for word in field.split():

            word = normalize_text(word)

            if len(word) >= 3:

                tags.add(word)

    return sorted(tags)


# ==========================================================
# Generate SEO Keywords
# ==========================================================

def generate_keywords(job):

    title = str(job.get("title", "")).strip()

    if not title:

        return []

    keywords = [

        title,

        f"{title} Recruitment",

        f"{title} Notification",

        f"{title} Apply Online",

        f"{title} Vacancy",

        f"{title} Jobs",

        f"{title} Last Date",

        f"{title} Official Notification"

    ]

    return list(dict.fromkeys(keywords))


# ==========================================================
# Optimize Single Job
# ==========================================================

def optimize_job(job):
    job = dict(job)
    title = str(job.get("title", "")).strip()
    url = str(job.get("url", "")).strip()
    category = classify_post(title, url, job.get("description", ""), job.get("source", ""))
    if not category:
        job["is_valid_post"] = False
        return job
    job["is_valid_post"] = True
    job["post_type"] = category
    job["job_id"] = generate_job_id(job)
    job["category"] = category
    job["department"] = detect_department(job)
    job["year"] = extract_year(title)
    source_date = (job.get("notification_date") or job.get("source_date") or job.get("published_date") or job.get("date_published") or job.get("posted_date"))
    if source_date:
        job["publish_date"] = source_date
    elif not job.get("publish_date"):
        # Do not stamp the GitHub workflow date onto an old/undated notification.
        # The HTML layer will show "उपलब्ध नहीं" until a source date is found.
        job["publish_date"] = ""
    job["last_seen_at"] = datetime.now().isoformat()
    job["tags"] = generate_tags(job)
    job["keywords"] = generate_keywords(job)
    return job


# ==========================================================
# Remove Duplicate Jobs
# ==========================================================

def remove_duplicates(jobs):

    unique = {}

    for job in jobs:

        job = optimize_job(job)

        if not job.get("is_valid_post"):
            continue
        jid = job["job_id"]

        old = unique.get(jid)

        if old is None:

            unique[jid] = job

            continue

        if job.get("priority", 0) > old.get("priority", 0):

            unique[jid] = job

    logger.info(

        "Duplicate Removed : %d -> %d",

        len(jobs),

        len(unique)

    )

    return list(unique.values())


# ==========================================================
# Optimize All Jobs
# ==========================================================

def optimize_jobs(jobs):

    jobs = remove_duplicates(jobs)
    jobs = validate_jobs(jobs)
    jobs = add_timestamp(jobs)

    jobs.sort(
        key=lambda x: (
            x.get("priority", 0),
            x.get("title", "")
        ),
        reverse=True
    )

    logger.info(
        "Optimized Jobs : %d",
        len(jobs)
    )

    return jobs


logger.info("Production Optimizer Ready")
# ==========================================================
# Merge Existing & New Jobs
# ==========================================================

def _job_changed(old, new):
    fields = ("title", "url", "category", "department", "vacancy", "qualification", "salary", "age_limit", "application_fee", "selection_process", "exam_date", "application_start_date", "last_date", "description", "apply_link", "notification_pdf", "official_website", "notification_date", "notification_text")
    return any(str(old.get(k, "")) != str(new.get(k, "")) for k in fields)

def _is_placeholder(value):
    s = str(value or "").strip().casefold()
    return s in {
        "", "not mentioned", "check official notification", "check notification",
        "as per rules", "not available", "उपलब्ध नहीं", "आधिकारिक अधिसूचना देखें",
        "official notification", "n/a", "na", "none", "null", ".",
    }

def _merge_field(old, new, key):
    """Prefer real newly extracted data, but never erase a real old value with
    an empty/default scraper placeholder."""
    nv = new.get(key)
    ov = old.get(key)
    if not _is_placeholder(nv):
        return nv
    if not _is_placeholder(ov):
        return ov
    return nv if nv is not None else ov

def merge_jobs(old_jobs, new_jobs):
    merged = {j.get("job_id"): dict(j) for j in old_jobs if j.get("job_id")}
    added = updated = 0
    detail_fields = (
        "vacancy", "qualification", "salary", "age_limit", "application_fee",
        "selection_process", "exam_date", "application_start_date", "last_date",
        "description", "content", "apply_link", "notification_pdf",
        "official_website", "official_notification_pdf", "notification_date", "notification_text",
    )

    for job in new_jobs:
        if not job.get("is_valid_post") or not job.get("job_id"):
            continue
        jid = job["job_id"]
        if jid in merged:
            old = merged[jid]
            combined = dict(old)

            # Always refresh canonical identity/category metadata.
            for key in ("title", "url", "category", "post_type", "department", "year", "tags", "keywords", "is_valid_post"):
                if job.get(key) is not None:
                    combined[key] = job.get(key)

            for key in detail_fields:
                combined[key] = _merge_field(old, job, key)

            # Source/notification date wins over workflow date.
            source_date = (
                job.get("notification_date") or job.get("source_date") or
                job.get("published_date") or job.get("date_published") or
                job.get("posted_date") or job.get("date")
            )
            if source_date:
                combined["publish_date"] = source_date
            elif old.get("publish_date"):
                combined["publish_date"] = old.get("publish_date")
            elif job.get("publish_date"):
                combined["publish_date"] = job.get("publish_date")

            # Never keep javascript pseudo-links as action URLs.
            if str(combined.get("apply_link", "")).lower().startswith("javascript:"):
                combined["apply_link"] = ""
            if str(combined.get("notification_pdf", "")).lower().startswith("javascript:"):
                combined["notification_pdf"] = ""

            if _job_changed(old, combined):
                merged[jid] = combined
                updated += 1
        else:
            merged[jid] = dict(job)
            added += 1
            logger.info("ADDED : %s", job.get("title"))

    logger.info("Merge Completed | Added=%d Updated=%d Total=%d", added, updated, len(merged))
    return list(merged.values())


# ==========================================================
# Filter Only New Jobs
# ==========================================================

def filter_new_jobs(old_jobs, new_jobs):
    existing = {job.get("job_id"): job for job in old_jobs if job.get("job_id")}
    fresh = []
    for job in new_jobs:
        if not job.get("is_valid_post"):
            continue
        old = existing.get(job.get("job_id"))
        if old is None or _job_changed(old, job):
            fresh.append(job)
    logger.info("New/Changed Jobs Found : %d", len(fresh))
    return fresh

MONTHS = {
    "jan":1,"january":1,
    "feb":2,"february":2,
    "mar":3,"march":3,
    "apr":4,"april":4,
    "may":5,
    "jun":6,"june":6,
    "jul":7,"july":7,
    "aug":8,"august":8,
    "sep":9,"sept":9,"september":9,
    "oct":10,"october":10,
    "nov":11,"november":11,
    "dec":12,"december":12
}

def is_expired(job):

    last_date = str(job.get("last_date", "")).strip()

    if not last_date:
        return False

    today = datetime.today().date()

    formats = [
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d.%m.%Y",
        "%Y-%m-%d",
        "%d %B %Y",
        "%d %b %Y"
    ]

    for fmt in formats:
        try:
            expiry = datetime.strptime(last_date, fmt).date()
            return expiry < today
        except:
            pass

    m = re.search(
        r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})",
        last_date
    )

    if m:

        day = int(m.group(1))

        month = MONTHS.get(
            m.group(2).lower()
        )

        year = int(m.group(3))

        if month:

            expiry = datetime(
                year,
                month,
                day
            ).date()

            return expiry < today

    return False
# ==========================================================
# Validate Jobs
# ==========================================================

def validate_jobs(jobs):

    valid = []

    rejected = 0

    required = [

        "title",

        "url",

        "job_id"

    ]

    for job in jobs:

        ok = True

        for field in required:

            if not job.get(field):

                ok = False
                break

        if ok and job.get("is_valid_post"):

            if is_expired(job):

                rejected += 1

                logger.info(
                    "Expired Job Removed : %s",
                    job.get("title")
                )

                continue

            valid.append(job)

        else:

            rejected += 1

    logger.info(

        "Validation | Valid=%d Rejected=%d",

        len(valid),

        rejected

    )

    return valid


# ==========================================================
# Build Summary
# ==========================================================

def build_summary(jobs):

    summary = {

        "total": len(jobs),

        "categories": {},

        "departments": {}

    }

    for job in jobs:

        category = job.get(
            "category",
            "Latest Jobs"
        )

        department = job.get(
            "department",
            "Government"
        )

        summary["categories"][category] = (

            summary["categories"].get(category, 0) + 1

        )

        summary["departments"][department] = (

            summary["departments"].get(department, 0) + 1

        )

    logger.info(

        "Summary Generated"

    )

    return summary


logger.info("Database Utilities Loaded Successfully")
# ==========================================================
# Print Optimizer Summary
# ==========================================================

def print_summary(summary):

    logger.info("=" * 60)
    logger.info("OPTIMIZER SUMMARY")
    logger.info("=" * 60)

    logger.info(
        "Total Jobs : %d",
        summary.get("total", 0)
    )

    logger.info("")

    logger.info("Categories")

    for category, total in sorted(

        summary.get("categories", {}).items()

    ):

        logger.info(

            "  %-20s %d",

            category,

            total

        )

    logger.info("")

    logger.info("Departments")

    for department, total in sorted(

        summary.get("departments", {}).items()

    ):

        logger.info(

            "  %-20s %d",

            department,

            total

        )

    logger.info("=" * 60)


# ==========================================================
# Optimizer Health Check
# ==========================================================

def health_check(jobs):

    errors = []

    for index, job in enumerate(jobs):

        if not job.get("job_id"):

            errors.append(

                f"Missing job_id at index {index}"

            )

        if not job.get("title"):

            errors.append(

                f"Missing title at index {index}"

            )

        if not job.get("url"):

            errors.append(

                f"Missing url at index {index}"

            )

    if errors:

        logger.warning(

            "Health Check Failed (%d issues)",

            len(errors)

        )

        return False

    logger.info(

        "Health Check Passed"

    )

    return True


# ==========================================================
# Production Optimizer Runner
# ==========================================================

def sanitize_existing_jobs(old_jobs):
    """Revalidate the persistent database on every run.

    Earlier versions trusted old ``is_valid_post`` flags, which allowed hundreds
    of navigation/category links to survive forever as "Latest Jobs".
    """
    clean = []
    rejected = 0
    for raw in old_jobs or []:
        if not isinstance(raw, dict):
            rejected += 1
            continue
        job = dict(raw)
        title = str(job.get("title", "") or "").strip()
        url = str(job.get("url", "") or "").strip()
        category = classify_post(title, url, job.get("description", ""), job.get("source", ""))
        if not category:
            rejected += 1
            continue
        job["title"] = title
        job["url"] = url
        job["category"] = category
        job["post_type"] = category
        job["is_valid_post"] = True
        job["job_id"] = generate_job_id(job)
        job["department"] = detect_department(job)
        job["year"] = extract_year(title)
        # Never use scraped_at/workflow date as a public Published Date.
        # Only explicit source/notification/posted dates are eligible.
        if not job.get("publish_date"):
            old_date = job.get("notification_date") or job.get("source_date") or job.get("published_date") or job.get("date_published") or job.get("posted_date") or job.get("date")
            if old_date:
                job["publish_date"] = str(old_date)[:30]
        clean.append(job)
    logger.info("DATABASE SANITIZE | Input=%d Valid=%d Rejected=%d", len(old_jobs or []), len(clean), rejected)
    return clean


def run_optimizer(old_jobs, new_jobs):

    logger.info("Starting Optimizer Pipeline")

    # Critical legacy-data fix: never trust old is_valid_post/category flags.
    old_jobs = sanitize_existing_jobs(old_jobs)
    new_jobs = optimize_jobs(new_jobs)

    valid_jobs = validate_jobs(new_jobs)

    merged_jobs = merge_jobs(

        old_jobs,

        valid_jobs

    )

    fresh_jobs = filter_new_jobs(
        old_jobs,
        valid_jobs
    )

    logger.info("=" * 60)
    logger.info("Old Jobs   : %d", len(old_jobs))
    logger.info("Valid Jobs : %d", len(valid_jobs))
    logger.info("Merged Jobs: %d", len(merged_jobs))
    logger.info("Fresh Jobs : %d", len(fresh_jobs))
    logger.info("=" * 60)

    for job in fresh_jobs[:20]:
        logger.info("NEW : %s", job.get("title"))

    summary = build_summary(

        merged_jobs

    )

    print_summary(summary)

    health_check(merged_jobs)

    logger.info(

        "Optimizer Finished Successfully"

    )

    return {

        "jobs": merged_jobs,

        "new_jobs": fresh_jobs,

        "summary": summary

    }


# ==========================================================
# Standalone Testing
# ==========================================================

if __name__ == "__main__":

    sample_old = []

    sample_new = [

        {

            "title": "SSC CGL Recruitment 2026",

            "url": "https://ssc.gov.in",

            "source": "SSC",

            "priority": 100

        },

        {

            "title": "IBPS PO Recruitment 2026",

            "url": "https://ibps.in",

            "source": "IBPS",

            "priority": 95

        }

    ]

    result = run_optimizer(

        sample_old,

        sample_new

    )

    logger.info(

        "Final Jobs : %d",

        len(result["jobs"])

    )
