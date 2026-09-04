"""Canonical URL helpers for Education Update Hub.

Every generator that creates or references an auto-generated post MUST use
this module.  This prevents Hindi/Unicode slugs, stale database slugs and
canonical/homepage/search/sitemap mismatches.
"""
import hashlib
import re
from pathlib import Path
try:
    from unidecode import unidecode
except ImportError:
    import unicodedata
    def unidecode(value):
        # Dependency-free fallback. Common Hindi words are already replaced
        # above; remaining Unicode is safely removed from the filename.
        return unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")

BASE_URL = "https://educationupdatehub.in"
ROOT_DIR = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT_DIR / "generated" / "posts"

# A small cleanup map keeps common Hindi words readable even after transliteration.
REPLACEMENTS = {
    "सरकारी": "government", "नौकरी": "job", "नौकरियां": "jobs",
    "भर्ती": "recruitment", "भर्तियां": "recruitments", "रिक्ति": "vacancy",
    "रिक्तियां": "vacancies", "अधिसूचना": "notification", "प्रवेश": "admit",
    "पत्र": "card", "परिणाम": "result", "उत्तर": "answer", "कुंजी": "key",
    "छात्रवृत्ति": "scholarship", "परीक्षा": "exam", "पाठ्यक्रम": "syllabus",
    "शिक्षक": "teacher", "पुलिस": "police", "वन": "forest", "विभाग": "department",
    "केंद्र": "central", "राज्य": "state", "उत्तराखंड": "uttarakhand",
    "ऑनलाइन": "online", "आवेदन": "application", "अंतिम": "last", "तिथि": "date",
    "योजना": "scheme", "विज्ञापन": "advertisement", "अभ्यर्थी": "candidate",
}

def safe(value, default=""):
    if value is None:
        return default
    return str(value).strip()

def slugify(title, job=None):
    job = job or {}
    original = safe(title)
    if not original:
        original = "update"

    raw = re.sub(r"\{\{.*?\}\}", "", original).strip().lower()
    raw = raw.replace("&", " and ")
    for src, dst in sorted(REPLACEMENTS.items(), key=lambda x: len(x[0]), reverse=True):
        raw = raw.replace(src, dst)

    # Transliterate Hindi/other Unicode to stable ASCII before filename creation.
    raw = unidecode(raw)
    slug = re.sub(r"[^a-z0-9]+", "-", raw)
    slug = re.sub(r"-+", "-", slug).strip("-")

    job_id = safe(job.get("job_id"))
    jid = re.sub(r"[^a-z0-9]+", "", job_id.lower())[-10:]

    # Guarantee deterministic uniqueness.  Only append an id/hash when needed.
    if slug:
        if len(slug) > 135:
            slug = slug[:135].rstrip("-")
        if jid:
            # Keep URLs stable for scraper records that have a real id.
            slug = f"{slug}-{jid}"
        elif len(original) != len(slug) or re.search(r"[^\x00-\x7f]", original):
            digest = hashlib.sha1(original.encode("utf-8")).hexdigest()[:8]
            slug = f"{slug}-{digest}"
        return slug[:150].rstrip("-")

    category = re.sub(r"[^a-z0-9]+", "-", safe(job.get("category"), "update").lower()).strip("-") or "update"
    year_match = re.findall(r"20\d{2}", original + " " + safe(job.get("year")))
    year = year_match[-1] if year_match else "2026"
    digest = hashlib.sha1((original + "|" + job_id).encode("utf-8")).hexdigest()[:10]
    return f"{category}-{year}-{jid or digest}"[:150].rstrip("-")

def post_filename(job):
    return slugify(job.get("title", ""), job) + ".html"

def post_relative_url(job):
    return f"generated/posts/{post_filename(job)}"

def post_site_url(job):
    return f"{BASE_URL}/generated/posts/{post_filename(job)}"

def post_path(job):
    return POSTS_DIR / post_filename(job)

def post_exists(job):
    return post_path(job).is_file()
