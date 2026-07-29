"""
=========================================================
Education Update Hub
Production UK Adapter
Phase 2 - Part 1
=========================================================
"""

import re

from .base import BaseAdapter


class UKAdapter(BaseAdapter):

    UKSSSC_URL = (
        "https://sssc.uk.gov.in/recruitment-notification/"
    )

    UKPSC_URL = (
        "https://psc.uk.gov.in/recruitment"
    )

    def scrape(self, source):

        jobs = []

        jobs.extend(
            self.scrape_uksssc()
        )

        jobs.extend(
            self.scrape_ukpsc()
        )

        return jobs


    # =====================================================
    # UKSSSC Recruitment
    # =====================================================

    def scrape_uksssc(self):

        soup = self.soup(
            self.UKSSSC_URL
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
                self.UKSSSC_URL,
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

                    department="UKSSSC",

                    category="Latest Jobs"

                )

            )

        return jobs
        # =====================================================
    # UKPSC Recruitment
    # =====================================================

    def scrape_ukpsc(self):

        soup = self.soup(
            self.UKPSC_URL
        )

        if soup is None:
            return []

        jobs = []

        links = soup.find_all(
            "a",
            href=True
        )

        seen = set()

        for link in links:

            title = self.clean(
                link.get_text(
                    " ",
                    strip=True
                )
            )

            href = self.absolute(
                self.UKPSC_URL,
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

                    department="UKPSC",

                    category="Latest Jobs"

                )

            )

        return jobs


    # =====================================================
    # Notification Filter
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

            "accessibility",
            "contact",
            "chairman",
            "member",
            "organisation",
            "organization",
            "gallery",
            "policy",
            "calendar",
            "help",
            "feedback",
            "rti",
            "act",
            "rule",
            "photo",
            "dashboard",
            "home",
            "login"

        ]

        for word in ignore:

            if word in text:
                return False

        keywords = [

            "recruitment",
            "notification",
            "advertisement",
            "advt",
            "vacancy",
            "posts",
            "apply",
            "online application",
            "direct recruitment"

        ]

        return any(
            key in text
            for key in keywords
        )


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
    # Final Scraper
    # =====================================================

    def scrape(self, source=None):

        jobs = []

        # UKSSSC
        try:

            jobs.extend(
                self.scrape_uksssc()
            )

        except Exception:

            pass

        # UKPSC
        try:

            jobs.extend(
                self.scrape_ukpsc()
            )

        except Exception:

            pass

        jobs = self.remove_duplicates(
            jobs
        )

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
    # Build Recruitment List
    # =====================================================

    def build_jobs(
        self,
        links,
        department
    ):

        jobs = []

        seen = set()

        for title, href in links:

            title = self.clean(title)

            href = self.clean(href)

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

                    department=department,

                    category="Latest Jobs"

                )

            )

        return jobs
