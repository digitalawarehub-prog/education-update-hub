"""
=========================================================
Education Update Hub
Production Base Adapter
Version 3.0
Part 1
=========================================================
"""

import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class BaseAdapter:

    USER_AGENT = (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/138.0 Safari/537.36"
    )

    JOB_KEYWORDS = [
        "recruitment",
        "notification",
        "vacancy",
        "advertisement",
        "advt",
        "apply",
        "apply online",
        "direct recruitment",
        "result",
        "answer key",
        "admit card",
        "hall ticket",
        "merit list",
        "walk in interview",
        "posts"
    ]

    IGNORE_KEYWORDS = [
        "contact",
        "feedback",
        "privacy",
        "policy",
        "gallery",
        "chairman",
        "member",
        "organisation",
        "organization",
        "about",
        "rti",
        "calendar",
        "help",
        "accessibility",
        "copyright",
        "photo gallery",
        "video gallery",
        "sitemap"
    ]

    def __init__(self):

        retry = Retry(
            total=2,
            connect=2,
            read=2,
            backoff_factor=1,
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

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": self.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"
        })

        self.session.mount(
            "https://",
            adapter
        )

        self.session.mount(
            "http://",
            adapter
        )

    # =====================================================
    # Download Page
    # =====================================================

    def fetch(self, url):

        try:

            response = self.session.get(
                url,
                timeout=20,
                allow_redirects=True
            )

            response.raise_for_status()

            return response.text

        except Exception:
            return ""

    # =====================================================
    # BeautifulSoup
    # =====================================================

    def soup(self, url):

        html = self.fetch(url)

        if not html:
            return None

        if isinstance(html, bytes):

            if html.startswith(b"%PDF"):
                return None

            html = html.decode(
                "utf-8",
                errors="ignore"
            )

        if (
            isinstance(html, str)
            and html.lstrip().startswith("%PDF")
        ):
            return None

        return BeautifulSoup(
            html,
            "html.parser"
        )
# =====================================================
# Clean Text
# =====================================================

def clean(self, text):

    if not text:
        return ""

    text = str(text)

    # Remove Jinja / Angular template text
    text = re.sub(r"\{\{.*?\}\}", "", text)

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text)

    # Remove unwanted symbols
    text = text.replace("\xa0", " ")

    return text.strip()


# =====================================================
# Absolute URL
# =====================================================

def absolute(self, base, url):

    if not url:
        return ""

    return urljoin(base, url)


# =====================================================
# Page Text
# =====================================================

def page_text(self, soup):

    if soup is None:
        return ""

    # Remove unwanted tags
    for tag in soup([
        "script",
        "style",
        "header",
        "footer",
        "nav",
        "aside",
        "noscript",
        "svg"
    ]):
        tag.decompose()

    main = (
        soup.find("article")
        or soup.find("main")
        or soup.find("div", class_="entry-content")
        or soup.find("div", class_="post-content")
        or soup.find("div", class_="content")
        or soup.find("section")
        or soup.find("body")
    )

    if not main:
        return ""

    text = main.get_text("\n", strip=True)

    text = self.clean(text)

    return text


# =====================================================
# Find Notification PDF
# =====================================================

def find_pdf(self, soup, base_url):

    if soup is None:
        return ""

    keywords = [
        "notification",
        "advertisement",
        "download",
        "pdf",
        "advt",
        "official notification"
    ]

    for link in soup.find_all("a", href=True):

        href = self.absolute(
            base_url,
            link["href"]
        )

        text = self.clean(
            link.get_text(" ", strip=True)
        ).lower()

        if href.lower().endswith(".pdf"):
            return href

        if any(k in text for k in keywords):
            return href

    return ""


# =====================================================
# Find Apply Link
# =====================================================

def find_apply_link(self, soup, base_url):

    if soup is None:
        return ""

    keywords = [
        "apply",
        "apply online",
        "registration",
        "candidate login",
        "new registration",
        "online form",
        "click here",
        "apply now"
    ]

    for link in soup.find_all("a", href=True):

        href = self.absolute(
            base_url,
            link["href"]
        )

        text = self.clean(
            link.get_text(" ", strip=True)
        ).lower()

        if any(k in text for k in keywords):
            return href

    return ""
# =====================================================
# Extract Regex Value
# =====================================================

def extract_value(self, text, patterns):

    if not text:
        return ""

    text = self.clean(text)

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE | re.MULTILINE
        )

        if match:
            return self.clean(match.group(1))

    return ""


# =====================================================
# Vacancy
# =====================================================

def extract_vacancy(self, text):

    patterns = [
        r"(\d+)\s+posts?",
        r"(\d+)\s+vacancies",
        r"total\s+vacancy[:\s\-]+(\d+)",
        r"total\s+posts?[:\s\-]+(\d+)",
        r"number\s+of\s+posts?[:\s\-]+(\d+)"
    ]

    return self.extract_value(text, patterns)


# =====================================================
# Salary
# =====================================================

def extract_salary(self, text):

    patterns = [
        r"salary[:\s\-]+([^\n]+)",
        r"pay\s+scale[:\s\-]+([^\n]+)",
        r"pay\s+level[:\s\-]+([^\n]+)",
        r"monthly\s+salary[:\s\-]+([^\n]+)"
    ]

    return self.extract_value(text, patterns)


# =====================================================
# Qualification
# =====================================================

