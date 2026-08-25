"""
=========================================================
Education Update Hub
Production Scraper v3.0
Part 1
=========================================================
"""

import os
import re
import json
import time
import random
import logging
import multiprocessing as mp
from optimizer import optimize_jobs
from pathlib import Path
from urllib.parse import urljoin, urlparse
from adapters import ADAPTERS
from utils.logger import logger
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from filters import allow_job
from downloader import download
# =========================================================
# CONFIG
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_DIR = BASE_DIR / "database"
GENERATED_DIR = BASE_DIR / "generated"

DATABASE_DIR.mkdir(exist_ok=True)
GENERATED_DIR.mkdir(exist_ok=True)

DATABASE_FILE = DATABASE_DIR / "jobs.json"

REQUEST_TIMEOUT = int(os.getenv("EHU_REQUEST_TIMEOUT", "8"))
MAX_RETRIES = int(os.getenv("EHU_MAX_RETRIES", "0"))
SOURCE_BATCH_SIZE = min(24, max(1, int(os.getenv("EHU_SOURCE_BATCH_SIZE", "24"))))
SOURCE_WORKERS = min(4, max(1, int(os.getenv("EHU_SOURCE_WORKERS", "4"))))
SOURCE_ROTATION_FILE = DATABASE_DIR / "source_rotation.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("EducationUpdateHub")

# =========================================================
# HTTP SESSION
# =========================================================

def create_session():

    retry = Retry(
        total=MAX_RETRIES,
        connect=MAX_RETRIES,
        read=MAX_RETRIES,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )

    adapter = HTTPAdapter(max_retries=retry)

    session = requests.Session()

    session.headers.update(HEADERS)

    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session


SESSION = create_session()

# Runtime safety: temporarily stop hammering hosts that repeatedly fail.
_FAILED_HOSTS = {}
_FAILED_HOST_TTL = 900

def _host_key(url):
    try:
        return (urlparse(str(url)).hostname or "").lower()
    except Exception:
        return ""

def _host_blocked(url):
    host = _host_key(url)
    if not host:
        return False
    ts = _FAILED_HOSTS.get(host)
    return bool(ts and time.time() - ts < _FAILED_HOST_TTL)

def _mark_host_failed(url):
    host = _host_key(url)
    if host:
        _FAILED_HOSTS[host] = time.time()


# =========================================================
# KEYWORDS
# =========================================================

JOB_KEYWORDS = [

    "recruitment",
    "vacancy",
    "vacancies",
    "notification",
    "advertisement",
    "advt",
    "job",
    "jobs",
    "career",
    "employment",
    "apply online",
    "online form",
    "registration",
    "walk in",
    "walk-in",
    "engagement",
    "admit card",
    "result",
    "answer key",
    "syllabus",
]
JOB_KEYWORDS.extend([

    "पदनाम",
    "विज्ञप्ति",
    "विज्ञापन",
    "भर्ती",
    "अधिसूचना",
    "आवेदन",
    "ऑनलाइन आवेदन",
    "चयन",
    "प्रवेश पत्र",
    "उत्तरकुंजी",
    "पाठ्यक्रम",
    "संशोधित",
    "रिक्त पद",
    "सीधी भर्ती",
    "संस्तुति"

])
IGNORE_KEYWORDS = [

    "facebook",
    "twitter",
    "instagram",
    "youtube",
    "privacy",
    "policy",
    "cookie",
    "login",
    "logout",
    "gallery",
    "contact",
    "feedback",
    "tender",
    "auction",
    "rti",
]

SUPPORTED_EXTENSIONS = [

    ".html",
    ".htm",
    ".php",
    ".aspx",
    ".pdf",

]

NOISE_WORDS = [

    "home",
    "homepage",
    "read more",
    "click here",
    "details",
    "view",
    "download",
    "new",
    "latest",

]

logger.info("Production Scraper v3.0 Loaded Successfully")
# =========================================================
# PART 2
# Utility Functions
# =========================================================

