"""
Intelligent Government Job Scraper
Version: 2.0
Author: Education Update Hub

Part 1
"""

import re
import time
import random
import logging
from urllib.parse import urljoin, urlparse

import requests
import os
import urllib3
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# -------------------------
# Logging
# -------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("SCRAPER")

# -------------------------
# Request Configuration
# -------------------------

REQUEST_TIMEOUT = int(os.getenv("EHU_REQUEST_TIMEOUT", "15"))
CONNECT_TIMEOUT = int(os.getenv("EHU_REQUEST_TIMEOUT", "15"))
READ_TIMEOUT = int(os.getenv("EHU_READ_TIMEOUT", "20"))
MAX_RETRIES = int(os.getenv("EHU_MAX_RETRIES", "1"))
SSL_FALLBACK = os.getenv("EHU_SSL_FALLBACK", "1").strip().lower() in {"1", "true", "yes", "on"}
if SSL_FALLBACK:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/138.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9"
}

# -------------------------
# Recruitment Keywords
# -------------------------

JOB_KEYWORDS = [

    "recruitment",
    "vacancy",
    "vacancies",
    "notification",
    "advertisement",
    "career",
    "careers",
    "job",
    "jobs",
    "employment",
    "apply online",
    "apply",
    "engagement",
    "selection",
    "walk in",
    "walk-in",
    "result",
    "admit card",
    "answer key",
    "exam"

]

# -------------------------
# Ignore Keywords
# -------------------------

IGNORE_KEYWORDS = [

    "facebook",
    "twitter",
    "youtube",
    "instagram",
    "linkedin",
    "privacy",
    "cookie",
    "copyright",
    "login",
    "logout",
    "contact",
    "feedback",
    "gallery",
    "photo",
    "video",
    "tender",
    "auction",
    "rti",
    "faq"

]

# -------------------------
# Supported File Types
# -------------------------

SUPPORTED_EXTENSIONS = [

    ".html",
    ".htm",
    ".php",
    ".aspx",
    ".pdf"

]

# -------------------------
# Retry Session
# -------------------------

def create_session():

    retry = Retry(
        total=MAX_RETRIES,
        connect=MAX_RETRIES,
        read=MAX_RETRIES,
        status=MAX_RETRIES,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["GET", "HEAD"]),
        raise_on_status=False,
        respect_retry_after_header=True,
    )

    adapter = HTTPAdapter(
        max_retries=retry,
        pool_connections=20,
        pool_maxsize=20,
    )

    session = requests.Session()
    session.headers.update(HEADERS)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


SESSION = create_session()

# -------------------------
# Download HTML
# -------------------------

def download(url):

    if not url:
        return None

    # Small jitter prevents all workers from hitting government servers together.
    time.sleep(random.uniform(0.2, 0.8))

    last_error = None

    for attempt in range(1, MAX_RETRIES + 2):
        try:
            response = SESSION.get(
                url,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
                allow_redirects=True,
            )
            response.raise_for_status()

            if not response.text:
                raise requests.RequestException("Empty response")

            return response.text

        except requests.exceptions.SSLError as e:
            last_error = e

            # Some Indian government sites expose incomplete/old certificate
            # chains. Keep normal verification first; only use the insecure
            # fallback for this specific SSL failure.
            if SSL_FALLBACK:
                try:
                    logger.warning(
                        "SSL certificate verification failed; retrying without "
                        "certificate verification: %s", url
                    )
                    response = SESSION.get(
                        url,
                        timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
                        allow_redirects=True,
                        verify=False,
                    )
                    response.raise_for_status()
                    if response.text:
                        return response.text
                except Exception as fallback_error:
                    last_error = fallback_error

        except (requests.exceptions.ConnectTimeout,
                requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError,
                requests.exceptions.RequestException) as e:
            last_error = e

        if attempt <= MAX_RETRIES:
            delay = min(8, 1.5 * attempt + random.uniform(0.2, 0.8))
            logger.warning(
                "Retrying %d/%d for %s after %s",
                attempt, MAX_RETRIES, url, type(last_error).__name__
            )
            time.sleep(delay)

    logger.error("%s -> %s", url, last_error)
    return None

# -------------------------
# HTML Parser
# -------------------------

def get_soup(url):

    html = download(url)

    if not html:
        return None

    return BeautifulSoup(
        html,
        "lxml"
    )

# -------------------------
# URL Cleaner
# -------------------------

def clean_url(base, href):

    if not href:
        return None

    href = href.strip()

    if href.startswith("#"):
        return None

    if href.startswith("javascript"):
        return None

    if href.startswith("mailto:"):
        return None

    if href.startswith("tel:"):
        return None

    return urljoin(base, href)
    # -------------------------
# URL Validation
# -------------------------

