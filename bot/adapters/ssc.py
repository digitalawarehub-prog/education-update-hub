"""
=========================================================
Education Update Hub
Production SSC Adapter
Phase 1 - Part 1
=========================================================
"""

from .base import BaseAdapter


class SSCAdapter(BaseAdapter):

    SSC_URL = (
        "https://ssc.gov.in/"
    )

    NOTICE_URL = (
        "https://ssc.gov.in/rhq-selection-post/rhq-post-details"
    )

    def scrape(self, source=None):

        jobs = []

        jobs.extend(
            self.scrape_notices()
        )

        return jobs


    # =====================================================
    # SSC Notices
    # =====================================================

    def scrape_notices(self):

        soup = self.soup(
            self.SSC_URL
        )

        if soup is None:
            return []

        jobs = []

        links = soup.find_all(
            "a",
            href=True
        )

        for link in links:

            title = self.clean(

                link.get_text(
                    " ",
                    strip=True
                )

            )

            href = self.absolute(
                self.SSC_URL,
                link["href"]
            )

            if not title:
                continue

            if not href:
                continue

            if not self.is_job_link(title):
                continue

            jobs.append(

                self.build_job(

                    title=title,

                    url=href,

                    department="SSC",

                    category="Latest Jobs"

                )

            )

        return jobs
        # =====================================================
    # SSC Notification Filter
    # =====================================================

    def is_valid_notification(
        self,
        title,
        url
    ):

        text = (
            f"{title} {url}"
        ).lower()

        ignore = [

            "login",
            "contact",
            "about",
            "privacy",
            "feedback",
            "gallery",
            "chairman",
            "commission",
            "faq",
            "help",
            "tender",
            "notice inviting tender",
            "website policy",
            "accessibility"

        ]

        for word in ignore:

            if word in text:

                return False

        keywords = [

            "recruitment",
            "notification",
            "vacancy",
            "advertisement",
            "advt",
            "exam",
            "selection post",
            "cgl",
            "chsl",
            "mts",
            "gd",
            "cpo",
            "stenographer",
            "je",
            "jr hindi translator",
            "scientific assistant",
            "phase"

        ]

        return any(

            key in text

            for key in keywords

        )


    # =====================================================
    # Category Detection
    # =====================================================

    def detect_category(self, title):

        title = title.lower()

        if "admit card" in title:

            return "Admit Card"

        if "answer key" in title:

            return "Answer Key"

        if "result" in title:

            return "Result"

        if "syllabus" in title:

            return "Syllabus"

        return "Latest Jobs"


    # =====================================================
    # Remove Duplicate Jobs
    # =====================================================

    def remove_duplicates(
        self,
        jobs
    ):

        unique = []

        seen = set()

        for job in jobs:

            key = (

                job["title"].lower(),

                job["url"]

            )

            if key in seen:

                continue

            seen.add(key)

            unique.append(job)

        return unique
        # =====================================================
    # Build Jobs
    # =====================================================

    def build_jobs(self, links):

        jobs = []

        for title, href in links:

            title = self.clean(title)

            href = self.clean(href)

            if not title or not href:
                continue

            if not self.is_valid_notification(
                title,
                href
            ):
                continue

            jobs.append(

                self.build_job(

                    title=title,

                    url=href,

                    department="SSC",

                    category=self.detect_category(title)

                )

            )

        return self.remove_duplicates(jobs)


    # =====================================================
    # Enrich Jobs
    # =====================================================

    def enrich_jobs(self, jobs):

        enriched = []

        for job in jobs:

            try:

                enriched.append(
                    self.enrich_job(job)
                )

            except Exception:

                enriched.append(job)

        return enriched


    # =====================================================
    # Final Scraper
    # =====================================================

    def scrape(self, source=None):

        jobs = self.scrape_notices()

        jobs = self.remove_duplicates(
            jobs
        )

        jobs = self.enrich_jobs(
            jobs
        )

        return jobs