def download(url):

    if not url or _host_blocked(url):
        return None

    try:
        response = SESSION.get(
            url,
            timeout=(min(REQUEST_TIMEOUT, 5), REQUEST_TIMEOUT),
            allow_redirects=True
        )
        response.raise_for_status()
        return response.text
    except Exception as e:
        _mark_host_failed(url)
        logger.warning("Fetch failed: %s | %s", url, type(e).__name__)
        return None


# ---------------------------------------------------------

def get_soup(url):

    html = download(url)

    if not html:

        return None

    return BeautifulSoup(html, "lxml")


# ---------------------------------------------------------

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


# ---------------------------------------------------------

def is_supported_url(url):

    if not url:

        return False

    url = url.lower()

    if url.startswith(("mailto:", "tel:", "javascript:")):

        return False

    return True


# ---------------------------------------------------------

def is_internal_link(base, url):

    try:

        return (
            urlparse(base).netloc ==
            urlparse(url).netloc
        )

    except Exception:

        return False


# ---------------------------------------------------------

def is_pdf(url):

    if not url:

        return False

    return url.lower().endswith(".pdf")


# ---------------------------------------------------------

def normalize_spaces(text):

    if not text:

        return ""

    return re.sub(r"\s+", " ", str(text)).strip()


# ---------------------------------------------------------

def clean_title(title):

    if not title:

        return ""

    title = normalize_spaces(title)

    title = re.sub(r"\|.*$", "", title)

    title = re.sub(r"\(.*?\)", "", title)

    title = title.replace("_", " ")

    title = title.replace("-", " ")

    title = re.sub(r"\.html?$", "", title, flags=re.I)

    for word in NOISE_WORDS:

        title = re.sub(
            rf"\b{re.escape(word)}\b",
            "",
            title,
            flags=re.I
        )

    title = normalize_spaces(title)

    return title


# ---------------------------------------------------------

def has_job_keyword(text):

    if not text:

        return False

    text = text.lower()

    return any(
        keyword in text
        for keyword in JOB_KEYWORDS
    )


# ---------------------------------------------------------

def should_ignore(text):

    if not text:

        return True

    text = text.lower()

    return any(
        keyword in text
        for keyword in IGNORE_KEYWORDS
    )


# ---------------------------------------------------------

def unique_links(items):

    seen = set()

    output = []

    for item in items:

        url = item.get("url")

        if not url:

            continue

        if url in seen:

            continue

        seen.add(url)

        output.append(item)

    return output


# ---------------------------------------------------------

def score_link(title, url):

    data = f"{title} {url}".lower()

    score = 0

    weights = {

        "recruitment": 15,
        "vacancy": 15,
        "notification": 12,
        "advertisement": 10,
        "career": 10,
        "job": 8,
        "apply": 7,
        "registration": 6,
        "result": 5,
        "admit": 5,
        "answer key": 5,
        "syllabus": 5,
        ".pdf": 5

    }

    for key, value in weights.items():

        if key in data:

            score += value

    return score


# ---------------------------------------------------------

def save_database(data):

    try:

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


# ---------------------------------------------------------