def is_supported_url(url):

    if not url:
        return False

    url = url.lower()

    if url.startswith("mailto:"):
        return False

    if url.startswith("tel:"):
        return False

    if url.startswith("javascript:"):
        return False

    return True


# -------------------------
# Internal Link Check
# -------------------------

def is_internal_link(base, url):

    try:

        return (
            urlparse(base).netloc ==
            urlparse(url).netloc
        )

    except Exception:

        return False


# -------------------------
# PDF Detection
# -------------------------

def is_pdf(url):

    if not url:

        return False

    return bool(re.search(r"\.pdf(?:[?#].*)?$", url, re.I))


# -------------------------
# Recruitment Keyword Match
# -------------------------

def has_job_keyword(text):

    if not text:

        return False

    text = text.lower()

    for keyword in JOB_KEYWORDS:

        if keyword in text:

            return True

    return False


# -------------------------
# Ignore Filter
# -------------------------

def should_ignore(text):

    if not text:

        return True

    text = text.lower()

    for keyword in IGNORE_KEYWORDS:

        if keyword in text:

            return True

    return False


# -------------------------
# Link Score
# -------------------------

def score_link(title, url):

    score = 0

    data = f"{title} {url}".lower()

    important = {

        "recruitment": 10,
        "vacancy": 10,
        "career": 8,
        "advertisement": 8,
        "notification": 8,
        "job": 6,
        "jobs": 6,
        "apply": 5,
        "engagement": 5,
        "result": 4,
        "admit": 4,
        "answer key": 4,
        "exam": 3,
        ".pdf": 3

    }

    for key, value in important.items():

        if key in data:

            score += value

    return score


# -------------------------
# Remove Duplicate Links
# -------------------------

def unique_links(items):

    seen = set()

    output = []

    for item in items:

        url = item["url"]

        if url in seen:

            continue

        seen.add(url)

        output.append(item)

    return output


# -------------------------
# Intelligent Link Extractor
# -------------------------

def extract_links(source_url):

    soup = get_soup(source_url)

    if soup is None:

        return []

    results = []

    for a in soup.find_all("a", href=True):

        href = clean_url(
            source_url,
            a["href"]
        )

        if not href:

            continue

        if not is_supported_url(href):

            continue

        title = a.get_text(" ", strip=True)

        if not title:

            title = href.split("/")[-1]

        if should_ignore(title):

            continue

        if should_ignore(href):

            continue

        if (
            has_job_keyword(title)
            or has_job_keyword(href)
            or is_pdf(href)
        ):

            results.append({

                "title": title.strip(),

                "url": href,

                "score": score_link(
                    title,
                    href
                ),

                "pdf": is_pdf(href),

                "internal": is_internal_link(
                    source_url,
                    href
                )

            })

    results = unique_links(results)

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return results
    # -------------------------
# Common Noise Words
# -------------------------

NOISE_WORDS = [
    "home",
    "click here",
    "read more",
    "more",
    "details",
    "view",
    "download",
    "new",
    "latest",
    "welcome",
    "homepage"
]

# -------------------------
# Title Cleaner
# -------------------------

def clean_title(title):

    if not title:
        return ""

    title = re.sub(r"\s+", " ", title)

    title = re.sub(r"\|.*", "", title)

    title = re.sub(r"\(.*?\)", "", title)

    title = title.replace("_", " ")

    title = title.replace("-", " ")

    title = title.strip()

    for word in NOISE_WORDS:

        pattern = rf"\b{re.escape(word)}\b"

        title = re.sub(
            pattern,
            "",
            title,
            flags=re.I
        )

    title = re.sub(r"\s+", " ", title)

    return title.strip()


# -------------------------
# Advertisement Number
# -------------------------

ADVERTISEMENT_REGEX = [

    r"\d+/\d{4}",

    r"advt\.?\s*no\.?\s*[\w/-]+",

    r"notification\s*no\.?\s*[\w/-]+",

    r"advertisement\s*no\.?\s*[\w/-]+"

]


def extract_advertisement(text):

    if not text:

        return None

    for pattern in ADVERTISEMENT_REGEX:

        match = re.search(
            pattern,
            text,
            flags=re.I
        )

        if match:

            return match.group()

    return None


# -------------------------
# Date Detection
# -------------------------

DATE_PATTERNS = [

    r"\d{2}[/-]\d{2}[/-]\d{4}",

    r"\d{1,2}\s+[A-Za-z]+\s+\d{4}",

    r"[A-Za-z]+\s+\d{1,2},\s*\d{4}"

]


def extract_dates(text):

    dates = []

    if not text:

        return dates

    for pattern in DATE_PATTERNS:

        dates.extend(

            re.findall(
                pattern,
                text,
                flags=re.I
            )

        )

    return list(dict.fromkeys(dates))


# -------------------------
# Fake Link Filter
# -------------------------

