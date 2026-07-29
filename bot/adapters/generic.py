import re
from urllib.parse import urljoin
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from parser import get_soup


class GenericAdapter:

    name = "Generic"

    MAX_DAYS = 180

    def scrape(self, source):

        return self.scrape_generic(source["url"])

    # ------------------------------------
    # HELPERS
    # ------------------------------------

    def clean(self, text):

        if not text:
            return ""

        return re.sub(
            r"\s+",
            " ",
            text
        ).strip()

    def absolute(self, base, link):

        return urljoin(base, link)

    def fetch(self, url):

        try:

            headers = {
                "User-Agent":
                "Mozilla/5.0"
            }

            r = requests.get(
                url,
                headers=headers,
                timeout=20
            )

            if r.status_code != 200:
                return None

            return BeautifulSoup(
                r.text,
                "html.parser"
            )

        except Exception:

            return None

    def page_text(self, soup):

        return self.clean(
            soup.get_text(
                " ",
                strip=True
            )
        )

    def extract_pdf(self, soup, base):

        for a in soup.find_all("a", href=True):

            href = a["href"]

            if href.lower().endswith(".pdf"):

                return self.absolute(
                    base,
                    href
                )

        return ""

    def extract_apply(self, soup, base):

        keywords = [

            "apply",
            "apply online",
            "registration",
            "login"

        ]

        for a in soup.find_all("a", href=True):

            text = self.clean(
                a.get_text()
            ).lower()

            if any(
                k in text
                for k in keywords
            ):

                return self.absolute(
                    base,
                    a["href"]
                )

        return ""

    def find_value(
        self,
        text,
        patterns
    ):

        for pattern in patterns:

            m = re.search(
                pattern,
                text,
                flags=re.I
            )

            if m:

                return self.clean(
                    m.group(1)
                )

        return ""

    def is_recent(self, date_text):

        date_text = self.clean(date_text)

        formats = [

            "%d-%m-%Y",
            "%d/%m/%Y",
            "%d.%m.%Y",
            "%d %B %Y",
            "%d %b %Y"

        ]

        for fmt in formats:

            try:

                dt = datetime.strptime(
                    date_text,
                    fmt
                )

                return (
                    datetime.today() - dt
                ).days <= self.MAX_DAYS

            except Exception:

                pass

        return True
        # ------------------------------------
    # GENERIC SCRAPER
    # ------------------------------------

    def scrape_generic(self, url):

        soup = get_soup(url)

        if not soup:
            return []

        jobs = []

        keywords = [

            "recruitment",
            "recruitment notice",
            "vacancy",
            "notification",
            "advertisement",
            "career",
            "careers",
            "job",
            "jobs",
            "employment",
            "latest",
            "result",
            "exam",
            "apply",
            "walk in",
            "walk-in"

        ]

        for a in soup.find_all("a", href=True):

            title = self.clean(
                a.get_text()
            )

            if len(title) < 8:
                continue

            href = self.absolute(
                url,
                a.get("href", "")
            )

            title_lower = title.lower()

            if not any(
                k in title_lower
                for k in keywords
            ):
                continue

            page = self.fetch(href)

            if not page:
                continue

            body = self.page_text(page)

            last_date = self.find_value(

                body,

                [

                    r"Last Date[:\s]*([0-9./-]+)",
                    r"Closing Date[:\s]*([0-9./-]+)",
                    r"Last date[:\s]*([0-9./-]+)",
                    r"Apply Before[:\s]*([0-9./-]+)"

                ]

            )

            if last_date:

                if not self.is_recent(
                    last_date
                ):
                    continue

            job = {

                "title": title,

                "url": href,

                "department": "General",

                "last_date": last_date,

                "notification_pdf":
                    self.extract_pdf(
                        page,
                        href
                    ),

                "apply_link":
                    self.extract_apply(
                        page,
                        href
                    ),

                "description":
                    body[:500],

                "content":
                    body

            }

            jobs.append(
                self.enrich_job(job)
            )

        return jobs
        # ------------------------------------
    # ENRICH JOB DETAILS
    # ------------------------------------

    def enrich_job(self, job):

        page = self.fetch(job["url"])

        if not page:
            return job

        text = self.page_text(page)

        job["vacancy"] = self.find_value(

            text,

            [

                r"Total Vacancies[:\s]*([^\n]+)",
                r"Total Posts[:\s]*([^\n]+)",
                r"Vacancy[:\s]*([^\n]+)",
                r"Posts[:\s]*([^\n]+)"

            ]

        )

        job["qualification"] = self.find_value(

            text,

            [

                r"Educational Qualification[:\s]*([^\n]+)",
                r"Qualification[:\s]*([^\n]+)",
                r"Eligibility[:\s]*([^\n]+)"

            ]

        )

        job["age_limit"] = self.find_value(

            text,

            [

                r"Age Limit[:\s]*([^\n]+)",
                r"Minimum Age[:\s]*([^\n]+)",
                r"Maximum Age[:\s]*([^\n]+)"

            ]

        )

        job["salary"] = self.find_value(

            text,

            [

                r"Salary[:\s]*([^\n]+)",
                r"Pay Scale[:\s]*([^\n]+)",
                r"Basic Pay[:\s]*([^\n]+)"

            ]

        )

        job["application_fee"] = self.find_value(

            text,

            [

                r"Application Fee[:\s]*([^\n]+)",
                r"Fee[:\s]*([^\n]+)"

            ]

        )

        job["selection_process"] = self.find_value(

            text,

            [

                r"Selection Process[:\s]*([^\n]+)",
                r"Selection[:\s]*([^\n]+)"

            ]

        )

        job["exam_date"] = self.find_value(

            text,

            [

                r"Exam Date[:\s]*([^\n]+)",
                r"Written Exam[:\s]*([^\n]+)",
                r"Interview[:\s]*([^\n]+)"

            ]

        )

        job["notification_pdf"] = self.extract_pdf(
            page,
            job["url"]
        )

        job["apply_link"] = self.extract_apply(
            page,
            job["url"]
        )

        job["description"] = text[:500]

        job["content"] = text

        return job