def load_database():

    if not DATABASE_FILE.exists():

        return []

    try:

        with open(
            DATABASE_FILE,
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        return []
    # =========================================================
# PART 3
# Intelligent Recruitment Detection
# =========================================================

BAD_TITLES = [

    "accessibility",
    "accessibility tools",
    "act and rule",
    "click here",
    "home",
    "homepage",
    "privacy",
    "privacy policy",
    "cookie",
    "contact",
    "feedback",
    "gallery",
    "photo",
    "video",
    "login",
    "logout",
    "tender",
    "auction",
    "faq",
    "help",
    "copyright",
    "terms",
    "site map",
    "sitemap"

]
BAD_TITLES.extend([

    "organization structure",
    "organisation",
    "composition",
    "chairman",
    "members",
    "finance controller",
    "public information officer",
    "different section",
    "government orders",
    "digital uttarakhand",
    "website policies",
    "national portal",
    "contact us",
    "web information manager"

])

# ---------------------------------------------------------

def is_fake_title(title):

    if not title:

        return True

    text = title.lower()

    return any(
        bad in text
        for bad in BAD_TITLES
    )


# ---------------------------------------------------------

def is_recruitment(title, url):

    if not title:

        return False

    title = clean_title(title)

    if is_fake_title(title):

        return False

    data = f"{title} {url}".lower()

    return any(
        keyword in data
        for keyword in JOB_KEYWORDS
    )


# ---------------------------------------------------------

def extract_links(source_url):

    soup = get_soup(source_url)

    if soup is None:
        return []

    # -----------------------------
    # Smart Source Containers
    # -----------------------------

    selectors = [
        ".news",
        ".notice",
        ".notification",
        ".notifications",
        ".recruitment",
        ".recruitment-notification",
        ".latest-news",
        ".latest-updates",
        ".breaking-news",
        ".content",
        ".entry-content",
        ".main-content",
        "#content",
        "#main-content"
    ]

    containers = []

    for selector in selectors:
        containers.extend(soup.select(selector))

    if not containers:
        containers = [soup]

    results = []
    seen = set()

    for container in containers:

        for a in container.find_all("a", href=True):

            href = clean_url(source_url, a.get("href"))

            if not href:
                continue

            if not is_supported_url(href):
                continue

            title = clean_title(
                a.get_text(" ", strip=True)
            )

            if len(title) < 8:
                continue

            if len(title) > 250:
                continue

            if should_ignore(title):
                continue

            if should_ignore(href):
                continue

            # Smart Filter (filters.py)
            if not allow_job(title, href):
                continue

            # Important notification links
            important = any(x in href.lower() for x in [
                "/document/",
                "/recruitment",
                ".pdf",
                "notification",
                "advertisement",
                "advt",
                "career",
                "apply",
                "result",
                "answer",
                "admit"
            ])

            if not important and not has_job_keyword(title):
                continue

            if href in seen:
                continue

            seen.add(href)

            results.append({

                "title": title,
                "url": href,
                "score": score_link(title, href),
                "pdf": is_pdf(href),
                "internal": is_internal_link(
                    source_url,
                    href
                )

            })

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    logger.info(
        "%s : %d links found",
        source_url,
        len(results)
    )

    return results

# =========================================================
# Category Detection
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
        "rrb",
        "railway",
        "rrc"
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

    "Teaching Jobs": [
        "teacher",
        "faculty",
        "lecturer",
        "professor",
        "principal"
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
# PART 4
# Source Scraper
# =========================================================

def scrape_source(source):

    source_name = source.get("name", "Unknown")
    source_url = source.get("url", "")
    source_category = source.get("category", "Latest Jobs")
    source_state = source.get("state", "India")

    logger.info(f"Scraping : {source_name}")

    jobs = scrape_source(source)

    results = []

    for job in jobs:

        job["source"] = source_name

        if source_category:
            job["category"] = source_category
        else:
            job["category"] = detect_category(
                job["title"]
            )

        job["state"] = source_state

        job["priority"] = score_link(
            job["title"],
            job["url"]
        )

        results.append(job)

    results.sort(
        key=lambda x: x["priority"],
        reverse=True
    )

    logger.info(
        "%s : %d jobs",
        source_name,
        len(results)
    )

    return results


# =========================================================
# Multi Source Scraper
# =========================================================

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed
)


def _source_key(source):

    url = str(source.get("url", "") or "").strip().lower().rstrip("/")
    name = str(source.get("name", "") or "").strip().lower()
    return url or name


def _dedupe_sources(sources):

    seen = set()
    output = []

    for source in sources:
        key = _source_key(source)
        if not key or key in seen:
            continue
        seen.add(key)
        output.append(source)

    return output


def _load_rotation_state(total_batches):

    try:
        if SOURCE_ROTATION_FILE.exists():
            with open(SOURCE_ROTATION_FILE, encoding="utf-8") as f:
                state = json.load(f)
            index = int(state.get("batch_index", 0))
            return index % max(total_batches, 1)
    except Exception:
        logger.warning("Source rotation state unreadable; starting at batch 0")

    return 0


def _save_rotation_state(next_batch, total_batches):

    try:
        SOURCE_ROTATION_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SOURCE_ROTATION_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "batch_index": next_batch % max(total_batches, 1),
                "batch_size": SOURCE_BATCH_SIZE,
                "updated_at": datetime.utcnow().isoformat(),
            }, f, indent=2)
    except Exception:
        logger.exception("Source rotation state save failed")


