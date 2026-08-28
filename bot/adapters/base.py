"""
=========================================================
Education Update Hub
Production Base Adapter
Phase 1 - Part 1
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
        "copyright"

    ]

    def __init__(self):

        retry = Retry(
            total=1,
            connect=1,
            read=1,
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

            "Accept":
            "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"

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
    # Detect Post Type
    # =====================================================

    def detect_post_type(self, title, url="", category=""):
        text = re.sub(r"\s+", " ", f"{title or ''} {category or ''}").strip().lower()
        # Preserve an explicit scheme category for legacy records. Only an
        # unmistakable recruitment/application title may override it.
        scheme_category = any(x in text for x in ("government scheme", "government schemes", "scheme", "yojana", "योजना"))
        explicit_recruitment = any(x in text for x in (
            "recruitment", "vacancy", "apply online", "applications are invited",
            "walk-in", "walk in", "appointment of", "engagement of", "भर्ती", "रिक्ति"
        ))
        if scheme_category and not explicit_recruitment:
            return "government-scheme"
        if any(x in text for x in ("admit card", "hall ticket", "e-admit", "प्रवेश पत्र", "call letter")):
            return "admit-card"
        if any(x in text for x in ("answer key", "answer keys", "उत्तर कुंजी", "उत्तरकुंजी")):
            return "answer-key"
        if any(x in text for x in ("result of", "results of", "result", "merit list", "scorecard", "परिणाम", "मेरिट")) and "recruitment" not in text:
            return "result"
        if any(x in text for x in ("syllabus", "indicative syllabus", "पाठ्यक्रम")):
            return "syllabus"
        if any(x in text for x in ("scholarship", "छात्रवृत्ति")):
            return "scholarship"
        if (any(x in text for x in ("scheme", "yojana", "योजना", "government scheme"))
                and not any(x in text for x in ("recruitment", "vacancy", "apply online", "applications are invited"))
                and not any(x in text for x in ("officer", "assistant", "teacher", "engineer", "technician", "clerk", "professor", "scientist"))):
            return "government-scheme"
        if any(x in text for x in ("recruitment", "vacancy", "advertisement", "advt", "apply online", "applications are invited", "walk-in", "walk in", "appointment of", "engagement of")):
            return "recruitment"
        if any(x in text for x in ("exam schedule", "exam programme", "timetable", "date sheet", "परीक्षा कार्यक्रम")):
            return "exam"
        return "other"

    # =====================================================
    # Download Page
    # =====================================================

    def fetch(self, url):

        try:

            r = self.session.get(
                url,
                timeout=10
            )

            r.raise_for_status()

            return r.text

        except Exception:

            return ""

    # =====================================================
    # BeautifulSoup
    # =====================================================

    def soup(self, url):

        html = self.fetch(url)

        if not html:

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

        text = re.sub(
            r"\s+",
            " ",
            str(text)
        )

        return text.strip()

    # =====================================================
    # Absolute URL
    # =====================================================

    def absolute(self, base, url):

        return urljoin(
            base,
            url
        )

    # =====================================================
    # Page Text
    # =====================================================

    def page_text(self, soup):

        if soup is None:

            return ""

        return self.clean(

            soup.get_text(
                " ",
                strip=True
            )

        )
      # =====================================================
    # Find Notification PDF
    # =====================================================

    def find_pdf(self, soup, base_url):

        if soup is None:
            return ""

        for link in soup.find_all("a", href=True):

            href = self.absolute(
                base_url,
                link["href"]
            )

            if href.lower().endswith(".pdf"):

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
            "online application",
            "fill application",
            "login"

        ]

        for link in soup.find_all("a", href=True):

            text = self.clean(

                link.get_text(
                    " ",
                    strip=True
                )

            ).lower()

            if any(k in text for k in keywords):

                return self.absolute(
                    base_url,
                    link["href"]
                )

        return ""


    # =====================================================
    # Extract Regex Value
    # =====================================================

    def extract_value(self, text, patterns):

        if not text:
            return ""

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if match:

                return self.clean(
                    match.group(1)
                )

        return ""


    # =====================================================
    # Vacancy
    # =====================================================

    def extract_vacancy(self, text):

        patterns = [

            r"(\d+)\s+posts?",
            r"(\d+)\s+vacancies",
            r"total\s+vacancy[:\s]+(\d+)",
            r"total\s+posts?[:\s]+(\d+)"

        ]

        return self.extract_value(
            text,
            patterns
        )


    # =====================================================
    # Salary
    # =====================================================

    def extract_salary(self, text):

        patterns = [

            r"salary[:\s]+([^\n]+)",
            r"pay\s+scale[:\s]+([^\n]+)",
            r"pay\s+level[:\s]+([^\n]+)"

        ]

        return self.extract_value(
            text,
            patterns
        )


    # =====================================================
    # Qualification
    # =====================================================

    def extract_qualification(self, text):

        patterns = [

            r"qualification[:\s]+([^\n]+)",
            r"eligibility[:\s]+([^\n]+)",
            r"educational\s+qualification[:\s]+([^\n]+)"

        ]

        return self.extract_value(
            text,
            patterns
        )


    # =====================================================
    # Last Date
    # =====================================================

    def extract_last_date(self, text):

        patterns = [

            r"last\s+date[:\s]+([^\n]+)",
            r"closing\s+date[:\s]+([^\n]+)",
            r"apply\s+last\s+date[:\s]+([^\n]+)",
            r"online\s+application\s+last\s+date[:\s]+([^\n]+)"

        ]

        return self.extract_value(
            text,
            patterns
        )


    # =====================================================
    # Job Link Filter
    # =====================================================

    def is_job_link(self, title):

        title = self.clean(title).lower()

        if any(
            word in title
            for word in self.IGNORE_KEYWORDS
        ):
            return False

        return any(
            word in title
            for word in self.JOB_KEYWORDS
        )


    # =====================================================
    # Date Validation
    # =====================================================

    def is_recent(self, value):

        if not value:
            return True

        return True
      # =====================================================
    # Build Job Dictionary
    # =====================================================

    def build_job(
        self,
        title,
        url,
        department="",
        category="Latest Jobs"
    ):

        return {

            "title": self.clean(title),

            "url": url,

            "department": department,

            "category": category,

            "vacancy": "",

            "qualification": "",

            "salary": "",

            "age_limit": "",

            "application_fee": "",

            "selection_process": "",

            "exam_date": "",

            "last_date": "",

            "notification_pdf": "",

            "apply_link": "",

            "description": "",

            "content": ""

        }


    # =====================================================
    # Enrich Job
    # =====================================================

    def enrich_job(self, job):

        url = job.get("url")

        if not url:
            return job

        soup = self.soup(url)

        if soup is None:
            return job

        text = self.page_text(soup)

        job["content"] = text

        job["description"] = text[:350]

        job["vacancy"] = self.extract_vacancy(text)

        job["salary"] = self.extract_salary(text)

        job["qualification"] = self.extract_qualification(text)

        job["last_date"] = self.extract_last_date(text)

        job["notification_pdf"] = self.find_pdf(
            soup,
            url
        )

        job["apply_link"] = self.find_apply_link(
            soup,
            url
        )

        return job


    # =====================================================
    # Extract Recruitment Links
    # =====================================================

    def extract_links(self, soup, base_url):

        jobs = []

        visited = set()

        if soup is None:
            return jobs

        for link in soup.find_all("a", href=True):

            title = self.clean(
                link.get_text(
                    " ",
                    strip=True
                )
            )

            href = self.absolute(
                base_url,
                link["href"]
            )

            if not title or not href:
                continue

            if href in visited:
                continue

            if not self.is_job_link(title):
                continue

            visited.add(href)

            jobs.append(
                self.build_job(
                    title,
                    href
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

        enriched = []

        for job in jobs:

            job["department"] = department

            enriched.append(
                self.enrich_job(job)
            )

        return enriched