def is_fake_job(title):

    if not title:

        return True

    title = title.lower()

    bad = [

        "privacy",

        "contact",

        "feedback",

        "gallery",

        "photo",

        "video",

        "copyright",

        "terms",

        "policy",

        "tender",

        "auction",

        "news"

    ]

    for item in bad:

        if item in title:

            return True

    return False


# -------------------------
# Recruitment Detector
# -------------------------

def is_recruitment(title, url):

    if not title:

        return False

    if is_fake_job(title):

        return False

    title = clean_title(title)

    data = f"{title} {url}".lower()

    strong_keywords = [

        "recruitment",

        "vacancy",

        "notification",

        "advt",

        "advertisement",

        "apply",

        "online form",

        "engagement",

        "assistant",

        "officer",

        "clerk",

        "engineer",

        "professor",

        "scientist",

        "technician",

        "nurse",

        "faculty",

        "driver",

        "manager"

    ]

    for keyword in strong_keywords:

        if keyword in data:

            return True

    return False


# -------------------------
# Priority Score
# -------------------------

def priority(job):

    score = job.get("score", 0)

    title = job.get("title", "").lower()

    if "recruitment" in title:

        score += 20

    if "notification" in title:

        score += 15

    if "vacancy" in title:

        score += 15

    if job.get("pdf"):

        score += 10

    return score
    # =====================================================
# PART 4
# Source Specific Parsers
# =====================================================

SITE_RULES = {

    "upsc.gov.in": {
        "container": [
            ".view-content",
            ".region-content",
            "table",
            "main"
        ]
    },

    "ssc.gov.in": {
        "container": [
            ".view-content",
            ".region-content",
            "table"
        ]
    },

    "ibps.in": {
        "container": [
            ".entry-content",
            ".post",
            ".content-area"
        ]
    },

    "rrb": {
        "container": [
            ".content",
            "table",
            "main"
        ]
    },

    "ukpsc": {
        "container": [
            ".field-items",
            ".view-content",
            "table"
        ]
    },

    "uksssc": {
        "container": [
            ".field-items",
            ".view-content",
            "table"
        ]
    },

    "aiims": {
        "container": [
            ".field-item",
            ".content",
            "table"
        ]
    }

}


# -----------------------------------------------------

def get_site_rule(url):

    domain = urlparse(url).netloc.lower()

    for key, rule in SITE_RULES.items():

        if key in domain:

            return rule

    return None


# -----------------------------------------------------

def extract_from_container(base_url, soup):

    results = []

    rule = get_site_rule(base_url)

    if not rule:

        return extract_links(base_url)

    selectors = rule["container"]

    for selector in selectors:

        try:

            blocks = soup.select(selector)

            for block in blocks:

                for a in block.find_all("a", href=True):

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

                    if not is_recruitment(
                        title,
                        href
                    ):
                        continue

                    results.append({

                        "title": title,

                        "url": href,

                        "score": score_link(
                            title,
                            href
                        ),

                        "pdf": is_pdf(href),

                        "internal": is_internal_link(
                            base_url,
                            href
                        )

                    })

        except Exception:

            continue

    return unique_links(results)


# -----------------------------------------------------

def scrape_source(source):

    url = source.get("url", "")
    name = source.get("name", "Unknown")

    logger.info("Scraping %s", url)

    soup = get_soup(url)

    if soup is None:
        # Raise a controlled error so the multi-source coordinator can record
        # this source as failed instead of silently treating it as zero jobs.
        raise RuntimeError("source_unavailable")

    jobs = extract_from_container(url, soup)

    final = []
    for job in jobs:
        job["source"] = name
        job["category"] = source.get("category", "Latest Jobs")
        job["state"] = source.get("state", "India")
        job["priority"] = priority(job)
        final.append(job)

    final.sort(key=lambda x: x["priority"], reverse=True)
    logger.info("%s : %d candidate jobs", name, len(final))
    return final
    # =====================================================
# PART 5
# PDF & Recruitment Details Extractor
# =====================================================

import re

# -----------------------------------------------------
# Vacancy
# -----------------------------------------------------

VACANCY_PATTERNS = [

    r"(\d+)\s+posts?",
    r"(\d+)\s+vacancies",
    r"total\s+(\d+)",
    r"(\d+)\s+positions"

]

def extract_vacancy(text):

    if not text:
        return None

    text = text.lower()

    for pattern in VACANCY_PATTERNS:

        m = re.search(pattern, text)

        if m:
            return m.group(1)

    return None


# -----------------------------------------------------
# Last Date
# -----------------------------------------------------

LAST_DATE_PATTERNS = [

    r"last\s*date.*?(\d{2}[/-]\d{2}[/-]\d{4})",

    r"closing\s*date.*?(\d{2}[/-]\d{2}[/-]\d{4})",

    r"apply\s*before.*?(\d{2}[/-]\d{2}[/-]\d{4})"

]

