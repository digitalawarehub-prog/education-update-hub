"""
=========================================================
Education Update Hub
Production Railway Adapter
Phase 1 - Part 1
=========================================================
"""

from .base import BaseAdapter


class RailwayAdapter(BaseAdapter):

    RRB_URL = "https://www.rrbcdg.gov.in/"
    RRC_URL = "https://rrcrail.in/"

    def scrape(self, source=None):

        jobs = []

        jobs.extend(
            self.scrape_rrb()
        )

        jobs.extend(
            self.scrape_rrc()
        )

        return jobs


    # =====================================================
    # RRB Recruitment
    # =====================================================

    def scrape_rrb(self):

        soup = self.soup(
            self.RRB_URL
        )

        if soup is None:
            return []

        jobs = []

        links=soup.select(
        ".table a,.content a"
        )

        for link in links:

            title = self.clean(
                link.get_text(
                    " ",
                    strip=True
                )
            )

            href = self.absolute(
                self.RRB_URL,
                link["href"]
            )
            if "{{" in title:
                continue
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

                    department="Railway",

                    category="Latest Jobs"

                )

            )

        return jobs
        # =====================================================
    # RRC Recruitment
    # =====================================================

    def scrape_rrc(self):

        soup = self.soup(
            self.RRC_URL
        )

        if soup is None:
            return []

        jobs = []

        seen = set()

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
                self.RRC_URL,
                link["href"]
            )

            if not title or not href:
                continue

            if href in seen:
                continue

            seen.add(href)

            if not self.is_valid_notification(
                title,
                href
            ):
                continue

            jobs.append(

                self.build_job(

                    title=title,

                    url=href,

                    department="Railway",

                    category=self.detect_category(title)

                )

            )

        return jobs


    # =====================================================
    # Railway Notification Filter
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

            "contact",
            "about",
            "privacy",
            "feedback",
            "gallery",
            "tender",
            "help",
            "faq",
            "login",
            "chairman",
            "policy",
            "accessibility"

        ]

        if any(word in text for word in ignore):
            return False

        keywords = [

            "cen",
            "recruitment",
            "notification",
            "vacancy",
            "rrb",
            "rrc",
            "alp",
            "technician",
            "ntpc",
            "group d",
            "paramedical",
            "ministerial",
            "je",
            "assistant loco pilot",
            "apply"

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
    # Build Railway Jobs
    # =====================================================

    def build_jobs(self, links, department):

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

                    department=department,

                    category=self.detect_category(title)

                )

            )

        return self.remove_duplicates(jobs)


    # =====================================================
    # Enrich Railway Jobs
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
    # Final Railway Scraper
    # =====================================================

    def scrape(self, source=None):

        jobs = []

        try:

            jobs.extend(
                self.scrape_rrb()
            )

        except Exception:

            pass

        try:

            jobs.extend(
                self.scrape_rrc()
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
