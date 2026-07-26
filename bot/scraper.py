"""
=========================================================
Education Update Hub
Production Scraper v4.0
=========================================================
"""

import json
import random
import time
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from adapters import ADAPTERS
from utils.logger import logger

# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_DIR = BASE_DIR / "database"
GENERATED_DIR = BASE_DIR / "generated"

DATABASE_DIR.mkdir(exist_ok=True)
GENERATED_DIR.mkdir(exist_ok=True)

DATABASE_FILE = DATABASE_DIR / "jobs.json"
SOURCE_FILE = BASE_DIR / "bot" / "sources.json"

# =========================================================
# CONFIG
# =========================================================

REQUEST_TIMEOUT = 30

MAX_RETRIES = 3

MAX_WORKERS = 10

HEADERS = {

    "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0 Safari/537.36",

    "Accept-Language":
        "en-IN,en;q=0.9"

}

logger.info("Production Scraper v4 Loaded")

# =========================================================
# HTTP SESSION
# =========================================================

def create_session():

    retry = Retry(

        total=MAX_RETRIES,

        connect=MAX_RETRIES,

        read=MAX_RETRIES,

        backoff_factor=2,

        status_forcelist=[
            429,
            500,
            502,
            503,
            504
        ]

    )

    adapter = HTTPAdapter(
        max_retries=retry
    )

    session = requests.Session()

    session.headers.update(
        HEADERS
    )

    session.mount(
        "https://",
        adapter
    )

    session.mount(
        "http://",
        adapter
    )

    return session


SESSION = create_session()

# =========================================================
# COMMON HELPERS
# =========================================================

def random_delay():

    time.sleep(

        random.uniform(
            0.5,
            1.5
        )

    )
    # =========================================================
# DATABASE
# =========================================================

