import os
import re
from datetime import datetime, UTC
import xml.etree.ElementTree as ET

SITE_URL = "https://educationupdatehub.in"
SITEMAP_FILE = "sitemap.xml"

NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
ET.register_namespace("", NS)


def slugify(title):
    title = title.lower()
    title = re.sub(r"[^a-z0-9]+", "-", title)
    return title.strip("-")


def create_sitemap():

    if os.path.exists(SITEMAP_FILE):
        return

    urlset = ET.Element(
        f"{{{NS}}}urlset"
    )

    tree = ET.ElementTree(urlset)

    tree.write(
        SITEMAP_FILE,
        encoding="utf-8",
        xml_declaration=True
    )


def update_sitemap(jobs):

    if not jobs:
        print("No new jobs. Sitemap skipped.")
        return

    create_sitemap()

    tree = ET.parse(SITEMAP_FILE)
    root = tree.getroot()

    existing = set()

    for url in root.findall(f"{{{NS}}}url"):

        loc = url.find(f"{{{NS}}}loc")

        if loc is not None:
            existing.add(loc.text)

    added = 0

    for job in jobs:

        slug = slugify(job["title"])

        page = f"{SITE_URL}/generated/{slug}.html"

        if page in existing:
            continue

        url = ET.SubElement(root, f"{{{NS}}}url")

        ET.SubElement(
            url,
            f"{{{NS}}}loc"
        ).text = page

        ET.SubElement(
            url,
            f"{{{NS}}}lastmod"
        ).text = datetime.now(UTC).strftime("%Y-%m-%d")

        ET.SubElement(
            url,
            f"{{{NS}}}changefreq"
        ).text = "weekly"

        ET.SubElement(
            url,
            f"{{{NS}}}priority"
        ).text = "0.80"

        existing.add(page)
        added += 1

    tree.write(
        SITEMAP_FILE,
        encoding="utf-8",
        xml_declaration=True
    )

    print(f"Sitemap Updated ({added} new URLs)")
