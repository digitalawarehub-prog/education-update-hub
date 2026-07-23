import os
from datetime import datetime
import xml.etree.ElementTree as ET

SITE_URL = "https://educationupdatehub.in"
SITEMAP_FILE = "sitemap.xml"


def slugify(title):
    return (
        title.lower()
        .replace(" ", "-")
        .replace("/", "-")
    )


def create_sitemap():
    if not os.path.exists(SITEMAP_FILE):
        urlset = ET.Element(
            "urlset",
            xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        )

        tree = ET.ElementTree(urlset)
        tree.write(
            SITEMAP_FILE,
            encoding="utf-8",
            xml_declaration=True
        )


def update_sitemap(jobs):

    create_sitemap()

    tree = ET.parse(SITEMAP_FILE)
    root = tree.getroot()

    existing = set()

    for url in root.findall("{*}url"):

        loc = url.find("{*}loc")

        if loc is not None:
            existing.add(loc.text)

    for job in jobs:

        slug = slugify(job["title"])

        page = f"{SITE_URL}/generated/{slug}.html"

        if page in existing:
            continue

        url = ET.SubElement(root, "url")

        loc = ET.SubElement(url, "loc")
        loc.text = page

        lastmod = ET.SubElement(url, "lastmod")
        lastmod.text = datetime.utcnow().strftime("%Y-%m-%d")

        changefreq = ET.SubElement(url, "changefreq")
        changefreq.text = "weekly"

        priority = ET.SubElement(url, "priority")
        priority.text = "0.80"

    tree.write(
        SITEMAP_FILE,
        encoding="utf-8",
        xml_declaration=True
    )

    print("Sitemap Updated Successfully")