def extract_last_date(text):

    if not text:
        return None

    text = text.lower()

    for pattern in LAST_DATE_PATTERNS:

        m = re.search(pattern, text)

        if m:
            return m.group(1)

    return None


# -----------------------------------------------------
# Salary
# -----------------------------------------------------

SALARY_PATTERNS = [

    r"₹\s?[\d,]+",

    r"rs\.?\s?[\d,]+",

    r"pay\s*level[- ]?\d+",

    r"level[- ]?\d+"

]

def extract_salary(text):

    if not text:
        return None

    for pattern in SALARY_PATTERNS:

        m = re.search(
            pattern,
            text,
            flags=re.I
        )

        if m:
            return m.group()

    return None


# -----------------------------------------------------
# Age Limit
# -----------------------------------------------------

AGE_PATTERNS = [

    r"(\d{2})\s*to\s*(\d{2})\s*years",

    r"minimum\s*(\d{2})",

    r"maximum\s*(\d{2})",

    r"age\s*limit.*?(\d{2})"

]

def extract_age(text):

    if not text:
        return None

    for pattern in AGE_PATTERNS:

        m = re.search(
            pattern,
            text,
            flags=re.I
        )

        if m:

            return m.group()

    return None


# -----------------------------------------------------
# Qualification
# -----------------------------------------------------

QUALIFICATION_KEYWORDS = [

    "10th",

    "12th",

    "iti",

    "diploma",

    "graduate",

    "graduation",

    "b.sc",

    "b.tech",

    "be",

    "b.e.",

    "m.sc",

    "mba",

    "ca",

    "llb",

    "phd",

    "nursing",

    "mbbs"

]

def extract_qualification(text):

    if not text:
        return None

    text = text.lower()

    found = []

    for q in QUALIFICATION_KEYWORDS:

        if q in text:

            found.append(q.upper())

    if found:

        return ", ".join(found)

    return None


# -----------------------------------------------------
# PDF Detector
# -----------------------------------------------------

def is_notification_pdf(url):

    if not url:
        return False

    url = url.lower()

    if not url.endswith(".pdf"):
        return False

    important = [

        "notification",

        "advertisement",

        "advt",

        "recruitment",

        "vacancy"

    ]

    for word in important:

        if word in url:

            return True

    return False


# -----------------------------------------------------
# Robust field extraction helpers
# -----------------------------------------------------

def _normalise_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _page_data(url):
    """Fetch a recruitment page once and return soup + visible text + table pairs.
    PDF content is deliberately NOT parsed or translated; PDFs are links only.
    """
    soup = get_soup(url)
    if soup is None:
        return None, "", {}

    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    text = _normalise_text(soup.get_text(" ", strip=True))
    pairs = {}

    for row in soup.find_all("tr"):
        cells = row.find_all(["th", "td"])
        if len(cells) >= 2:
            key = _normalise_text(cells[0].get_text(" ", strip=True)).lower().rstrip(":")
            value = _normalise_text(" ".join(c.get_text(" ", strip=True) for c in cells[1:]))
            if key and value and len(key) <= 120 and len(value) <= 600:
                pairs[key] = value

    # Also capture simple label/value blocks often used by government sites.
    labels = {
        "vacancy", "vacancies", "total vacancies", "total posts", "number of posts",
        "qualification", "educational qualification", "eligibility", "education",
        "salary", "pay scale", "pay level", "remuneration", "last date", "closing date",
        "application last date", "last date to apply"
    }
    for node in soup.find_all(["div", "p", "li", "span", "strong", "b"]):
        raw = _normalise_text(node.get_text(" ", strip=True))
        if ":" not in raw or len(raw) > 500:
            continue
        k, v = raw.split(":", 1)
        k = _normalise_text(k).lower()
        v = _normalise_text(v)
        if k in labels and v:
            pairs.setdefault(k, v)

    return soup, text, pairs


def _pair_value(pairs, keys):
    for key in keys:
        key = key.lower()
        for existing, value in pairs.items():
            if existing == key or existing.startswith(key):
                return value
    return None


def _extract_with_patterns(text, patterns):
    for pattern in patterns:
        m = re.search(pattern, text, re.I)
        if m:
            value = _normalise_text(m.group(1))
            if value:
                return value
    return None


def _valid_external_url(url, session=None):
    """Reject obvious bad/placeholder URLs. Do not make the scraper fail on a link check."""
    if not url:
        return False
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return False
    lowered = url.lower()
    if any(x in lowered for x in ("javascript:", "mailto:", "tel:", "#")):
        return False
    return True