def select_source_batch(sources):
    """Select a bounded rotating source batch so one run cannot process the full list."""

    sources = _dedupe_sources(sources)
    if not sources:
        return []

    # Keep explicitly important adapter sources in every run when possible.
    priority_sources = [
        s for s in sources
        if str(s.get("adapter", "generic")).lower() in {
            "ibps", "ssc", "upsc", "psc", "uk"
        } or int(s.get("priority", 0) or 0) >= 100
    ]

    # Railway sources are rotated, not forced into every run. Many zones currently
    # resolve to the same RRB endpoint, so processing all of them wastes the run.

    priority_keys = {_source_key(s) for s in priority_sources}
    rotating = [s for s in sources if _source_key(s) not in priority_keys]

    batch_size = max(1, SOURCE_BATCH_SIZE)
    mandatory = priority_sources[:batch_size]
    remaining_size = max(0, batch_size - len(mandatory))

    if not rotating or remaining_size == 0:
        selected = mandatory
    else:
        total_batches = max(1, (len(rotating) + remaining_size - 1) // remaining_size)
        batch_index = _load_rotation_state(total_batches)
        start = (batch_index * remaining_size) % len(rotating)
        selected = [rotating[(start + i) % len(rotating)] for i in range(min(remaining_size, len(rotating)))]
        _save_rotation_state(batch_index + 1, total_batches)
        selected = mandatory + selected

    # Stable order avoids changing the run shape unnecessarily.
    selected = _dedupe_sources(selected)[:batch_size]

    # Collapse repeated sources that point to the same host/path. This prevents
    # one unreachable government domain (notably RRB) from occupying many workers.
    seen_targets = set()
    compact = []
    for source in selected:
        url = str(source.get("url", "") or "").strip().lower().rstrip("/")
        parsed = urlparse(url)
        host = (parsed.hostname or "")
        target = (host, parsed.path or "/")
        if host == "www.rrbcdg.gov.in":
            target = (host, "/")
        if target in seen_targets:
            continue
        seen_targets.add(target)
        compact.append(source)
    selected = compact[:batch_size]

    logger.info(
        "Source Rotation : %d selected / %d enabled | batch_size=%d workers=%d",
        len(selected), len(sources), batch_size, SOURCE_WORKERS
    )
    return selected


def _scrape_source_process_entry(source, result_queue):
    """Run one source in an isolated process so OCR/parser hangs can be killed."""
    try:
        result_queue.put((True, scrape_source(source)))
    except BaseException as exc:
        try:
            result_queue.put((False, f"{type(exc).__name__}: {exc}"))
        except Exception:
            pass


def _kill_process_tree(proc):
    """Terminate a timed-out source and any OCR children it spawned."""
    try:
        import psutil
        parent = psutil.Process(proc.pid)
        children = parent.children(recursive=True)
        for child in children:
            try:
                child.terminate()
            except Exception:
                pass
        try:
            parent.terminate()
        except Exception:
            pass
        gone, alive = psutil.wait_procs(children + [parent], timeout=2)
        for child in alive:
            try:
                child.kill()
            except Exception:
                pass
    except Exception:
        try:
            proc.terminate()
        except Exception:
            pass


def _scrape_source_hard_timeout(source, timeout_seconds=35):
    """Return jobs or [] and guarantee one source cannot hold the run indefinitely."""
    ctx = mp.get_context("spawn")
    q = ctx.Queue(maxsize=1)
    proc = ctx.Process(target=_scrape_source_process_entry, args=(source, q), daemon=True)
    proc.start()
    proc.join(timeout_seconds)
    if proc.is_alive():
        logger.warning("SOURCE TIMEOUT | %s | %ss", source.get("name", "Unknown"), timeout_seconds)
        _kill_process_tree(proc)
        proc.join(timeout=2)
        return []
    try:
        ok, payload = q.get_nowait()
    except Exception:
        return []
    if not ok:
        logger.warning("SOURCE PROCESS FAILED | %s | %s", source.get("name", "Unknown"), payload)
        return []
    return payload or []


def scrape_all_sources(
    sources,
    workers=None
):
    """Scrape a small rotating batch with a hard per-source timeout.

    Thread futures cannot cancel a blocked OCR/tesseract call. Each source therefore
    runs in its own short-lived process; a hung source is terminated without holding
    the entire GitHub Actions job.
    """
    workers = min(4, max(1, workers or SOURCE_WORKERS))
    sources = select_source_batch(sources)
    all_jobs = []
    logger.info("Total Sources In This Run : %d", len(sources))

    # Keep the batch bounded even if an older workflow exports a larger value.
    sources = sources[:24]
    hard_timeout = int(os.getenv("EHU_SOURCE_TIMEOUT", "35"))

    pending = list(sources)
    active = []

    while pending or active:
        while pending and len(active) < workers:
            source = pending.pop(0)
            ctx = mp.get_context("spawn")
            q = ctx.Queue(maxsize=1)
            proc = ctx.Process(target=_scrape_source_process_entry, args=(source, q), daemon=True)
            proc.start()
            active.append((source, proc, q, time.monotonic()))

        next_active = []
        for source, proc, q, started in active:
            elapsed = time.monotonic() - started
            if proc.is_alive() and elapsed < hard_timeout:
                next_active.append((source, proc, q, started))
                continue
            if proc.is_alive():
                logger.warning("SOURCE TIMEOUT | %s | %ss", source.get("name", "Unknown"), hard_timeout)
                _kill_process_tree(proc)
                proc.join(timeout=2)
                continue
            try:
                ok, payload = q.get_nowait()
                if ok and payload:
                    all_jobs.extend(payload)
                elif not ok:
                    logger.warning("SOURCE PROCESS FAILED | %s | %s", source.get("name", "Unknown"), payload)
            except Exception:
                logger.warning("SOURCE NO RESULT | %s", source.get("name", "Unknown"))
        active = next_active
        if active:
            time.sleep(0.15)

    all_jobs = unique_links(all_jobs)
    all_jobs.sort(key=lambda x: x.get("priority", x.get("score", 0)), reverse=True)
    logger.info("Collected Jobs : %d", len(all_jobs))
    return all_jobs


# =========================================================
# Retry Failed Sources
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
            "Retry %d",
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
    # =========================================================
# PART 5
# Job Detail Extractor
# =========================================================

VACANCY_PATTERNS = [
    r"(\d+)\s+posts?",
    r"(\d+)\s+vacancies?",
    r"total\s+(\d+)",
    r"(\d+)\s+positions?"
]

LAST_DATE_PATTERNS = [
    r"last\s*date.*?(\d{2}[/-]\d{2}[/-]\d{4})",
    r"closing\s*date.*?(\d{2}[/-]\d{2}[/-]\d{4})",
    r"apply\s*before.*?(\d{2}[/-]\d{2}[/-]\d{4})",
    r"apply\s*last\s*date.*?(\d{2}[/-]\d{2}[/-]\d{4})"
]

SALARY_PATTERNS = [
    r"₹\s?[\d,]+",
    r"Rs\.?\s?[\d,]+",
    r"Pay\s*Level[- ]?\d+",
    r"Level[- ]?\d+"
]

QUALIFICATIONS = [
    "10th",
    "12th",
    "ITI",
    "Diploma",
    "Graduate",
    "Graduation",
    "B.Sc",
    "B.Tech",
    "BE",
    "B.E",
    "M.Sc",
    "MBA",
    "CA",
    "LLB",
    "PhD",
    "MBBS",
    "Nursing"
]


# ---------------------------------------------------------

def extract_pattern(patterns, text):

    if not text:
        return None

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.I
        )

        if match:

            return match.group(1) if match.groups() else match.group()

    return None


