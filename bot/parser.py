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
# STRONG TITLE / URL FILTER
# ==========================================================

# Exact navigation / utility titles. These must NEVER become jobs.
BAD_EXACT_TITLES = {
    "home", "homepage", "about", "about us", "contact", "contact us",
    "feedback", "help", "faq", "login", "logout", "register",
    "registration", "new registration", "forgot password",
    "reset password", "view all", "view more", "read more",
    "click here", "more", "menu", "search", "sitemap",
    "vacancy position", "vacancy/nia",
    "recruitment/admission links",
    "download notification", "download hindi notification",
    "download english notification", "download guidelines",
    "website policies", "privacy policy", "copyright",
    "accessibility", "photo gallery", "gallery",
    "government orders", "digital uttarakhand", "cm office",
    "cm dashboard", "national portal of india", "national portal",
    "web information manager", "public information officer",
    "appellate authority", "finance controller",
    "examination controller", "organization", "organisation",
    "organization structure", "composition of the commission",
    "different section", "rti", "rti manuals", "act and rule",
}

# Phrases seen in application/login/navigation pages.
BAD_TITLE_PHRASES = (
    "step-1", "step 1", "step-2", "step 2",
    "forgot password", "reset password",
    "new registration", "login register", "login / register",
    "download hindi notification", "download english notification",
    "download notification", "download guidelines",
    "recruitment/admission links", "vacancy position", "vacancy/nia",
    "view all", "view more", "read more", "click here",
    "skip to main content", "select your language",
)

# Words which are too broad on their own and should not make a page a job.
WEAK_ONLY_WORDS = {
    "apply", "application", "registration", "posts", "selection",
    "exam", "calendar", "pdf", "download", "notification",
}

GOOD_WORDS = {
    "recruitment", "vacancy", "vacancies", "advertisement", "advt",
    "direct recruitment", "job", "jobs", "hiring", "engagement",
    "appointment", "walk-in", "walk in", "apprentice", "apprenticeship",
    "application invited", "applications are invited",
    "apply online", "online application", "career",
    "result", "recommendation", "answer key", "admit card", "hall ticket",
    "syllabus", "exam", "selection", "merit list", "shortlisted",
    "document verification", "counselling",
    "भर्ती", "विज्ञापन", "विज्ञप्ति", "अधिसूचना", "रिक्ति", "रिक्तियां",
    "पदनाम", "पदों", "आवेदन आमंत्रित", "ऑनलाइन आवेदन",
    "प्रवेश पत्र", "उत्तरकुंजी", "पाठ्यक्रम", "संस्तुति", "परिणाम",
    "नियुक्ति", "अप्रेंटिस", "साक्षात्कार",
}

BAD_URL_PARTS = (
    "/login", "/logout", "/register", "/registration", "/forgot",
    "/reset-password", "/reset_password", "/search",
    "/about", "/contact", "/feedback", "/gallery", "/photo-gallery",
    "/privacy", "/cookie", "/sitemap", "/website-policies",
    "/organization", "/organisation", "/chairman", "/member",
    "/finance-controller", "/examination-controller",
    "/public-information-officer", "/appellate-authority",
    "/web-information-manager", "/act-and-rule", "/rti", "/manual",
)

GOOD_URL_PARTS = (
    "/recruitment", "/notification", "/advertisement", "/vacancy",
    "/career", "/careers", "/job", "/jobs", "/advt", "/engagement",
    "/apprentice", "/apprenticeship", "/result", "/admit-card",
    "/answer-key", "/syllabus", "/exam", "/selection",
)


def _norm(text):
    text = normalize(str(text or "")).strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def _is_bad_title(text):
    if not text or len(text) < 6:
        return True

    if text in BAD_EXACT_TITLES:
        return True

    if any(p in text for p in BAD_TITLE_PHRASES):
        return True

    # Utility/download labels with no actual recruitment wording.
    if text.startswith(("download ", "view ", "click here", "step-")):
        return True

    return False


def _has_strong_good_word(text):
    return any(word in text for word in GOOD_WORDS)


def _has_only_weak_word(text):
    words = set(re.findall(r"[a-z0-9]+", text))
    return bool(words) and words.issubset(WEAK_ONLY_WORDS)


def allow_title(title, url=""):
    text = _norm(title)
    url_text = _norm(url)

    if _is_bad_title(text):
        return False

    # Strongly reject known portal/navigation URLs.
    if any(part in url_text for part in BAD_URL_PARTS):
        return False

    # A page whose title is only "Apply", "Registration", etc. is not a job.
    if _has_only_weak_word(text):
        return False

    if _has_strong_good_word(text):
        return True

    # Allow genuine Indian-language titles only when they are not
    # navigation/utility pages. They will still be checked by URL/content.
    if any(ord(c) > 127 for c in text):
        return bool(any(part in url_text for part in GOOD_URL_PARTS))

    return False


def clean_url(base, href):
    if not href:
        return None

    href = href.strip()
    if href.startswith(("#", "javascript:", "mailto:", "tel:")):
        return None

    url = urljoin(base, href)
    lower = url.lower()

    if any(part in lower for part in BAD_URL_PARTS):
        return None

    return url

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

        if not allow_title(title, url):
            continue

        # -----------------------------
        # Accept only useful URLs
        # -----------------------------
        lower_url = href.lower()

        VALID_URL = (

    "/recruitment" in lower_url
    or "/notification" in lower_url
    or "/advertisement" in lower_url
    or "/vacancy" in lower_url
    or "/career" in lower_url
    or "/job" in lower_url
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

        if not allow_title(title, url):
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
