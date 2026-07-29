"""
=========================================================
Education Update Hub
Production UPSC Adapter
Part 1
=========================================================
"""

from .base import BaseAdapter


class UPSCAdapter(BaseAdapter):

    UPSC_URL = "https://upsc.gov.in/"

    def scrape(self, source=None):

        jobs = []

        jobs.extend(
            self.scrape_recruitments()
        )

        return jobs


    # =====================================================
    # UPSC Recruitment
    # =====================================================

    def scrape_recruitments(self):

        soup = self.soup(
            self.UPSC_URL
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
                self.UPSC_URL,
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

                    department="UPSC",

                    category="Latest Jobs"

                )

            )

        return jobs
        # =====================================================
    # UPSC Notification Filter
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

            "about",
            "contact",
            "privacy",
            "policy",
            "feedback",
            "gallery",
            "photo",
            "video",
            "chairman",
            "commission",
            "tender",
            "login",
            "help",
            "faq",
            "accessibility",
            "site map"

        ]

        if any(word in text for word in ignore):
            return False

        keywords = [

            "recruitment",
            "notification",
            "vacancy",
            "advertisement",
            "exam",
            "examination",
            "nda",
            "cds",
            "capf",
            "cms",
            "engineering services",
            "civil services",
            "forest service",
            "ies",
            "iss",
            "geo-scientist",
            "assistant professor",
            "medical officer",
            "specialist",
            "scientist",
            "apply online"

        ]

        return any(
            word in text
            for word in keywords
        )


    # =====================================================
    # Category Detection
    # =====================================================

    def detect_category(
        self,
        title
    ):

        title = title.lower()

        if "admit card" in title:
            return "Admit Card"

        if "e-admit card" in title:
            return "Admit Card"

        if "result" in title:
            return "Result"

        if "answer key" in title:
            return "Answer Key"

        if "syllabus" in title:
            return "Syllabus"

        if "interview schedule" in title:
            return "Interview"

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
    # Build UPSC Jobs
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

                    department="UPSC",

                    category=self.detect_category(title)

                )

            )

        return self.remove_duplicates(jobs)


    # =====================================================
    # Enrich UPSC Jobs
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
    # Final UPSC Scraper
    # =====================================================

    def scrape(self, source=None):

        jobs = []

        try:

            jobs.extend(
                self.scrape_recruitments()
            )

        except Exception as e:

            print(
                f"UPSC Error: {e}"
            )

        jobs = self.remove_duplicates(
            jobs
        )

        jobs = self.enrich_jobs(
            jobs
        )

        return jobs