def _find_best_pdf(soup, base_url):
    if soup is None:
        return None
    candidates = []
    for a in soup.find_all("a", href=True):
        href = clean_url(base_url, a.get("href"))
        if not _valid_external_url(href):
            continue
        label = _normalise_text(a.get_text(" ", strip=True)).lower()
        if ".pdf" not in href.lower() and "pdf" not in label:
            continue
        if is_notification_pdf(href) or any(k in label for k in ("notification", "advertisement", "advt", "recruitment")):
            candidates.append(href)
    return candidates[0] if candidates else None


def _find_best_apply(soup, base_url):
    if soup is None:
        return None
    candidates = []
    for a in soup.find_all("a", href=True):
        href = clean_url(base_url, a.get("href"))
        if not _valid_external_url(href):
            continue
        label = _normalise_text(a.get_text(" ", strip=True)).lower()
        if any(k in label for k in ("apply online", "apply now", "online application", "registration", "register", "application form")):
            candidates.append(href)
    return candidates[0] if candidates else None

# -----------------------------------------------------
# Complete Detail Extractor
# -----------------------------------------------------

def enrich_job(job, page_text):

    job["vacancy"] = extract_vacancy(page_text)

    job["last_date"] = extract_last_date(page_text)

    job["salary"] = extract_salary(page_text)

    job["age_limit"] = extract_age(page_text)

    job["qualification"] = extract_qualification(page_text)

    job["advertisement"] = extract_advertisement(page_text)

    job["dates_found"] = extract_dates(page_text)

    return job
    # =====================================================
# PART 6
# Intelligent Page Parser
# =====================================================

def get_page_text(url):

    soup = get_soup(url)

    if soup is None:
        return ""

    # Remove unwanted tags
    for tag in soup([
        "script",
        "style",
        "noscript",
        "svg",
        "footer",
        "header",
        "nav",
        "iframe"
    ]):
        tag.decompose()

    text = soup.get_text(" ", strip=True)

    text = re.sub(r"\s+", " ", text)

    return text


# -----------------------------------------------------

def extract_job_details(job):
    try:
        url = job.get("url", "")
        if not _valid_external_url(url):
            job["fetch_error"] = "invalid_url"
            return job

        soup, page_text, pairs = _page_data(url)
        if not page_text:
            job["fetch_error"] = "page_unavailable_or_404"
            logger.warning("Skipping unavailable page: %s", url)
            return job

        # Prefer structured/table values; use regex only as fallback.
        vacancy = _pair_value(pairs, ("vacancy", "vacancies", "total vacancies", "total posts", "number of posts"))
        if not vacancy:
            vacancy = extract_vacancy(page_text)

        last_date = _pair_value(pairs, ("last date", "closing date", "application last date", "last date to apply"))
        if not last_date:
            last_date = extract_last_date(page_text)

        salary = _pair_value(pairs, ("salary", "pay scale", "pay level", "remuneration"))
        if not salary:
            salary = extract_salary(page_text)

        qualification = _pair_value(pairs, ("qualification", "educational qualification", "eligibility", "education"))
        if not qualification:
            qualification = extract_qualification(page_text)

        job["vacancy"] = vacancy
        job["last_date"] = last_date
        job["salary"] = salary
        job["qualification"] = qualification
        job["advertisement"] = extract_advertisement(page_text)
        job["dates_found"] = extract_dates(page_text)
        job["content"] = page_text
        job["description"] = page_text[:500]

        # PDF is stored only as an official link. No PDF OCR/translation is done.
        job["notification_pdf"] = _find_best_pdf(soup, url) or job.get("notification_pdf", "")
        job["apply_link"] = _find_best_apply(soup, url) or job.get("apply_link", "")

        # Do not publish known-bad links as buttons.
        if not _valid_external_url(job.get("notification_pdf")):
            job["notification_pdf"] = ""
        if not _valid_external_url(job.get("apply_link")):
            job["apply_link"] = ""

        return job

    except Exception as e:
        logger.exception("Detail extraction failed for %s: %s", job.get("url", ""), e)
        job["fetch_error"] = str(e)
        return job


# -----------------------------------------------------

def enrich_all_jobs(jobs):

    final = []

    for job in jobs:

        final.append(

            extract_job_details(job)

        )

    return final


# -----------------------------------------------------
# Intelligent Category Detection
# -----------------------------------------------------

CATEGORY_RULES = {

    "Banking": [
        "bank",
        "ibps",
        "rbi",
        "nabard",
        "lic"
    ],

    "Railway": [
        "railway",
        "rrb",
        "rrc"
    ],

    "Defence": [
        "army",
        "navy",
        "air force",
        "drdo",
        "bsf",
        "crpf",
        "cisf",
        "itbp"
    ],

    "Teaching": [
        "teacher",
        "assistant professor",
        "lecturer",
        "faculty",
        "principal"
    ],

    "Medical": [
        "staff nurse",
        "nursing",
        "doctor",
        "pharmacist",
        "medical officer",
        "aiims"
    ],

    "Engineering": [
        "engineer",
        "civil",
        "mechanical",
        "electrical",
        "electronics"
    ]

}