# ---------------------------------------------------------

def extract_qualification(text):

    if not text:
        return None

    found = []

    lower = text.lower()

    for item in QUALIFICATIONS:

        if item.lower() in lower:

            found.append(item)

    if found:

        return ", ".join(sorted(set(found)))

    return None


# ---------------------------------------------------------

def get_page_text(url):

    soup = get_soup(url)

    if soup is None:

        return ""

    for tag in soup([
        "script",
        "style",
        "noscript",
        "svg",
        "header",
        "footer",
        "nav",
        "iframe"
    ]):

        tag.decompose()

    text = soup.get_text(
        " ",
        strip=True
    )

    return normalize_spaces(text)


# ---------------------------------------------------------

def find_notification_pdf(soup, base_url):

    if soup is None:

        return None

    for a in soup.find_all("a", href=True):

        href = clean_url(
            base_url,
            a["href"]
        )

        if href and href.lower().endswith(".pdf"):

            return href

    return None


# ---------------------------------------------------------

def find_apply_link(soup, base_url):

    if soup is None:

        return None

    for a in soup.find_all("a", href=True):

        text = a.get_text(
            " ",
            strip=True
        ).lower()

        if any(word in text for word in [
            "apply",
            "registration",
            "online application",
            "apply online"
        ]):

            return clean_url(
                base_url,
                a["href"]
            )

    return None


