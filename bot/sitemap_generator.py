"""Canonical sitemap generator for the live custom domain."""
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from config import SITE_URL

SITEMAP_FILE = Path(__file__).resolve().parent.parent / "sitemap.xml"
NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
ET.register_namespace("", NS)
logger = logging.getLogger("SitemapGenerator")

STATIC_PAGES = [
    "", "about.html", "contact.html", "privacy-policy.html", "disclaimer.html",
    "terms-and-conditions.html", "latest-jobs.html", "admit-card.html", "result.html",
    "answer-key.html", "syllabus.html", "scholarship.html", "teaching-exams.html",
    "entrance-exams.html", "government-schemes.html", "uttarakhand-jobs.html",
    "central-government-jobs.html", "other-state-jobs.html", "banking-jobs.html",
    "railway.html", "ssc.html", "upsc.html", "ctet.html", "utet.html", "deled.html",
]


def _slug(title, job=None):
    raw = str(title or "").strip().lower().replace("&", " and ")
    mapping = {"सरकारी":"government","नौकरी":"job","नौकरियां":"jobs","भर्ती":"recruitment","भर्तियां":"recruitments","रिक्ति":"vacancy","रिक्तियां":"vacancies","अधिसूचना":"notification","प्रवेश":"admit","पत्र":"card","परिणाम":"result","उत्तर":"answer","कुंजी":"key","छात्रवृत्ति":"scholarship","परीक्षा":"exam","पाठ्यक्रम":"syllabus","शिक्षक":"teacher","पुलिस":"police","वन":"forest","विभाग":"department","केंद्र":"central","राज्य":"state","उत्तराखंड":"uttarakhand","ऑनलाइन":"online","आवेदन":"application","अंतिम":"last","तिथि":"date"}
    for a,b in sorted(mapping.items(), key=lambda x: len(x[0]), reverse=True): raw = raw.replace(a,b)
    slug = re.sub(r"[^a-z0-9]+", "-", raw)
    slug = re.sub(r"-+", "-", slug).strip("-")
    if slug:
        if len(slug) > 150:
            import hashlib
            seed = str(title or "") + "|" + str((job or {}).get("job_id", ""))
            suffix = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:10]
            slug = slug[:139].rstrip("-") + "-" + suffix
        return slug
    jid = re.sub(r"[^a-z0-9]", "", str((job or {}).get("job_id", ""))).lower()[-10:] or "update"
    return "update-" + jid


def _valid_post(job):
    title = str(job.get("title", "")).strip()
    return bool(title and job.get("is_valid_post", True))


def update_sitemap(jobs=None):
    jobs = jobs or []
    root = ET.Element(f"{{{NS}}}urlset")
    today = datetime.now().strftime("%Y-%m-%d")
    seen = set()

    def add(loc, lastmod=today, priority="0.7", freq="weekly"):
        if loc in seen: return
        seen.add(loc)
        u = ET.SubElement(root, f"{{{NS}}}url")
        ET.SubElement(u, f"{{{NS}}}loc").text = loc
        ET.SubElement(u, f"{{{NS}}}lastmod").text = lastmod
        ET.SubElement(u, f"{{{NS}}}changefreq").text = freq
        ET.SubElement(u, f"{{{NS}}}priority").text = priority

    for page in STATIC_PAGES:
        add(f"{SITE_URL}/{page}" if page else f"{SITE_URL}/", priority="0.8" if page else "1.0", freq="daily" if not page else "weekly")

    # Only actual generated post files are included. This prevents deleted,
    # malformed and non-post database records from remaining in the sitemap.
    posts_dir = Path(__file__).resolve().parent.parent / "generated" / "posts"
    file_names = {p.name for p in posts_dir.glob("*.html")} if posts_dir.exists() else set()
    for job in jobs:
        if not _valid_post(job):
            continue
        slug = _slug(job.get("title"), job)
        filename = slug + ".html"
        if filename not in file_names:
            continue
        add(f"{SITE_URL}/generated/posts/{filename}", lastmod=today, priority="0.9", freq="daily")

    tree = ET.ElementTree(root)
    tree.write(SITEMAP_FILE, encoding="utf-8", xml_declaration=True)
    logger.info("Sitemap updated successfully (%d URLs)", len(seen))
    return True


def create_sitemap():
    return update_sitemap([])


def validate_sitemap():
    try:
        root = ET.parse(SITEMAP_FILE).getroot()
        urls = root.findall(f"{{{NS}}}url")
        ok = bool(urls)
        logger.info("Sitemap validation: %s (%d URLs)", "PASSED" if ok else "FAILED", len(urls))
        return ok
    except Exception:
        logger.exception("Sitemap validation failed")
        return False


# Backward-compatible API used by older scraper/monitor modules.
def generate_sitemap(jobs=None):
    return update_sitemap(jobs)
