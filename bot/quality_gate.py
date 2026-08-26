"""Publication quality gate for Education Update Hub.
Only verified/available information is published. Missing fields are omitted.
"""
import re
from urllib.parse import urlparse

PLACEHOLDERS = {
    "not available", "not mentioned", "not provided", "check official notification",
    "check notification", "as per rules", "to be announced", "tba", "n/a", "na",
    "none", "null", "unknown", "-"
}

NOISE_TITLE_PATTERNS = [
    r"^\s*apply\s+(online|now)\s*$",
    r"^\s*(login|register|home|contact|about|privacy|disclaimer|faq)\s*$",
    r"click\s+here", r"fill\s+online\s+details", r"modify\s+online\s+details",
    r"important\s+links?$", r"view\s+all", r"more\s+details",
    r"\{\{.*?translate.*?\}\}", r"facility\s+to\s+candidates",
]

def clean_optional_value(value):
    if value is None:
        return ""
    value = re.sub(r"\s+", " ", str(value)).strip(" -:|;,.")
    if not value or value.lower() in PLACEHOLDERS:
        return ""
    return value

def _title_is_valid(title):
    title = re.sub(r"\s+", " ", str(title or "")).strip()
    if len(title) < 12 or len(title) > 500:
        return False
    low = title.lower()
    return not any(re.search(p, low, re.I) for p in NOISE_TITLE_PATTERNS)

def _has_real_value(job, keys):
    for key in keys:
        if clean_optional_value(job.get(key)):
            return True
    return False

def _content_length(job):
    parts = [job.get("description"), job.get("content"), job.get("summary")]
    text = " ".join(str(x or "") for x in parts)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return len(text)

def is_publishable(job):
    title = str(job.get("title") or "").strip()
    url = str(job.get("url") or "").strip()
    if not _title_is_valid(title) or not url:
        return False

    # Never publish obvious non-web/non-official destinations.
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False

    category = str(job.get("category") or "").lower()
    notification = clean_optional_value(job.get("notification_pdf"))
    content_ok = _content_length(job) >= 300
    detail_keys = (
        "vacancy", "qualification", "salary", "age_limit", "application_fee",
        "selection_process", "exam_date", "application_start", "last_date"
    )
    detail_count = sum(1 for k in detail_keys if clean_optional_value(job.get(k)))

    # A notification PDF is a strong source signal; otherwise require meaningful text/data.
    if notification:
        return True
    if content_ok:
        return True
    if detail_count >= 2:
        return True

    # Results/admit cards can be short but must have a real notice/link or meaningful text.
    if any(x in category for x in ("result", "admit", "answer key", "syllabus")):
        return bool(clean_optional_value(job.get("official_website")) or clean_optional_value(job.get("apply_link")) or content_ok)

    return False
