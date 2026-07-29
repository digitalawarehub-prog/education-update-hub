"""
=========================================================
Education Update Hub
Production Generic Adapter
Part 1
=========================================================
"""

from .base import BaseAdapter


class GenericAdapter(BaseAdapter):

    def scrape(self, source):

        if not source.get("url"):
            return []

        return self.scrape_site(source)


    # =====================================================
    # Generic Site Scraper
    # =====================================================

    def scrape_site(self, source):

        soup = self.soup(source["url"])

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
                source["url"],
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

                    department=source.get(
                        "department",
                        "Government"
                    ),

                    category=source.get(
                        "category",
                        "Latest Jobs"
                    )

                )

            )

        return jobs
        # =====================================================
    # Generic Notification Filter
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
            "member",
            "committee",
            "login",
            "register",
            "help",
            "faq",
            "tender",
            "accessibility",
            "site map"

        ]

        if any(word in text for word in ignore):
            return False

        keywords = [

            "recruitment",
            "vacancy",
            "notification",
            "advertisement",
            "advt",
            "exam",
            "result",
            "answer key",
            "admit card",
            "hall ticket",
            "call letter",
            "syllabus",
            "interview",
            "merit list",
            "selection list",
            "apply",
            "online application"

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

        if "hall ticket" in title:
            return "Admit Card"

        if "call letter" in title:
            return "Admit Card"

        if "result" in title:
            return "Result"

        if "answer key" in title:
            return "Answer Key"

        if "syllabus" in title:
            return "Syllabus"

        if "interview" in title:
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
    # Build Generic Jobs
    # =====================================================

    def build_jobs(
        self,
        links,
        source
    ):

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

                    department=source.get(
                        "department",
                        "Government"
                    ),

                    category=self.detect_category(
                        title
                    )

                )

            )

        return self.remove_duplicates(
            jobs
        )


    # =====================================================
    # Enrich Generic Jobs
    # =====================================================

    def enrich_jobs(
        self,
        jobs
    ):

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
    # Final Generic Scraper
    # =====================================================

    def scrape(
        self,
        source
    ):

        jobs = []

        try:

            jobs.extend(
                self.scrape_site(
                    source
                )
            )

        except Exception as e:

            print(
                f"Generic Adapter Error: {e}"
            )

        jobs = self.remove_duplicates(
            jobs
        )

        jobs = self.enrich_jobs(
            jobs
        )

        return jobs