# ---------------------------------------------------------

def extract_job_details(job):

    try:

        text = get_page_text(job["url"])

        if not text:

            return job

        soup = get_soup(job["url"])

        job["vacancy"] = extract_pattern(
            VACANCY_PATTERNS,
            text
        )

        job["last_date"] = extract_pattern(
            LAST_DATE_PATTERNS,
            text
        )

        job["salary"] = extract_pattern(
            SALARY_PATTERNS,
            text
        )

        job["qualification"] = extract_qualification(
            text
        )

        job["notification_pdf"] = find_notification_pdf(
            soup,
            job["url"]
        )

        job["apply_link"] = find_apply_link(
            soup,
            job["url"]
        )

        return job

    except Exception as e:

        logger.error(e)

        return job


# ---------------------------------------------------------

def enrich_jobs(jobs):

    output = []

    for job in jobs:

        output.append(

            extract_job_details(job)

        )

    return output
    # =========================================================
# PART 6
# Duplicate Filter, Department, SEO & Optimizer
# =========================================================

import hashlib


# ---------------------------------------------------------
# Normalize Text
# ---------------------------------------------------------

def normalize_text(text):

    if not text:
        return ""

    text = str(text).lower().strip()

    text = re.sub(r"\s+", " ", text)

    text = re.sub(r"[^a-z0-9 ]", "", text)

    return text


# ---------------------------------------------------------
# Generate Job ID
# ---------------------------------------------------------

def generate_job_id(job):

    key = "|".join([

        normalize_text(job.get("title")),

        normalize_text(job.get("url")),

        normalize_text(job.get("source")),

        normalize_text(job.get("last_date"))

    ])

    return hashlib.md5(
        key.encode("utf-8")
    ).hexdigest()


# ---------------------------------------------------------
# Remove Duplicate Jobs
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Department Detection
# ---------------------------------------------------------

DEPARTMENT_RULES = {

    "Railway": [
        "railway",
        "rrb",
        "rrc"
    ],

    "Banking": [
        "bank",
        "ibps",
        "rbi",
        "nabard",
        "lic"
    ],

    "Defence": [
        "army",
        "navy",
        "air force",
        "drdo",
        "crpf",
        "bsf",
        "cisf",
        "itbp"
    ],

    "Teaching": [
        "teacher",
        "lecturer",
        "faculty",
        "professor",
        "principal"
    ],

    "Medical": [
        "doctor",
        "medical",
        "nurse",
        "pharmacist",
        "aiims"
    ],

    "Engineering": [
        "engineer",
        "civil",
        "mechanical",
        "electrical"
    ]

}


def detect_department(title):

    title = title.lower()

    for department, words in DEPARTMENT_RULES.items():

        if any(word in title for word in words):

            return department

    return "Government"


# ---------------------------------------------------------
# Auto Tags
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# SEO Keywords
# ---------------------------------------------------------

def generate_keywords(job):

    title = job.get("title", "")

    keywords = [

        title,

        f"{title} Recruitment",

        f"{title} Notification",

        f"{title} Apply Online",

        f"{title} Vacancy",

        f"{title} Jobs"

    ]

    return list(dict.fromkeys(keywords))