def detect_category(title):

    title = title.lower()

    for category, words in CATEGORY_RULES.items():

        for word in words:

            if word in title:

                return category

    return "Government Job"


# -----------------------------------------------------

def enrich_category(jobs):

    for job in jobs:

        job["category"] = detect_category(

            job["title"]

        )

    return jobs
    # =====================================================
# PART 7
# Multi-thread Scraper & Sitemap/RSS Support
# =====================================================

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed
)

import xml.etree.ElementTree as ET


# -----------------------------------------------------
# RSS Parser
# -----------------------------------------------------

def parse_rss_feed(feed_url):

    items = []

    data = download(feed_url)

    if not data:
        return items

    try:

        root = ET.fromstring(data)

        for item in root.iter("item"):

            title = item.findtext("title", default="")

            link = item.findtext("link", default="")

            if not title or not link:
                continue

            items.append({

                "title": clean_title(title),

                "url": link,

                "score": score_link(title, link),

                "pdf": is_pdf(link),

                "internal": True

            })

    except Exception as e:

        logger.warning(
            f"RSS Parse Failed: {feed_url} -> {e}"
        )

    return unique_links(items)


# -----------------------------------------------------
# Sitemap Parser
# -----------------------------------------------------

def parse_sitemap(sitemap_url):

    urls = []

    data = download(sitemap_url)

    if not data:
        return urls

    try:

        root = ET.fromstring(data)

        for loc in root.iter():

            if loc.tag.endswith("loc"):

                if loc.text:

                    urls.append(loc.text.strip())

    except Exception as e:

        logger.warning(
            f"Sitemap Error: {e}"
        )

    return urls


# -----------------------------------------------------
# Robots.txt Sitemap Discovery
# -----------------------------------------------------

def discover_sitemaps(base_url):

    found = []

    robots = urljoin(
        base_url,
        "/robots.txt"
    )

    text = download(robots)

    if not text:
        return found

    for line in text.splitlines():

        if line.lower().startswith("sitemap:"):

            sitemap = line.split(
                ":",
                1
            )[1].strip()

            found.append(sitemap)

    return list(dict.fromkeys(found))


# -----------------------------------------------------
# Thread Worker
# -----------------------------------------------------

def scrape_worker(source):

    try:

        jobs = scrape_source(source)

        jobs = enrich_all_jobs(jobs)

        jobs = enrich_category(jobs)

        return jobs

    except Exception as e:

        logger.error(
            f"{source['name']} -> {e}"
        )

        return []


# -----------------------------------------------------
# Parallel Scraper
# -----------------------------------------------------

def scrape_sources_parallel(
    sources,
    workers=8
):

    all_jobs = []

    with ThreadPoolExecutor(
        max_workers=workers
    ) as executor:

        futures = {

            executor.submit(
                scrape_worker,
                source
            ): source

            for source in sources
        }

        for future in as_completed(futures):

            try:

                jobs = future.result()

                if jobs:

                    all_jobs.extend(jobs)

            except Exception as e:

                logger.error(e)

    return all_jobs


# -----------------------------------------------------
# Retry Queue
# -----------------------------------------------------

def retry_failed_sources(
    failed_sources,
    retries=2
):

    recovered = []

    for _ in range(retries):

        if not failed_sources:
            break

        remaining = []

        for source in failed_sources:

            try:

                jobs = scrape_worker(source)

                if jobs:

                    recovered.extend(jobs)

                else:

                    remaining.append(source)

            except Exception:

                remaining.append(source)

        failed_sources = remaining

    return recovered
    # =====================================================
# PART 8
# Data Cleaner, Duplicate Filter & Ranking Engine
# =====================================================

import hashlib


# -----------------------------------------------------
# Normalize Text
# -----------------------------------------------------

def normalize_text(text):

    if not text:
        return ""

    text = text.lower().strip()

    text = re.sub(r"\s+", " ", text)

    text = re.sub(r"[^a-z0-9 ]", "", text)

    return text


# -----------------------------------------------------
# Unique Job ID
# -----------------------------------------------------

def generate_job_id(job):

    key = "|".join([

        normalize_text(job.get("title", "")),

        normalize_text(job.get("url", "")),

        normalize_text(job.get("advertisement", ""))

    ])

    return hashlib.md5(
        key.encode("utf-8")
    ).hexdigest()


# -----------------------------------------------------
# Remove Duplicate Jobs
# -----------------------------------------------------

def remove_duplicate_jobs(jobs):

    unique = {}

    for job in jobs:

        job["job_id"] = generate_job_id(job)

        jid = job["job_id"]

        if jid not in unique:

            unique[jid] = job

            continue

        if job.get("priority", 0) > unique[jid].get("priority", 0):

            unique[jid] = job

    return list(unique.values())


