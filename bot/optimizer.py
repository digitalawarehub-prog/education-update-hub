"""
=========================================================
Education Update Hub
Production Optimizer v4
=========================================================
"""

import hashlib
import logging
import re
from datetime import datetime

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
    "vacancy": "Recruitment",
    "notification": "Recruitment",
    "admit": "Admit Card",
    "result": "Result",
    "answer key": "Answer Key",
    "syllabus": "Syllabus",
    "scholarship": "Scholarship",
}

# ==========================================================
# Department Rules
# ==========================================================

DEPARTMENT_RULES = {
    "Banking": [
        "bank",
        "ibps",
        "rbi",
        "nabard",
        "lic"
    ],

    "Railway": [
        "railway",
        "rrb",
        "rrc"
    ],

    "Defence": [
        "army",
        "navy",
        "air force",
        "drdo",
        "bsf",
        "crpf",
        "cisf",
        "itbp"
    ],

    "Teaching": [
        "teacher",
        "faculty",
        "lecturer",
        "professor",
        "principal"
    ],

    "Medical": [
        "medical",
        "doctor",
        "nurse",
        "pharmacist",
        "aiims"
    ]
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

    key = "|".join([
        normalize_text(job.get("title", "")),
        normalize_text(job.get("url", "")),
        normalize_text(job.get("source", "")),
        normalize_text(job.get("last_date", ""))
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

def detect_category(title):

    text = normalize_text(title)

    for keyword, category in CATEGORY_MAP.items():

        if keyword in text:

            return category

    return "Latest Jobs"


# ==========================================================
# Detect Department
# ==========================================================

def detect_department(title):

    text = normalize_text(title)

    for department, keywords in DEPARTMENT_RULES.items():

        if any(word in text for word in keywords):

            return department

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

    job["job_id"] = generate_job_id(job)

    job["category"] = detect_category(

        job.get("title", "")

    )

    job["department"] = detect_department(

        job.get("title", "")

    )

    job["year"] = extract_year(

        job.get("title", "")

    )

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

    jobs = validate_jobs(jobs)
jobs = remove_duplicates(jobs)
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

def merge_jobs(old_jobs, new_jobs):

    merged = {}

    for job in old_jobs:

        if job.get("job_id"):

            merged[job["job_id"]] = job

    added = 0
    updated = 0

    for job in new_jobs:

        jid = job.get("job_id")

        if not jid:
            continue

        if jid in merged:

            old = merged[jid]

            if job.get("priority", 0) > old.get("priority", 0):

                merged[jid] = job

                updated += 1

        else:

            merged[jid] = job

            added += 1

    logger.info(
        "Merge Completed | Added=%d Updated=%d Total=%d",
        added,
        updated,
        len(merged)
    )

    return list(merged.values())


# ==========================================================
# Filter Only New Jobs
# ==========================================================

def filter_new_jobs(old_jobs, new_jobs):

    existing = {

        job.get("job_id")

        for job in old_jobs

        if job.get("job_id")

    }

    fresh = [

        job

        for job in new_jobs

        if job.get("job_id") not in existing

    ]

    logger.info(

        "New Jobs Found : %d",

        len(fresh)

    )

    return fresh


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

        if ok:

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

def run_optimizer(old_jobs, new_jobs):

    logger.info("Starting Optimizer Pipeline")

    new_jobs = optimize_jobs(new_jobs)

    valid_jobs = validate_jobs(new_jobs)

    merged_jobs = merge_jobs(

        old_jobs,

        valid_jobs

    )

    fresh_jobs = filter_new_jobs(

        old_jobs,

        merged_jobs

    )

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
