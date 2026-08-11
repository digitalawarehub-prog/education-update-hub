"""
=========================================================
Education Update Hub
Production Scraper v4
Phase 2 - Part 1
=========================================================
"""

import json
import logging
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin, urlparse
from database import load_jobs, save_jobs
from optimizer import run_optimizer
from html_generator import generate_all
import homepage
from sitemap_generator import generate_sitemap
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from downloader import download
from filters import allow_job
from optimizer import optimize_jobs
from utils.logger import logger
from adapters import get_adapter
from search_index import run as generate_search_index
BASE_URL = "https://educationupdatehub.in"
# ==========================================================
# Paths
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent

DATABASE_DIR = BASE_DIR / "database"
GENERATED_DIR = BASE_DIR / "generated"

DATABASE_DIR.mkdir(
    parents=True,
    exist_ok=True
)

GENERATED_DIR.mkdir(
    parents=True,
    exist_ok=True
)

DATABASE_FILE = DATABASE_DIR / "jobs.json"

# ==========================================================
# Network Configuration
# ==========================================================

REQUEST_TIMEOUT = 6
MAX_RETRIES = 0

HEADERS = {

    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/138.0 Safari/537.36"
    ),

    "Accept": (
        "text/html,"
        "application/xhtml+xml,"
        "application/xml;q=0.9,"
        "*/*;q=0.8"
    ),

    "Accept-Language": "en-IN,en;q=0.9",

    "Connection": "keep-alive"
}


# ==========================================================
# HTTP Session
# ==========================================================