# -----------------------------------------------------
# Department Detection
# -----------------------------------------------------

DEPARTMENT_RULES = {

    "Railway": [
        "railway",
        "rrb",
        "rrc"
    ],

    "Bank": [
        "bank",
        "ibps",
        "rbi",
        "nabard"
    ],

    "Police": [
        "police",
        "constable",
        "sub inspector"
    ],

    "Education": [
        "teacher",
        "lecturer",
        "professor",
        "faculty"
    ],

    "Medical": [
        "nurse",
        "doctor",
        "medical",
        "pharmacist"
    ],

    "Defence": [
        "army",
        "navy",
        "air force",
        "drdo"
    ]

}


def detect_department(title):

    title = title.lower()

    for dept, words in DEPARTMENT_RULES.items():

        for word in words:

            if word in title:

                return dept

    return "Government"


# -----------------------------------------------------
# Auto Tags
# -----------------------------------------------------

def generate_tags(job):

    tags = set()

    fields = [

        job.get("title", ""),

        job.get("category", ""),

        job.get("department", ""),

        job.get("state", "")

    ]

    for field in fields:

        for word in field.split():

            word = word.strip()

            if len(word) >= 3:

                tags.add(word)

    return sorted(tags)


# -----------------------------------------------------
# SEO Keywords
# -----------------------------------------------------

def generate_keywords(job):

    title = job.get("title", "")

    keywords = [

        title,

        f"{title} Recruitment",

        f"{title} Notification",

        f"{title} Apply Online",

        f"{title} Vacancy"

    ]

    return list(dict.fromkeys(keywords))


# -----------------------------------------------------
# Final Optimizer
# -----------------------------------------------------

def optimize_jobs(jobs):

    cleaned = []
    skipped_unavailable = 0

    for job in jobs:

        # A source URL returning 404/unavailable must never become a post.
        if job.get("fetch_error"):
            skipped_unavailable += 1
            continue

        job["title"] = clean_title(

            job.get("title", "")

        )

        job["department"] = detect_department(

            job["title"]

        )

        job["tags"] = generate_tags(job)

        job["keywords"] = generate_keywords(job)

        cleaned.append(job)

    cleaned = remove_duplicate_jobs(cleaned)

    cleaned.sort(

        key=lambda x: x.get(

            "priority",
            0

        ),

        reverse=True

    )

    logger.info("UNAVAILABLE URL FILTER | Removed=%d", skipped_unavailable)

    return cleaned
    # =====================================================
# PART 9
# Main Scraping Pipeline & Database Integration
# =====================================================

import json
import os
from datetime import datetime


# -----------------------------------------------------
# Load Sources
# -----------------------------------------------------

def load_sources(file_path="bot/sources.json"):

    if not os.path.exists(file_path):

        logger.error(f"Sources file not found: {file_path}")

        return []

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as f:

            sources = json.load(f)

        enabled = [

            s for s in sources

            if s.get("enabled", True)

        ]

        logger.info(

            f"Loaded {len(enabled)} sources"

        )

        return enabled

    except Exception as e:

        logger.error(e)

        return []


# -----------------------------------------------------
# Save JSON
# -----------------------------------------------------

def save_jobs_json(
    jobs,
    filename="database/jobs.json"
):

    os.makedirs(
        os.path.dirname(filename),
        exist_ok=True
    )

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(

            jobs,
            f,
            indent=2,
            ensure_ascii=False

        )

    logger.info(

        f"Saved {len(jobs)} jobs"

    )


# -----------------------------------------------------
# Load Existing Jobs
# -----------------------------------------------------