def extract_qualification(self, text):

    patterns = [
        r"qualification[:\s\-]+([^\n]+)",
        r"eligibility[:\s\-]+([^\n]+)",
        r"educational\s+qualification[:\s\-]+([^\n]+)",
        r"essential\s+qualification[:\s\-]+([^\n]+)"
    ]

    return self.extract_value(text, patterns)


# =====================================================
# Last Date
# =====================================================

def extract_last_date(self, text):

    patterns = [
        r"last\s+date[:\s\-]+([^\n]+)",
        r"closing\s+date[:\s\-]+([^\n]+)",
        r"apply\s+last\s+date[:\s\-]+([^\n]+)",
        r"last\s+date\s+to\s+apply[:\s\-]+([^\n]+)"
    ]

    return self.extract_value(text, patterns)
# =====================================================
# Build Job
# =====================================================

def build_job(
    self,
    title,
    url,
    department="",
    category="Latest Jobs"
):

    title = self.clean(title)

    return {
        "title": title,
        "url": url,

        # Basic Info
        "department": department,
        "category": category,

        # Recruitment Details
        "vacancy": "",
        "qualification": "",
        "salary": "",
        "last_date": "",

        # Important Links
        "notification_pdf": url,
        "apply_link": url,
        "official_website": url,

        # Images
        "image": "",
        "thumbnail": "",
        "featured_image": "",

        # Content
        "description": "",
        "content": "",

        # SEO
        "tags": [],
        "priority": 0
    }


# =====================================================
# Enrich Job
# =====================================================

def enrich_job(self, job):

    url = job.get("url", "")

    if not url:
        return job

    try:

        content_type = self.session.head(
            url,
            allow_redirects=True,
            timeout=5
        ).headers.get(
            "Content-Type",
            ""
        )

    except Exception:

        content_type = ""

    # PDF Direct Link
    if (
        "pdf" in content_type.lower()
        or url.lower().endswith(".pdf")
    ):

        job["content"] = ""
        job["description"] = "Official Notification PDF Available."

        job["notification_pdf"] = url
        job["apply_link"] = url
        job["official_website"] = url

        return job

    soup = self.soup(url)

    if soup is None:
        return job

    text = self.page_text(soup)

    if len(text) > 7000:
        text = text[:7000]

    job["content"] = text
    job["description"] = text[:400]

    job["vacancy"] = self.extract_vacancy(text)
    job["salary"] = self.extract_salary(text)
    job["qualification"] = self.extract_qualification(text)
    job["last_date"] = self.extract_last_date(text)

    # Links
    pdf = self.find_pdf(soup, url)
    apply = self.find_apply_link(soup, url)

    job["notification_pdf"] = pdf if pdf else url
    job["apply_link"] = apply if apply else url
    job["official_website"] = url

    # Image
    img = soup.find("meta", property="og:image")

    if img and img.get("content"):
        job["image"] = img["content"]
        job["thumbnail"] = img["content"]
        job["featured_image"] = img["content"]

    return job
# =====================================================
# Detect Category
# =====================================================

def detect_category(self, title):

    title = self.clean(title).lower()

    if any(x in title for x in [
        "admit card",
        "hall ticket",
        "call letter",
        "e-admit card"
    ]):
        return "Admit Card"

    if any(x in title for x in [
        "result",
        "final result",
        "merit list",
        "selection list",
        "score card"
    ]):
        return "Results"

    if any(x in title for x in [
        "answer key",
        "provisional answer key",
        "final answer key"
    ]):
        return "Answer Key"

    if any(x in title for x in [
        "syllabus",
        "exam pattern"
    ]):
        return "Syllabus"

    if any(x in title for x in [
        "scholarship",
        "fellowship"
    ]):
        return "Scholarship"

    return "Latest Jobs"


# =====================================================
# Extract Links
# =====================================================

def extract_links(self, soup, base_url):

    jobs = []

    visited = set()

    if soup is None:
        return jobs

    for link in soup.find_all("a", href=True):

        title = self.clean(
            link.get_text(" ", strip=True)
        )

        href = self.absolute(
            base_url,
            link.get("href", "")
        )

        if not title or not href:
            continue

        title_lower = title.lower()

        # Skip Template
        if "{{" in title or "}}" in title:
            continue

        if "translate" in title_lower:
            continue

        # Skip Short
        if len(title) < 6:
            continue

        # Skip JS
        if href.startswith("#"):
            continue

        if href.lower().startswith("javascript"):
            continue

        if href.lower().startswith("mailto:"):
            continue

        # Skip unwanted pages
        if any(x in title_lower for x in [
            "gallery",
            "photo",
            "video",
            "chairman",
            "member",
            "contact",
            "feedback",
            "privacy",
            "policy",
            "help",
            "dashboard",
            "login",
            "translate",
            "notifications notices",
            "work recruitments"
        ]):
            continue

        if href in visited:
            continue

        visited.add(href)

        jobs.append(

            self.build_job(

                title=title,

                url=href,

                category=self.detect_category(title)

            )

        )

    return jobs


# =====================================================
# Common Scraper
# =====================================================

def scrape_page(
    self,
    url,
    department=""
):

    soup = self.soup(url)

    jobs = self.extract_links(
        soup,
        url
    )

    result = []

    for job in jobs:

        job["department"] = department

        result.append(
            self.enrich_job(job)
        )

    return result