def create_session():

    retry = Retry(
        total=0,
        connect=0,
        read=0,
        backoff_factor=0,
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

# ==========================================================
# Helper
# ==========================================================

def random_delay():

    time.sleep(

        random.uniform(

            0.5,

            1.5

        )

    )


logger.info(
    "Production Scraper Initialized"
)
# ==========================================================
# Download HTML
# ==========================================================

def download_page(url):

    if not url:
        return None

    try:

        random_delay()

        response = SESSION.get(
            url,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
            verify=False
        )

        response.raise_for_status()

        # Skip PDF and non-HTML content
        content_type = response.headers.get("Content-Type", "").lower()

        if "application/pdf" in content_type:
            logger.info("Skipped PDF : %s", url)
            return None

        if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
            logger.info("Skipped Non HTML : %s", url)
            return None

        html = response.text

        if not html.strip():
            logger.warning(
                "Empty Response : %s",
                url
            )
            return None

        if html.lstrip().startswith("%PDF"):
            logger.info("PDF Content : %s", url)
            return None

        logger.info(
            "Downloaded : %s",
            url
        )

        return html

    except requests.exceptions.Timeout:

        logger.error(
            "Timeout : %s",
            url
        )

    except requests.exceptions.SSLError:

        logger.error(
            "SSL Error : %s",
            url
        )

    except requests.exceptions.ConnectionError:

        logger.error(
            "Connection Error : %s",
            url
        )

    except requests.exceptions.HTTPError as e:

        logger.error(
            "HTTP %s : %s",
            e.response.status_code,
            url
        )

    except Exception as e:

        logger.exception(
            "Download Failed : %s | %s",
            url,
            e
        )

    return None

# ==========================================================
# BeautifulSoup Parser
# ==========================================================

def get_soup(url):

    html = download_page(url)

    if not html:
        return None

    if isinstance(html, bytes):
        if html.startswith(b"%PDF"):
            return None
        html = html.decode("utf-8", errors="ignore")

    if isinstance(html, str):
        if html.lstrip().startswith("%PDF"):
            return None

    try:
        return BeautifulSoup(
            html,
            "html.parser"
        )

    except Exception as e:
        logger.exception(
            "Soup Error : %s | %s",
            url,
            e
        )
        return None

# ==========================================================
# Validate HTML
# ==========================================================

def is_valid_html(soup):

    if soup is None:

        return False

    if soup.find("html") is None:

        return False

    if soup.find("body") is None:

        return False

    return True


# ==========================================================
# Safe Soup Loader
# ==========================================================

def load_page(url):

    soup = get_soup(url)

    if not is_valid_html(soup):

        logger.warning(
            "Invalid HTML : %s",
            url
        )

        return None

    return soup


logger.info(
    "Downloader Ready"
)
# ==========================================================
# URL Cleaner
# ==========================================================

def clean_url(url):

    if not url:
        return ""

    url = url.strip()

    url = url.split("#")[0]

    return url.rstrip("/")


# ==========================================================
# Title Cleaner
# ==========================================================

def clean_title(title):

    if not title:
        return ""

    title = re.sub(r"\s+", " ", title)

    title = re.sub(r"[|]+", " ", title)

    return title.strip()


# ==========================================================
# Ignore Links
# ==========================================================

IGNORE_KEYWORDS = {

    "login",
    "register",
    "privacy",
    "contact",
    "about",
    "feedback",
    "copyright",
    "sitemap",
    "faq",
    "facebook",
    "twitter",
    "instagram",
    "youtube"
}


# ==========================================================
# Score Link
# ==========================================================

def score_link(title, url):

    score = 0

    text = f"{title} {url}".lower()

    job_keywords = [

        "recruitment",
        "vacancy",
        "notification",
        "apply",
        "job",
        "result",
        "admit",
        "answer key",
        "exam"

    ]

    for word in job_keywords:

        if word in text:

            score += 10

    if url.endswith(".pdf"):

        score += 5

    return score


# ==========================================================
# Extract Links
# ==========================================================

def extract_links(soup, base_url):

    jobs = []

    visited = set()

    for link in soup.find_all("a", href=True):

        href = clean_url(
            urljoin(base_url, link["href"])
        )

        title = clean_title(
            link.get_text(" ", strip=True)
        )

        if not href or not title:
            continue

        # Skip invalid links
        if href.startswith("javascript:") or href == "#":
            continue

        text = f"{title} {href}".lower()

        if any(word in text for word in IGNORE_KEYWORDS):
            continue

        if not allow_job(title):
            continue

        if href in visited:
            continue

        visited.add(href)

        jobs.append({
            "title": title,
            "url": href,
            "score": score_link(title, href)
        })

    jobs.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    logger.info(
        "Links Extracted : %d",
        len(jobs)
    )

    return jobs


logger.info("Smart Parser Ready")


# ==========================================================
# Scrape Single Source
# ==========================================================

def scrape_source(source):

    name = source.get("name", "Unknown")

    logger.info(
        "Scraping Source : %s",
        name
    )

    try:

        adapter = get_adapter(source)

        jobs = adapter.scrape(source)

        if jobs is None:
            jobs = []

        logger.info(
            "%s : %d Jobs",
            name,
            len(jobs)
        )

        return jobs

    except Exception:

        logger.exception(
            "Scraping Failed : %s",
            name
        )

        return []

# ==========================================================
# Scrape Multiple Sources
# ==========================================================

def scrape_sources(sources):

    all_jobs = []

    for source in sources:

        jobs = scrape_source(source)

        all_jobs.extend(jobs)

    logger.info(
        "Total Jobs Collected : %d",
        len(all_jobs)
    )

    return all_jobs


# ==========================================================
# Validate Adapter Output
# ==========================================================

def validate_adapter_jobs(jobs):

    valid = []

    for job in jobs:

        if not isinstance(job, dict):
            continue

        if not job.get("title"):
            continue

        if not job.get("url"):
            continue

        valid.append(job)

    return valid


logger.info("Adapter Integration Ready")
# ==========================================================
# Multi-thread Scraping Engine
# ==========================================================

MAX_WORKERS = 5


def scrape_all_sources(sources):

    all_jobs = []
    failed_sources = []

    logger.info(
        "Starting Parallel Scraping (%d Sources)",
        len(sources)
    )

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        future_map = {

            executor.submit(
                scrape_source,
                source
            ): source

            for source in sources

        }

        for future in as_completed(future_map):

            source = future_map[future]

            try:

                jobs = future.result()

                jobs = validate_adapter_jobs(jobs)

                all_jobs.extend(jobs)

            except Exception:

                logger.exception(

                    "Source Failed : %s",

                    source.get("name")

                )

                failed_sources.append(source)

    logger.info(

        "Parallel Scraping Completed"

    )

    logger.info(

        "Collected Jobs : %d",

        len(all_jobs)

    )

    return all_jobs, failed_sources


# ==========================================================
# Retry Failed Sources
# ==========================================================

def retry_failed_sources(failed_sources):

    if not failed_sources:
        return []

    # A failed source is already isolated by scrape_source().
    # Do not retry every dead/blocked source and delay the whole workflow.
    logger.info("Skipping retry for %d failed sources", len(failed_sources))
    return []

    recovered = []

    for source in failed_sources:

        try:

            jobs = scrape_source(source)

            jobs = validate_adapter_jobs(jobs)

            recovered.extend(jobs)

        except Exception:

            logger.exception(

                "Retry Failed : %s",

                source.get("name")

            )

    logger.info(

        "Recovered Jobs : %d",

        len(recovered)

    )

    return recovered


# ==========================================================
# Complete Scraping Pipeline
# ==========================================================

def run_scraping(sources):

    jobs, failed = scrape_all_sources(sources)

    recovered = retry_failed_sources(failed)

    jobs.extend(recovered)

    logger.info(

        "Final Jobs : %d",

        len(jobs)

    )

    return jobs


logger.info(
    "Multi-thread Scraper Ready"
)
# ==========================================================
# Job Detail Patterns
# ==========================================================

PATTERNS = {

    "vacancy": r"(\d+)\s+(?:vacancies|vacancy|posts?)",

    "last_date": r"(?:last date|closing date|apply last date)[^\n:]*[:\-]?\s*([^\n]+)",

    "salary": r"(?:salary|pay scale|pay level)[^\n:]*[:\-]?\s*([^\n]+)",

    "qualification": r"(?:qualification|eligibility)[^\n:]*[:\-]?\s*([^\n]+)"
}


# ==========================================================
# Extract Using Regex
# ==========================================================

def extract_pattern(text, pattern):

    if not text:

        return ""

    match = re.search(

        pattern,

        text,

        re.IGNORECASE

    )

    if match:

        return match.group(1).strip()

    return ""


# ==========================================================
# Get Page Text
# ==========================================================

def get_page_text(url):

    soup = load_page(url)

    if soup is None:

        return ""

    return soup.get_text(

        " ",

        strip=True

    )


# ==========================================================
# Find Notification PDF
# ==========================================================

def find_notification_pdf(soup, base_url):

    if soup is None:

        return ""

    for link in soup.find_all("a", href=True):

        href = urljoin(

            base_url,

            link["href"]

        )

        if href.lower().endswith(".pdf"):

            return href

    return ""


# ==========================================================
# Find Apply Link
# ==========================================================

def find_apply_link(soup, base_url):

    if soup is None:

        return ""

    keywords = [

        "apply",

        "registration",

        "online application"

    ]

    for link in soup.find_all("a", href=True):

        text = link.get_text(

            " ",

            strip=True

        ).lower()

        if any(

            key in text

            for key in keywords

        ):

            return urljoin(

                base_url,

                link["href"]

            )

    return ""


# ==========================================================
# Enrich Single Job
# ==========================================================

def enrich_job(job):

    url = job.get("url")

    if not url:
        return job

    # PDF URL है तो HTML की तरह parse मत करो
    if url.lower().endswith(".pdf"):
        job["description"] = "Official recruitment notification is available in PDF."
        job["content"] = ""
        job["notification_pdf"] = url
        job["apply_link"] = ""
        return job

    soup = load_page(url)

    if soup is None:
        return job

    text = soup.get_text(
        " ",
        strip=True
    )

    job["description"] = text[:300]
    job["content"] = ""

    job["vacancy"] = extract_pattern(text, PATTERNS["vacancy"])
    job["last_date"] = extract_pattern(text, PATTERNS["last_date"])
    job["salary"] = extract_pattern(text, PATTERNS["salary"])
    job["qualification"] = extract_pattern(text, PATTERNS["qualification"])
    job["vacancy"] = job["vacancy"] or "Not Mentioned"
    job["salary"] = job["salary"] or "As Per Rules"
    job["qualification"] = job["qualification"] or "Check Official Notification"
    job["last_date"] = job["last_date"] or "Check Notification"
    job["notification_pdf"] = find_notification_pdf(
        soup,
        url
    )

    job["apply_link"] = find_apply_link(
        soup,
        url
    )

    return job


# ==========================================================
# Enrich All Jobs
# ==========================================================

def enrich_jobs(jobs):

    enriched = []

    for job in jobs:

        try:

            enriched.append(

                enrich_job(job)

            )

        except Exception:

            logger.exception(

                "Enrichment Failed : %s",

                job.get("title")

            )

            enriched.append(job)

    logger.info(

        "Job Enrichment Completed : %d",

        len(enriched)

    )

    return enriched


logger.info(
    "Job Detail Extractor Ready"
)
# ==========================================================
# Load Sources
# ==========================================================

def load_sources():

    source_file = BASE_DIR / "sources.json"

    if not source_file.exists():

        logger.error(
            "sources.json not found"
        )

        return []

    with open(

        source_file,

        "r",

        encoding="utf-8"

    ) as f:

        sources = json.load(f)

    logger.info(

        "Loaded %d Sources",

        len(sources)

    )

    return sources


# ==========================================================
# Complete Pipeline
# ==========================================================

def run_pipeline():

    logger.info("=" * 60)
    logger.info("Production Pipeline Started")
    logger.info("=" * 60)

    sources = load_sources()

    if not sources:

        logger.warning(
            "No Sources Available"
        )

        return []

    # Step 1
    jobs = run_scraping(sources)

    # Step 2
    jobs = optimize_jobs(jobs)

    # Step 3
    old_jobs = load_jobs()

    result = run_optimizer(
        old_jobs,
        jobs
    )

    merged_jobs = result["jobs"]

    print("=" * 60)
    print("TOTAL JOBS :", len(merged_jobs))
    print("=" * 60)

    if len(merged_jobs) == 0:

        raise Exception(
            "No jobs found. merged_jobs is empty."
        )

    import json

    print("\n===== FIRST 3 JOBS =====")
    print(
        json.dumps(
            merged_jobs[:3],
            indent=4,
            ensure_ascii=False
        )
    )
    print("========================\n")

    # Step 4
    save_jobs(
        merged_jobs
    )

    # Step 5
    generate_all(
        merged_jobs
    )

    # Step 6
    logger.info(
        "Generating Search Index..."
    )

    generate_search_index()

    # Step 7
    homepage.run(
        merged_jobs
    )

    # Step 8
    generate_sitemap()

    logger.info("")
    logger.info(
        "Pipeline Finished Successfully"
    )

    logger.info(
        "Total Jobs : %d",
        len(merged_jobs)
    )

    return merged_jobs

        # ==========================================================
# Post Processing
# ==========================================================

def post_processing(jobs):

    logger.info("=" * 60)
    logger.info("Starting Post Processing")
    logger.info("=" * 60)

    # HTML Generation
    try:

        generate_all(
            jobs
        )

        logger.info(
            "HTML Generation Completed"
        )

    except Exception:

        logger.exception(
            "HTML Generation Failed"
        )

    # Homepage Update
    try:

        homepage.run(
            jobs
        )

        logger.info(
            "Homepage Updated"
        )

    except Exception:

        logger.exception(
            "Homepage Update Failed"
        )

    # Sitemap Update
    try:

        generate_sitemap()

        logger.info(
            "Sitemap Generated"
        )

    except Exception:

        logger.exception(
            "Sitemap Generation Failed"
        )

    logger.info("=" * 60)
    logger.info("Post Processing Completed")
    logger.info("=" * 60)

# ==========================================================
# Execution Report
# ==========================================================

def execution_report(jobs):

    report = {

        "timestamp": time.strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        "total_jobs": len(jobs),

        "status": "success"

    }

    report_file = GENERATED_DIR / "execution_report.json"

    with open(

        report_file,

        "w",

        encoding="utf-8"

    ) as f:

        json.dump(

            report,

            f,

            indent=4,

            ensure_ascii=False

        )

    logger.info(
        "Execution Report Saved"
    )


# ==========================================================
# Production Runner
# ==========================================================

def production_runner():

    logger.info("=" * 60)
    logger.info("Education Update Hub Production Runner")
    logger.info("=" * 60)

    jobs = run_pipeline()

    if not jobs:

        logger.warning(
            "No Jobs Generated"
        )

        return

    post_processing(jobs)

    execution_report(jobs)

    logger.info("=" * 60)
    logger.info("Production Completed Successfully")
    logger.info("=" * 60)


# ==========================================================
# Final Entry Point
# ==========================================================

if __name__ == "__main__":

    try:

        production_runner()

    except KeyboardInterrupt:

        logger.warning(
            "Execution Interrupted"
        )

    except Exception:

        logger.exception(
            "Unexpected Error"
        )
