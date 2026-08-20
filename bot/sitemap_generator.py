"""Canonical sitemap generator for Education Update Hub."""
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET
from config import SITE_URL

ROOT_DIR = Path(__file__).resolve().parent.parent
SITEMAP_FILE = ROOT_DIR / "sitemap.xml"
NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
ET.register_namespace("", NS)


def update_sitemap(jobs=None):
    """Rebuild sitemap from real local files; never publish stale/404 URLs."""
    urls = {SITE_URL.rstrip("/") + "/"}
    for path in ROOT_DIR.glob("*.html"):
        if path.name in {"index.html"}:
            continue
        urls.add(f"{SITE_URL.rstrip('/')}/{path.name}")
    posts_dir = ROOT_DIR / "generated" / "posts"
    if posts_dir.exists():
        for path in posts_dir.glob("*.html"):
            urls.add(f"{SITE_URL.rstrip('/')}/generated/posts/{path.name}")

    urlset = ET.Element(f"{{{NS}}}urlset")
    today = datetime.now().strftime("%Y-%m-%d")
    for loc in sorted(urls):
        u = ET.SubElement(urlset, f"{{{NS}}}url")
        ET.SubElement(u, f"{{{NS}}}loc").text = loc
        ET.SubElement(u, f"{{{NS}}}lastmod").text = today
        ET.SubElement(u, f"{{{NS}}}changefreq").text = "daily" if loc.endswith("/") else "weekly"
        ET.SubElement(u, f"{{{NS}}}priority").text = "1.0" if loc.endswith("/") else "0.8"

    ET.ElementTree(urlset).write(SITEMAP_FILE, encoding="utf-8", xml_declaration=True)
    print(f"Sitemap updated successfully ({len(urls)} URLs)")
    return True
