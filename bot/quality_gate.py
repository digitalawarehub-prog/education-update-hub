"""Publication quality gate for Education Update Hub.

Only reader-friendly, useful records are eligible for an indexable HTML post.
Missing fields are omitted; placeholders are never rendered.
"""
import re
from urllib.parse import urlparse

PLACEHOLDERS = {
    "not available", "not mentioned", "not provided", "check official notification",
    "check notification", "as per rules", "to be announced", "tba", "n/a", "na",
    "none", "null", "unknown", "-", "--", "—", "–", ""
}

NOISE_TITLE_PATTERNS = [
    r"^\s*(apply|login|register|home|contact|about|privacy|disclaimer|faq|support|more|view all|click here)\s*$",
    r"^(?:advertisement|notification|notice|recruitment|recruitment exams|crp|crp\s*[-–]\s*(?:rrbs|clerks|clerk))$",
    r"important\s+links?", r"facility\s+to\s+candidates", r"fill\s+online\s+details",
    r"modify\s+online\s+details", r"select\s+your\s+language", r"skip\s+to",
    r"go\s+to\s+index", r"table\s+of\s+contents", r"\{\{.*?\}\}",
]


def clean_optional_value(value):
    if value is None:
        return ""
    value = re.sub(r"\s+", " ", str(value)).strip(" -:|;,.\n\t")
    if not value or value.lower() in PLACEHOLDERS:
        return ""
    return value


def _title_is_valid(title):
    title = re.sub(r"\s+", " ", str(title or "")).strip()
    if len(title) < 8 or len(title) > 500:
        return False
    low = title.lower()
    if any(re.search(p, low, re.I) for p in NOISE_TITLE_PATTERNS):
        return False
    # Reject titles made mostly of symbols/numbers.
    meaningful = len(re.findall(r"[A-Za-z\u0900-\u0DFF]", title))
    return meaningful >= 5


def _text_length(job):
    parts = [job.get("reader_summary"), job.get("notification_text_clean"), job.get("content"), job.get("description")]
    text = " ".join(str(x or "") for x in parts)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return len(text)


def is_publishable(job):
    title = str(job.get("title") or "").strip()
    url = str(job.get("url") or "").strip()
    if not _title_is_valid(title) or not url:
        return False
    if urlparse(url).scheme not in {"http", "https"}:
        return False

    validation = str(job.get("detail_validation") or "").lower()
    if "source page does not match post title" in validation:
        return False

    detail_keys = (
        "vacancy", "qualification", "salary", "age_limit", "application_fee",
        "selection_process", "exam_date", "application_start", "last_date"
    )
    detail_count = sum(1 for k in detail_keys if clean_optional_value(job.get(k)))
    pdf = clean_optional_value(job.get("notification_pdf"))
    pdf_ok = bool(pdf and re.sub(r"\?.*$", "", pdf).lower().endswith(".pdf"))
    apply_ok = bool(clean_optional_value(job.get("apply_link")))
    useful_text = _text_length(job) >= 120

    category = str(job.get("category") or "").lower()
    special = any(x in category for x in ("result", "admit", "answer key", "syllabus"))

    if detail_count >= 1:
        return True
    if useful_text and (pdf_ok or apply_ok or clean_optional_value(job.get("official_website"))):
        return True
    if special and (pdf_ok or apply_ok or clean_optional_value(job.get("official_website"))):
        return True
    return False
