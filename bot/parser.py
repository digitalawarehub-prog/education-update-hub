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
# ==========================================================
# BAD TITLE FILTER
# ==========================================================

BAD_WORDS = {

    # Navigation
    "home",
    "homepage",
    "about",
    "about us",
    "organisation",
    "organization",
    "organization structure",
    "composition of the commission",
    "different section",

    # Office
    "chairman",
    "hon'ble",
    "member",
    "finance controller",
    "examination controller",
    "public information officer",
    "appellate authority",
    "web information manager",

    # Website
    "contact",
    "contact us",
    "feedback",
    "gallery",
    "photo gallery",
    "privacy",
    "cookie",
    "copyright",
    "accessibility",
    "accessibility tools",
    "hide images",
    "faq",
    "login",
    "logout",
    "sitemap",
    "website policies",

    # Misc
    "government orders",
    "digital uttarakhand",
    "cm office",
    "cm dashboard",
    "national portal",
    "nic",
    "meity",
    "sanction posts",
    "act and rule",
    "rti",
    "manual",
}


# ==========================================================
# GOOD KEYWORDS
# ==========================================================

GOOD_WORDS = {

    "recruitment",
    "vacancy",
    "notification",
    "advertisement",
    "advt",
    "apply",
    "online application",
    "result",
    "recommendation",
    "answer key",
    "admit card",
    "syllabus",
    "exam",
    "exam calendar",
    "selection",

    "भर्ती",
    "विज्ञापन",
    "विज्ञप्ति",
    "पदनाम",
    "परीक्षा",
    "प्रवेश पत्र",
    "उत्तरकुंजी",
    "पाठ्यक्रम",
    "संस्तुति",
    "परिणाम",
}
# ==========================================================
# URL FILTER
# ==========================================================

def clean_url(base, href):

    if not href:
        return None

    href = href.strip()

    if (
        href.startswith("#")
        or href.startswith("javascript:")
        or href.startswith("mailto:")
        or href.startswith("tel:")
    ):
        return None

    url = urljoin(base, href)

    BAD_URLS = (

        "/organization",
        "/organisation",
        "/organization-structure",
        "/about",
        "/contact",
        "/feedback",
        "/gallery",
        "/photo-gallery",
        "/chairman",
        "/honble",
        "/member",
        "/finance-controller",
        "/examination-controller",
        "/different-section",
        "/website-policies",
        "/privacy",
        "/cookie",
        "/web-information-manager",
        "/appellate-authority",
        "/public-information-officer",
        "/act-and-rule",
        "/rti",
        "/manual",

    )

    lower = url.lower()

    for bad in BAD_URLS:
        if bad in lower:
            return None

    return url


# ==========================================================
# TITLE FILTER
# ==========================================================

def allow_title(title):

    if not title:
        return False

    text = clean_title(title).lower()

    if len(text) < 6:
        return False

    for bad in BAD_WORDS:
        if bad in text:
            return False

    for good in GOOD_WORDS:
        if good in text:
            return True

    return False
    # ==========================================================
# LINK EXTRACTOR
# ==========================================================

def extract_links(soup, base_url):

    results = []
    seen = set()

    for a in soup.find_all("a", href=True):

        # -----------------------------
        # URL
        # -----------------------------
        href = clean_url(
            base_url,
            a.get("href")
        )

        if not href:
            continue

        # -----------------------------
        # Title
        # -----------------------------
        title = clean_title(
            a.get_text(
                " ",
                strip=True
            )
        )

        if not title:
            continue

        if not allow_title(title):
            continue

        # -----------------------------
        # Accept only useful URLs
        # -----------------------------
        lower_url = href.lower()

        VALID_URL = (

            "/document/" in lower_url
            or ".pdf" in lower_url
            or "recruitment" in lower_url
            or "notification" in lower_url
            or "admit-card" in lower_url
            or "answer" in lower_url
            or "result" in lower_url
            or "syllabus" in lower_url
            or "exam" in lower_url
            or "calendar" in lower_url

        )

        if not VALID_URL:
            continue

        # -----------------------------
        # Duplicate Check
        # -----------------------------
        key = (title.lower(), href)

        if key in seen:
            continue

        seen.add(key)

        # -----------------------------
        # Save
        # -----------------------------
        results.append({

            "title": title,
            "url": href

        })

    return results
    # ==========================================================
# PARSE JOBS
# ==========================================================

def parse_jobs(jobs):

    parsed = []

    seen = set()

    for job in jobs:

        title = clean_title(
            job.get("title", "")
        )

        url = clean_url(
            job.get("url", ""),
            job.get("url", "")
        )

        if not title:
            continue

        if not url:
            continue

        if not allow_title(title):
            continue

        key = (
            title.lower(),
            url
        )

        if key in seen:
            continue

        seen.add(key)

        lower = title.lower()

        # --------------------------------
        # Category Detection
        # --------------------------------

        category = "Latest Updates"

        if any(x in lower for x in (
            "recruitment",
            "vacancy",
            "advertisement",
            "advt",
            "notification",
            "apply",
            "भरती",
            "भर्ती",
            "विज्ञापन",
            "विज्ञप्ति",
            "पदनाम"
        )):
            category = "Latest Jobs"

        elif any(x in lower for x in (
            "admit card",
            "hall ticket",
            "प्रवेश पत्र"
        )):
            category = "Admit Card"

        elif any(x in lower for x in (
            "result",
            "selection",
            "recommendation",
            "परिणाम",
            "संस्तुति"
        )):
            category = "Result"

        elif any(x in lower for x in (
            "answer key",
            "उत्तरकुंजी"
        )):
            category = "Answer Key"

        elif any(x in lower for x in (
            "syllabus",
            "पाठ्यक्रम"
        )):
            category = "Syllabus"

        elif any(x in lower for x in (
            "exam calendar",
            "exam programme",
            "परीक्षा कार्यक्रम"
        )):
            category = "Exam"

        parsed.append({

            "title": title,
            "url": url,
            "category": category

        })

    return parsed
    # ==========================================================
# FINAL CLEANUP
# ==========================================================

def finalize_jobs(jobs):

    cleaned = []

    seen = set()

    for job in jobs:

        title = clean_title(
            job.get("title", "")
        )

        url = job.get("url", "").strip()

        category = job.get(
            "category",
            "Latest Updates"
        )

        if not title:
            continue

        if not url:
            continue

        if url == "#":
            continue

        if url.startswith("javascript"):
            continue

        key = (
            title.lower(),
            url
        )

        if key in seen:
            continue

        seen.add(key)

        cleaned.append({

            "title": title,
            "url": url,
            "category": category

        })

    cleaned.sort(
        key=lambda x: x["title"].lower()
    )

    return cleaned


# ==========================================================
# MAIN PARSER
# ==========================================================

def parse(soup, base_url):

    links = extract_links(
        soup,
        base_url
    )

    jobs = parse_jobs(
        links
    )

    jobs = finalize_jobs(
        jobs
    )

    return jobs
