"""
=========================================================
Education Update Hub
Production IBPS Adapter
Part 1
=========================================================
"""

from .base import BaseAdapter


class IBPSAdapter(BaseAdapter):

    IBPS_URL = "https://www.ibps.in/"

    def scrape(self, source=None):

        jobs = []

        jobs.extend(
            self.scrape_notifications()
        )

        return jobs


    # =====================================================
    # IBPS Notifications
    # =====================================================

    def scrape_notifications(self):

        soup = self.soup(
            self.IBPS_URL
        )

        if soup is None:
            return []

        jobs = []

        links=soup.select(
        ".news a,.content a"
        )

        for link in links:

            title = self.clean(
                link.get_text(
                    " ",
                    strip=True
                )
            )

            href = self.absolute(
                self.IBPS_URL,
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

                    department="IBPS",

                    category="Latest Jobs"

                )

            )

        return jobs
        # =====================================================
    # IBPS Notification Filter
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
            "faq",
            "help",
            "login",
            "career",
            "gallery",
            "archive",
            "tender",
            "accessibility"

        ]

        if any(word in text for word in ignore):
            return False

        keywords = [

            "crp",
            "po",
            "clerk",
            "specialist officer",
            "so",
            "rrb",
            "officer scale",
            "office assistant",
            "csa",
            "recruitment",
            "notification",
            "vacancy",
            "apply online",
            "exam",
            "interview"

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

        if "call letter" in title:
            return "Admit Card"

        if "answer key" in title:
            return "Answer Key"

        if "result" in title:
            return "Result"

        if "score card" in title:
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
    # Build IBPS Jobs
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

                    department="IBPS",

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

        jobs = []

        try:

            jobs.extend(
                self.scrape_notifications()
            )

        except Exception:

            pass

        jobs = self.remove_duplicates(
            jobs
        )

        jobs = self.enrich_jobs(
            jobs
        )

        return jobs
