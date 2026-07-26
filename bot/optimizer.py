import hashlib
import re


CATEGORY_MAP = {
    "admit": "Admit Card",
    "result": "Result",
    "answer key": "Answer Key",
    "syllabus": "Syllabus",
    "recruitment": "Recruitment",
    "vacancy": "Recruitment",
    "notification": "Recruitment",
}


def generate_id(title, url):
    return hashlib.md5(
        f"{title}{url}".encode()
    ).hexdigest()


def detect_category(title):

    text = title.lower()
from datetime import datetime


def add_timestamp(jobs):

    now = datetime.utcnow().isoformat()

    for job in jobs:

        job["scraped_at"] = now

    return jobs
    def merge_jobs(old_jobs, new_jobs):

    data = {}

    for job in old_jobs + new_jobs:

        data[job["job_id"]] = job

    return list(data.values())
    def filter_new_jobs(old_jobs, new_jobs):

    old = {

        job["job_id"]

        for job in old_jobs

    }

    return [

        job

        for job in new_jobs

        if job["job_id"] not in old

    ]
    for key, value in CATEGORY_MAP.items():

        if key in text:
            return value

    return "Latest Job"


def extract_year(title):

    m = re.search(r"(20\d{2})", title)

    if m:
        return m.group(1)

    return ""
  def optimize_jobs(jobs):

    output = []

    seen = set()

    for job in jobs:

        uid = generate_id(
            job["title"],
            job["url"]
        )

        if uid in seen:
            continue

        seen.add(uid)

        job["id"] = uid

        job["category"] = detect_category(
            job["title"]
        )

        job["year"] = extract_year(
            job["title"]
        )

        output.append(job)

    return output