def load_database():

    if not DATABASE_FILE.exists():
        return []

    try:

        with open(
            DATABASE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception as e:

        logger.error(e)

        return []


def save_database(data):

    try:

        DATABASE_DIR.mkdir(exist_ok=True)

        with open(
            DATABASE_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2
            )

    except Exception as e:

        logger.error(e)


# =========================================================
# SOURCES
# =========================================================

def load_sources():

    if not SOURCE_FILE.exists():

        logger.error("sources.json not found")

        return []

    try:

        with open(
            SOURCE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            sources = json.load(f)

    except Exception as e:

        logger.error(e)

        return []

    enabled = []

    for source in sources:

        if source.get(
            "enabled",
            True
        ):

            enabled.append(source)

    logger.info(

        "Loaded %d Sources",

        len(enabled)

    )

    return enabled


# =========================================================
# DOWNLOADER
# =========================================================

def download(url):

    random_delay()

    try:

        response = SESSION.get(

            url,

            timeout=REQUEST_TIMEOUT,

            allow_redirects=True,

            verify=False

        )

        response.raise_for_status()

        return response.text

    except Exception as e:

        logger.error(

            "Download Failed : %s",

            url

        )

        logger.error(e)

        return None


# =========================================================
# HTML PARSER
# =========================================================

from bs4 import BeautifulSoup

def get_soup(url):

    html = download(url)

    if not html:

        return None

    return BeautifulSoup(

        html,

        "lxml"

    )


# =========================================================
# URL HELPERS
# =========================================================

from urllib.parse import urljoin


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

    return urljoin(

        base,

        href

    )


# =========================================================
# TEXT HELPERS
# =========================================================

import re


def normalize(text):

    if not text:

        return ""

    return re.sub(

        r"\s+",

        " ",

        str(text)

    ).strip()


def clean_title(title):

    if not title:

        return ""

    title = normalize(title)

    title = re.sub(

        r"\|.*$",

        "",

        title

    )

    title = re.sub(

        r"\(.*?\)",

        "",

        title

    )

    title = title.replace("_", " ")

    title = title.replace("-", " ")

    title = normalize(title)

    return title
    # =========================================================
# SMART FILTERS
# =========================================================

JOB_KEYWORDS = {

    "recruitment",
    "vacancy",
    "vacancies",
    "notification",
    "advertisement",
    "career",
    "job",
    "jobs",
    "apply",
    "registration",
    "online form",
    "walk in",
    "result",
    "admit card",
    "answer key",
    "syllabus",

    "भर्ती",
    "विज्ञापन",
    "अधिसूचना",
    "आवेदन",
    "ऑनलाइन आवेदन",
    "प्रवेश पत्र",
    "उत्तर कुंजी",
    "पाठ्यक्रम"
}

IGNORE_WORDS = {

    "privacy",
    "cookie",
    "contact",
    "feedback",
    "gallery",
    "facebook",
    "twitter",
    "instagram",
    "youtube",
    "login",
    "logout",
    "tender",
    "auction",
    "rti",
    "accessibility",
    "website policy",
    "sitemap"
}


# =========================================================
# CHECK FUNCTIONS
# =========================================================

def has_job_keyword(text):

    if not text:
        return False

    text = text.lower()

    return any(
        keyword in text
        for keyword in JOB_KEYWORDS
    )


def should_ignore(text):

    if not text:
        return True

    text = text.lower()

    return any(
        word in text
        for word in IGNORE_WORDS
    )


def is_pdf(url):

    if not url:
        return False

    return url.lower().endswith(".pdf")


# =========================================================
# LINK SCORE
# =========================================================

def score_link(title, url):

    data = f"{title} {url}".lower()

    score = 0

    SCORE = {

        "recruitment":15,
        "vacancy":15,
        "notification":12,
        "advertisement":10,
        "career":10,
        "apply":8,
        "result":7,
        "admit":7,
        "answer key":6,
        "syllabus":5,
        ".pdf":5
    }

    for key, value in SCORE.items():

        if key in data:

            score += value

    return score


# =========================================================
# SMART SELECTORS
# =========================================================

SMART_SELECTORS = [

    ".notification",

    ".notifications",

    ".notice",

    ".latest-news",

    ".latest-updates",

    ".recruitment",

    ".content",

    ".entry-content",

    "#content",

    "#main-content"
]


# =========================================================
# LINK EXTRACTOR
# =========================================================

def extract_links(source):

    soup = get_soup(
        source["url"]
    )

    if soup is None:

        return []

    containers = []

    for selector in SMART_SELECTORS:

        containers.extend(

            soup.select(selector)

        )

    if not containers:

        containers = [soup]

    links = []

    seen = set()

    for container in containers:

        for a in container.find_all(

            "a",

            href=True

        ):

            href = clean_url(

                source["url"],

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

            if should_ignore(title):

                continue

            if should_ignore(href):

                continue

            important = (

                has_job_keyword(title)

                or

                ".pdf" in href.lower()

                or

                "notification" in href.lower()

                or

                "recruitment" in href.lower()

                or

                "career" in href.lower()

            )

            if not important:

                continue

            if href in seen:

                continue

            seen.add(href)

            links.append({

                "title": title,

                "url": href,

                "pdf": is_pdf(href),

                "score": score_link(

                    title,

                    href

                )

            })

    links.sort(

        key=lambda x:x["score"],

        reverse=True

    )

    logger.info(

        "%s : %d links",

        source["name"],

        len(links)

    )

    return links
    # =========================================================
# CATEGORY DETECTION
# =========================================================

CATEGORY_RULES = {

    "Bank Jobs": [
        "bank",
        "ibps",
        "rbi",
        "nabard",
        "lic"
    ],

    "Railway Jobs": [
        "railway",
        "rrb",
        "rrc"
    ],

    "Teaching Jobs": [
        "teacher",
        "faculty",
        "lecturer",
        "professor"
    ],

    "Defence Jobs": [
        "army",
        "navy",
        "air force",
        "drdo",
        "crpf",
        "cisf",
        "itbp",
        "bsf"
    ],

    "Medical Jobs": [
        "medical",
        "doctor",
        "nurse",
        "pharmacist",
        "aiims"
    ]

}


def detect_category(title):

    title = title.lower()

    for category, words in CATEGORY_RULES.items():

        if any(word in title for word in words):

            return category

    return "Latest Jobs"


# =========================================================
# ADAPTER SCRAPER
# =========================================================

def scrape_source(source):

    adapter_name = source.get(
        "adapter",
        "generic"
    ).lower()

    adapter = ADAPTERS.get(
        adapter_name,
        ADAPTERS["generic"]
    )

    logger.info(

        "Using %s Adapter",

        adapter.name

    )

    jobs = adapter.scrape(source)

    output = []

    for job in jobs:

        job["source"] = source.get(
            "name",
            "Unknown"
        )

        job["state"] = source.get(
            "state",
            "India"
        )

        job["category"] = source.get(
            "category",
            detect_category(
                job["title"]
            )
        )

        output.append(job)

    logger.info(

        "%s : %d Jobs",

        source["name"],

        len(output)

    )

    return output


# =========================================================
# MULTI THREAD SCRAPER
# =========================================================

from concurrent.futures import (

    ThreadPoolExecutor,

    as_completed

)


def scrape_all_sources(

    sources,

    workers=10

):

    logger.info(

        "Total Sources : %d",

        len(sources)

    )

    jobs = []

    with ThreadPoolExecutor(

        max_workers=workers

    ) as executor:

        future_map = {

            executor.submit(

                scrape_source,

                source

            ): source

            for source in sources

        }

        for future in as_completed(

            future_map

        ):

            source = future_map[future]

            try:

                data = future.result()

                if data:

                    jobs.extend(data)

            except Exception as e:

                logger.error(

                    "%s Failed",

                    source["name"]

                )

                logger.error(e)

    logger.info(

        "Collected Jobs : %d",

        len(jobs)

    )

    return jobs


# =========================================================
# FAILED SOURCE RETRY
# =========================================================

def retry_failed_sources(

    failed_sources,

    retries=2

):

    recovered = []

    for attempt in range(retries):

        if not failed_sources:

            break

        logger.info(

            "Retry Attempt %d",

            attempt + 1

        )

        remaining = []

        for source in failed_sources:

            try:

                jobs = scrape_source(source)

                if jobs:

                    recovered.extend(jobs)

                else:

                    remaining.append(source)

            except Exception:

                remaining.append(source)

        failed_sources = remaining

    return recovered
