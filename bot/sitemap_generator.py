# =====================================================
# Part 1 - Imports, Config & Helpers
# =====================================================

import os
import re
import logging
import xml.etree.ElementTree as ET

from datetime import datetime

from config import SITE_URL


SITEMAP_FILE = "sitemap.xml"

NS = "http://www.sitemaps.org/schemas/sitemap/0.9"

ET.register_namespace("", NS)


logger = logging.getLogger("SitemapGenerator")

if not logger.handlers:

    handler = logging.StreamHandler()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    handler.setFormatter(formatter)

    logger.addHandler(handler)

logger.setLevel(logging.INFO)


def slugify(text):

    text = str(text).lower()

    text = re.sub(r"&", " and ", text)

    text = re.sub(r"[^a-z0-9]+", "-", text)

    text = re.sub(r"-{2,}", "-", text)

    return text.strip("-")


def indent_xml(elem, level=0):

    indent = "\n" + level * "    "

    if len(elem):

        if not elem.text or not elem.text.strip():

            elem.text = indent + "    "

        for child in elem:

            indent_xml(child, level + 1)

        if not child.tail or not child.tail.strip():

            child.tail = indent

    else:

        if level and (not elem.tail or not elem.tail.strip()):

            elem.tail = indent


def create_sitemap():

    if os.path.exists(SITEMAP_FILE):

        logger.info("Sitemap already exists.")

        return

    urlset = ET.Element(f"{{{NS}}}urlset")

    home = ET.SubElement(
        urlset,
        f"{{{NS}}}url"
    )

    ET.SubElement(
        home,
        f"{{{NS}}}loc"
    ).text = SITE_URL

    ET.SubElement(
        home,
        f"{{{NS}}}lastmod"
    ).text = datetime.now().strftime("%Y-%m-%d")

    ET.SubElement(
        home,
        f"{{{NS}}}changefreq"
    ).text = "daily"

    ET.SubElement(
        home,
        f"{{{NS}}}priority"
    ).text = "1.0"

    indent_xml(urlset)

    tree = ET.ElementTree(urlset)

    tree.write(

        SITEMAP_FILE,

        encoding="utf-8",

        xml_declaration=True

    )

    logger.info(
        "New sitemap created."
    )
    # =====================================================
# Part 2 - Production Sitemap Updater
# =====================================================

def update_sitemap(jobs):

    if not jobs:

        logger.info("No new jobs. Sitemap skipped.")

        return False

    try:

        create_sitemap()

        tree = ET.parse(SITEMAP_FILE)

        root = tree.getroot()

        existing = set()

        for url in root.findall(f"{{{NS}}}url"):

            loc = url.find(f"{{{NS}}}loc")

            if loc is not None and loc.text:

                existing.add(loc.text)

        added = 0

        for job in jobs:

            title = job.get("title")

            if not title:

                continue

            slug = slugify(title)

            page_url = (
                f"{SITE_URL}/generated/{slug}.html"
            )

            if page_url in existing:

                continue

            url = ET.SubElement(
                root,
                f"{{{NS}}}url"
            )

            ET.SubElement(
                url,
                f"{{{NS}}}loc"
            ).text = page_url

            ET.SubElement(
                url,
                f"{{{NS}}}lastmod"
            ).text = datetime.now().strftime("%Y-%m-%d")

            category = job.get(
                "category",
                "Latest Jobs"
            ).lower()

            if "result" in category:

                changefreq = "monthly"
                priority = "0.70"

            elif "admit" in category:

                changefreq = "weekly"
                priority = "0.80"

            else:

                changefreq = "daily"
                priority = "0.90"

            ET.SubElement(
                url,
                f"{{{NS}}}changefreq"
            ).text = changefreq

            ET.SubElement(
                url,
                f"{{{NS}}}priority"
            ).text = priority

            existing.add(page_url)

            added += 1

        indent_xml(root)

        tree.write(

            SITEMAP_FILE,

            encoding="utf-8",

            xml_declaration=True

        )

        logger.info(

            "Sitemap updated successfully (%d new URLs)",

            added

        )

        return True

    except Exception:

        logger.exception(

            "Failed to update sitemap."

        )

        return False
        # =====================================================
# Part 3 - Validation & Runner
# =====================================================

def validate_sitemap():

    if not os.path.exists(SITEMAP_FILE):

        logger.error("Sitemap file not found.")

        return False

    try:

        tree = ET.parse(SITEMAP_FILE)

        root = tree.getroot()

        urls = root.findall(f"{{{NS}}}url")

        if not urls:

            logger.warning(
                "Sitemap contains no URLs."
            )

            return False

        logger.info(

            "Sitemap validation successful (%d URLs).",

            len(urls)

        )

        return True

    except ET.ParseError:

        logger.exception(

            "Invalid XML in sitemap."

        )

        return False

    except Exception:

        logger.exception(

            "Sitemap validation failed."

        )

        return False


# =====================================================
# Production Runner
# =====================================================

def run_sitemap_update(jobs):

    success = update_sitemap(jobs)

    if not success:

        return False

    return validate_sitemap()


# =====================================================
# Standalone Testing
# =====================================================

if __name__ == "__main__":

    sample_jobs = [

        {

            "title":
            "SSC CGL Recruitment 2026",

            "category":
            "Latest Jobs"

        },

        {

            "title":
            "IBPS PO Recruitment 2026",

            "category":
            "Bank Jobs"

        }

    ]

    success = run_sitemap_update(
        sample_jobs
    )

    if success:

        logger.info(

            "Sitemap generator completed successfully."

        )

    else:

        logger.error(

            "Sitemap generator failed."

        )