# ---------------------------------------------------------
# Final Optimizer
# ---------------------------------------------------------

def optimize_jobs(jobs):

    optimized = []

    for job in jobs:

        job["title"] = clean_title(

            job.get("title", "")

        )

        job["department"] = detect_department(

            job["title"]

        )

        job["tags"] = generate_tags(job)

        job["keywords"] = generate_keywords(job)

        optimized.append(job)

    optimized = remove_duplicate_jobs(optimized)

    optimized.sort(

        key=lambda x: (
            x.get("priority", 0),
            x.get("title", "")
        ),

        reverse=True

    )

    logger.info(

        "Final Jobs : %d",

        len(optimized)

    )

    return optimized
    # =========================================================
# PART 7
# Sources Loader, Database & Main Pipeline
# =========================================================

from datetime import datetime


# ---------------------------------------------------------
# Load Sources
# ---------------------------------------------------------

def load_sources(file_path="bot/sources.json"):

    if not os.path.exists(file_path):

        logger.error("Sources file not found : %s", file_path)

        return []

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as f:

            sources = json.load(f)

    except Exception as e:

        logger.exception(e)

        return []

    enabled = [

        source

        for source in sources

        if source.get("enabled", True)

    ]

    logger.info(
        "Loaded %d Sources",
        len(enabled)
    )

    return enabled


# ---------------------------------------------------------
# Timestamp
# ---------------------------------------------------------

def add_timestamp(jobs):

    now = datetime.utcnow().isoformat()

    for job in jobs:

        job["scraped_at"] = now

    return jobs


# ---------------------------------------------------------
# Existing Database
# ---------------------------------------------------------

def load_existing_jobs():

    return load_database()


# ---------------------------------------------------------
# New Jobs Filter
# ---------------------------------------------------------

def filter_new_jobs(new_jobs, old_jobs):

    old_ids = {

        job.get("job_id")

        for job in old_jobs

    }

    fresh = []

    for job in new_jobs:

        if job["job_id"] not in old_ids:

            fresh.append(job)

    return fresh


# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------

