import re
from urllib.parse import urljoin
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

from parser import get_soup


class UKAdapter:

    name = "UK"

    # 6 महीने से पुरानी notification skip
    MAX_DAYS = 180

    def scrape(self, source):

        url = source["url"]

        if "psc.uk.gov.in" in url:
            return self.scrape_ukpsc(url)

        if "sssc.uk.gov.in" in url:
            return self.scrape_uksssc(url)

        return []

    # ------------------------------------
    # COMMON HELPERS
    # ------------------------------------

    def clean(self, text):

        if not text:
            return ""

        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def absolute(self, base, link):

        if not link:
            return ""

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

    def extract_pdf(self, soup, base):

        for a in soup.find_all("a", href=True):

            href = a["href"]

            if ".pdf" in href.lower():
                return self.absolute(base, href)

        return ""

    def extract_apply(self, soup, base):

        words = [
            "apply",
            "online",
            "registration",
            "login"
        ]

        for a in soup.find_all("a", href=True):

            txt = self.clean(a.get_text()).lower()

            if any(x in txt for x in words):

                return self.absolute(
                    base,
                    a["href"]
                )

        return ""

    def page_text(self, soup):

        return self.clean(
            soup.get_text(
                " ",
                strip=True
            )
        )

    def find_value(self, text, patterns):

        for p in patterns:

            m = re.search(
                p,
                text,
                flags=re.I
            )

            if m:
                return self.clean(
                    m.group(1)
                )

        return ""

    def is_recent(self, text):

        text = self.clean(text)

        formats = [
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%d.%m.%Y",
            "%d %B %Y",
            "%d %b %Y"
        ]

        for f in formats:

            try:

                dt = datetime.strptime(
                    text,
                    f
                )

                if (
                    datetime.today() - dt
                ).days <= self.MAX_DAYS:
                    return True

            except Exception:
                pass

        return True
        # ------------------------------------
    # UKPSC SCRAPER
    # ------------------------------------

    def scrape_ukpsc(self, url):

        soup = get_soup(url)

        if not soup:
            return []

        jobs = []

        for a in soup.find_all("a", href=True):

            title = self.clean(a.get_text())

            if len(title) < 10:
                continue

            href = self.absolute(
                url,
                a.get("href", "")
            )

            text = title.lower()

            keywords = [

                "advertisement",
                "recruitment",
                "notification",
                "assistant",
                "officer",
                "inspector",
                "engineer",
                "lecturer",
                "professor",
                "exam"

            ]

            if not any(k in text for k in keywords):
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
                    r"Last date for submission[:\s]*([0-9./-]+)"

                ]

            )

            if last_date and not self.is_recent(last_date):
                continue

        job = {

            "title": title,
            "url": href,
            "department": "UKPSC",
            "last_date": last_date,
            "notification_pdf": self.extract_pdf(page, href),
            "apply_link": self.extract_apply(page, href),
            "description": body[:500],
            "content": body

        }

        jobs.append(
            self.enrich_job(job)
        )

        return jobs

    # ------------------------------------
    # UKSSSC SCRAPER
    # ------------------------------------

    def scrape_uksssc(self, url):

        soup = get_soup(url)

        if not soup:
            return []

        jobs = []
        for a in soup.find_all("a", href=True):

            title = self.clean(a.get_text())

            if len(title) < 10:
                continue

            href = self.absolute(
                url,
                a.get("href", "")
            )

            text = title.lower()

            keywords = [

                "recruitment",
                "notification",
                "group c",
                "group-c",
                "assistant",
                "technician",
                "police",
                "constable",
                "forest",
                "driver"

            ]

            if not any(k in text for k in keywords):
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
                    r"Last date[:\s]*([0-9./-]+)"

                ]

            )

            if last_date and not self.is_recent(last_date):
                continue

            job = {

                "title": title,
                "url": href,
                "department": "UKPSC",
                "last_date": last_date,
                "notification_pdf": self.extract_pdf(page, href),
                "apply_link": self.extract_apply(page, href),
                 "description": body[:500],
                "content": body

            }

jobs.append(
    self.enrich_job(job)
)

        return jobs
        # ------------------------------------
    # UNIVERSAL FIELD EXTRACTOR
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
                r"Vacancies[:\s]*([^\n]+)",
                r"Posts[:\s]*([^\n]+)"

            ]

        )

        job["qualification"] = self.find_value(

            text,

            [

                r"Qualification[:\s]*([^\n]+)",
                r"Educational Qualification[:\s]*([^\n]+)",
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
                r"Pay Level[:\s]*([^\n]+)"

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

                r"Exam Date[:\s]*([^\n]+)"

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