def load_existing_jobs(
    filename="database/jobs.json"
):

    if not os.path.exists(filename):

        return []

    try:

        with open(
            filename,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        return []


# -----------------------------------------------------
# Incremental Filter
# -----------------------------------------------------

def filter_new_jobs(
    new_jobs,
    old_jobs
):

    old_ids = {

        j.get("job_id")

        for j in old_jobs

    }

    result = []

    for job in new_jobs:

        if job["job_id"] not in old_ids:

            result.append(job)

    return result


# -----------------------------------------------------
# Timestamp
# -----------------------------------------------------

def add_timestamp(jobs):

    now = datetime.utcnow().isoformat()

    for job in jobs:

        job["scraped_at"] = now

    return jobs


# -----------------------------------------------------
# Logging Summary
# -----------------------------------------------------

def print_summary(jobs):

    logger.info("=" * 40)

    logger.info(

        f"Total Jobs : {len(jobs)}"

    )

    departments = {}

    for job in jobs:

        dept = job.get(

            "department",

            "Government"

        )

        departments.setdefault(

            dept,

            0

        )

        departments[dept] += 1

    for k, v in departments.items():

        logger.info(

            f"{k} : {v}"

        )

    logger.info("=" * 40)


# -----------------------------------------------------
# Main Pipeline
# -----------------------------------------------------

def run_pipeline():

    sources = load_sources()

    if not sources:

        return []

    jobs = scrape_sources_parallel(

        sources,

        workers=10

    )

    jobs = optimize_jobs(jobs)

    jobs = add_timestamp(jobs)

    old_jobs = load_existing_jobs()

    new_jobs = filter_new_jobs(

        jobs,

        old_jobs

    )

    save_jobs_json(jobs)

    print_summary(jobs)

    return new_jobs
    # =====================================================
# PART 10
# Final Execution Pipeline
# =====================================================

try:
    from duplicate_checker import remove_existing_jobs
except ImportError:
    remove_existing_jobs = None

try:
    from html_generator import generate_all
except ImportError:
    generate_all = None

try:
    from homepage_updater import update_homepage
except ImportError:
    update_homepage = None

try:
    from sitemap_generator import update_sitemap
except ImportError:
    update_sitemap = None


# -----------------------------------------------------
# Main Scraper
# -----------------------------------------------------

def scrape_all():

    logger.info("=" * 60)
    logger.info("Government Jobs Auto Scraper Started")
    logger.info("=" * 60)

    try:

        new_jobs = run_pipeline()

        if not new_jobs:

            logger.info("No new jobs found.")
            return []

        logger.info(f"New Jobs Found : {len(new_jobs)}")

        # Duplicate Checker
        if remove_existing_jobs:

            try:

                new_jobs = remove_existing_jobs(new_jobs)

                logger.info(
                    f"After Duplicate Filter : {len(new_jobs)}"
                )

            except Exception as e:

                logger.error(e)

        if not new_jobs:

            logger.info("Everything already exists.")
            return []

        # HTML Generation
        if generate_all:

            try:

                generate_all(new_jobs)

                logger.info("HTML Generated")

            except Exception as e:

                logger.error(e)

        # Homepage
        if update_homepage:
            try:
                update_homepage(new_jobs)
                logger.info("Homepage Updated")
            except Exception as e:
                logger.error(e)

        # Sitemap
        if update_sitemap:
            try:
                update_sitemap(new_jobs)
                logger.info("Sitemap Generated")
            except Exception as e:
                logger.error(e)

        logger.info("=" * 60)
        logger.info("Automation Completed Successfully")
        logger.info("=" * 60)
        return new_jobs

    except Exception as e:
        logger.exception(e)
        return []
# =====================================================
# PART 7
# Multi Source Scraper
# =====================================================

from concurrent.futures import ThreadPoolExecutor, as_completed


def scrape_all_sources(sources, workers=8):

    results = []
    failed_sources = []

    if not sources:
        return results, failed_sources

    logger.info("Scraping %d sources...", len(sources))

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(scrape_source, source): source
            for source in sources
        }

        for future in as_completed(futures):
            source = futures[future]
            name = source.get("name", "Unknown")

            try:
                jobs = future.result()
                if jobs:
                    results.extend(jobs)
                logger.info(
                    "%s : %d jobs",
                    name,
                    len(jobs or [])
                )

            except Exception as e:
                failed_sources.append({
                    "name": name,
                    "url": source.get("url", ""),
                    "error": str(e),
                })
                logger.warning(
                    "Source unavailable | %s | %s | %s",
                    name,
                    source.get("url", ""),
                    e,
                )

    # Retry only failed sources. Successful sources are never re-hit.
    if failed_sources:
        logger.info(
            "Retry Queue : %d failed source(s)",
            len(failed_sources)
        )
        retry_sources = []
        for item in failed_sources:
            retry_sources.append({
                "name": item["name"],
                "url": item["url"],
                "category": next(
                    (s.get("category", "Latest Jobs") for s in sources
                     if s.get("name") == item["name"] and s.get("url") == item["url"]),
                    "Latest Jobs",
                ),
                "state": next(
                    (s.get("state", "India") for s in sources
                     if s.get("name") == item["name"] and s.get("url") == item["url"]),
                    "India",
                ),
            })

        recovered = retry_failed_sources(retry_sources, retries=1)
        if recovered:
            results.extend(recovered)
            recovered_urls = {j.get("url") for j in recovered}
            failed_sources = [
                f for f in failed_sources
                if f.get("url") not in recovered_urls
            ]

    results.sort(key=lambda x: x.get("priority", 0), reverse=True)

    logger.info(
        "SCRAPE SUMMARY | Successful Sources=%d | Jobs=%d | Unavailable Sources=%d",
        len(sources) - len(failed_sources),
        len(results),
        len(failed_sources),
    )

    return results, failed_sources

# -----------------------------------------------------
# Standalone Execution
# -----------------------------------------------------

if __name__ == "__main__":

    scrape_all()