def print_summary(jobs):

    logger.info("=" * 50)

    logger.info(
        "Total Jobs : %d",
        len(jobs)
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

    for dept, total in sorted(departments.items()):

        logger.info(
            "%s : %d",
            dept,
            total
        )

    logger.info("=" * 50)


# ---------------------------------------------------------
# Main Pipeline
# ---------------------------------------------------------

def run_pipeline():

    logger.info("Pipeline Started")

    sources = load_sources()

    if not sources:
        logger.warning("No Sources Loaded")
        return []

    jobs = scrape_all_sources(
        sources,
        workers=SOURCE_WORKERS
    )

    logger.info(
        "Scraped Jobs : %d",
        len(jobs)
    )

    jobs = enrich_jobs(jobs)

    jobs = optimize_jobs(jobs)

    jobs = add_timestamp(jobs)

    existing_jobs = load_existing_jobs()

    existing_jobs = remove_duplicate_jobs(existing_jobs)

    jobs = remove_duplicate_jobs(jobs)

    new_jobs = filter_new_jobs(
        jobs,
        existing_jobs
    )

    updated_jobs = remove_duplicate_jobs(
        existing_jobs + new_jobs
    )

    save_database(updated_jobs)

    print_summary(jobs)

    logger.info(
        "New Jobs : %d",
        len(new_jobs)
    )

    return new_jobs
    # =========================================================
# PART 8
# Final Execution Pipeline
# =========================================================

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


# ---------------------------------------------------------
# Main Scraper
# ---------------------------------------------------------

def scrape_all():

    logger.info("=" * 60)
    logger.info("Education Update Hub Auto Publisher Started")
    logger.info("=" * 60)

    try:

        new_jobs = run_pipeline()

        if not new_jobs:

            logger.info("No New Jobs Found")
            return []

        logger.info("New Jobs : %d", len(new_jobs))

        # Duplicate Checker
        if remove_existing_jobs:

            try:
                new_jobs = remove_existing_jobs(new_jobs)

                logger.info(
                    "After Duplicate Filter : %d",
                    len(new_jobs)
                )

            except Exception:
                logger.exception(
                    "Duplicate Checker Failed"
                )

        if not new_jobs:

            logger.info("Everything Already Published")
            return []

        # HTML Generator
        if generate_all:

            try:

                generate_all(new_jobs)

                logger.info("HTML Generated")

            except Exception:

                logger.exception(
                    "HTML Generation Failed"
                )

        # Homepage
        if update_homepage:

            try:

                update_homepage(new_jobs)

                logger.info("Homepage Updated")

            except Exception:

                logger.exception(
                    "Homepage Update Failed"
                )

        # Sitemap
        if update_sitemap:

            try:

                update_sitemap(new_jobs)

                logger.info("Sitemap Updated")

            except Exception:

                logger.exception(
                    "Sitemap Update Failed"
                )

        logger.info("=" * 60)
        logger.info("Automation Completed Successfully")
        logger.info("=" * 60)

        return new_jobs

    except Exception:

        logger.exception(
            "Pipeline Failed"
        )

        return []

def _build_adapter(adapter_def):
    """Return an adapter instance regardless of whether ADAPTERS stores a class or instance."""
    if adapter_def is None:
        return None
    try:
        # Most project adapters are classes. Instantiate them before calling instance methods.
        if isinstance(adapter_def, type):
            return adapter_def()
    except Exception:
        pass
    return adapter_def


def _adapter_label(adapter):
    """Get a safe human-readable adapter name without touching an unbound property."""
    if adapter is None:
        return "Generic"
    try:
        value = getattr(adapter, "name", None)
        if isinstance(value, str) and value.strip():
            return value.strip()
    except Exception:
        pass
    return adapter.__class__.__name__.replace("Adapter", "") or "Generic"


def scrape_source(source):
    """Scrape one source using a properly instantiated adapter.

    The previous runtime called adapter classes directly. That caused errors such as
    `RailwayAdapter has no attribute name` and `GenericAdapter.scrape() missing source`.
    """
    adapter_name = str(source.get("adapter", "generic") or "generic").strip().lower()
    adapter_def = ADAPTERS.get(adapter_name) or ADAPTERS.get("generic")
    adapter = _build_adapter(adapter_def)
    source_name = source.get("name", "Unknown")

    if adapter is None:
        logger.error("No adapter available for %s (adapter=%s)", source_name, adapter_name)
        return []

    label = _adapter_label(adapter)
    logger.info("Using %s Adapter : %s", label, source_name)

    try:
        scrape_fn = getattr(adapter, "scrape", None)
        if not callable(scrape_fn):
            raise TypeError(f"Adapter {label} has no callable scrape() method")

        # Adapters in this project use either scrape(source) or scrape(source, session).
        try:
            jobs = scrape_fn(source, session=SESSION)
        except TypeError as exc:
            if "session" not in str(exc).lower():
                raise
            jobs = scrape_fn(source)

        jobs = jobs or []
        try:
            jobs = optimize_jobs(jobs)
        except Exception:
            logger.exception("Job optimization failed for %s; keeping scraped jobs", source_name)

        if not jobs:
            logger.warning("No jobs found : %s", source_name)
        else:
            logger.info("%d jobs collected from %s", len(jobs), source_name)
        return jobs

    except Exception as exc:
        logger.error("%s Failed", source_name)
        logger.error("%s", exc)

        # Do not let a broken custom adapter kill the source. Fall back to the generic
        # link extractor once; this is especially useful for simple HTML notice pages.
        try:
            fallback = extract_links(source.get("url", ""))
            if fallback:
                logger.info("Generic fallback recovered %d links from %s", len(fallback), source_name)
            return fallback
        except Exception:
            logger.exception("Generic fallback failed for %s", source_name)
            return []
# ---------------------------------------------------------
# GitHub Actions Entry
# ---------------------------------------------------------

def main():

    return scrape_all()


# ---------------------------------------------------------
# Standalone Execution
# ---------------------------------------------------------

if __name__ == "__main__":

    main()
