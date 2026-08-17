"""Canonical sitemap generator for the live custom domain."""
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from config import SITE_URL
from url_utils import slugify as canonical_slug, post_site_url, post_exists

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
    return canonical_slug(title, job)


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
        if not post_exists(job):
            continue
        add(post_site_url(job), lastmod=today, priority="0.9", freq="daily")

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
