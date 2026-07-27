import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from downloader import download
from utils.helpers import normalize


def get_soup(url):

    html = download(url)

    if not html:
        return None

    return BeautifulSoup(html, "lxml")


def clean_url(base, href):

    if not href:
        return None

    href = href.strip()

    if href.startswith("#"):
        return None

    if href.startswith("javascript:"):
        return None

    if href.startswith("mailto:"):
        return None

    if href.startswith("tel:"):
        return None

    return urljoin(base, href)


def clean_title(title):

    if not title:
        return ""

    title = normalize(title)

    title = re.sub(r"\|.*$", "", title)
    title = re.sub(r"\(.*?\)", "", title)

    title = title.replace("_", " ")
    title = title.replace("-", " ")

    title = re.sub(r"\s+", " ", title)

    return title.strip()


BAD_WORDS = {

    "privacy",
    "cookie",
    "gallery",
    "feedback",
    "contact",
    "home",
    "login",
    "logout",
    "faq",
    "copyright",
    "tender",
    "auction",
    "accessibility",
    "sitemap",
    "organisation"

}


def allow_title(title):

    text = title.lower()

    for word in BAD_WORDS:

        if word in text:
            return False

   return True

def extract_links(soup, base_url):

    results = []

    seen = set()

    for a in soup.find_all("a", href=True):

        href = clean_url(
            base_url,
            a["href"]
        )

        if not href:
            continue

        title = clean_title(
            a.get_text(
                " ",
                strip=True
            )
        )

        if len(title) < 6:
            continue

        if not allow_title(title):
            continue

        if href in seen:
            continue

        seen.add(href)

        results.append({

            "title": title,

            "url": href

        })

    return results
