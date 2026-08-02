"""
=========================================================
Education Update Hub
Production Generic Adapter
Version 4.0
=========================================================
"""

from .base import BaseAdapter


class GenericAdapter(BaseAdapter):

    # =====================================================
    # Clean Text
    # =====================================================

    def clean(self, text):

        if text is None:
            return ""

        text = str(text)

        text = " ".join(text.split())

        return text.strip()

    # =====================================================
    # Generic Site Scraper
    # =====================================================

    def scrape_site(self, source):

        soup = self.soup(source["url"])

        if soup is None:
            return []

        jobs = []

        main = (
            soup.find("article")
            or soup.find("main")
            or soup.find("div", class_="content")
            or soup.find("div", class_="container")
            or soup.find("body")
        )

        if not main:
            return []

        for link in main.find_all("a", href=True):

            title = self.clean(
                link.get_text(" ", strip=True)
            )

            href = self.absolute(
                source["url"],
                link.get("href", "")
            )

            if not title or not href:
                continue

            title_lower = title.lower()

            if (
                "{{" in title
                or "}}" in title
                or "translate" in title_lower
            ):
                continue

            if len(title) < 6:
                continue

            if (
                href.lower().startswith("javascript")
                or href.lower().startswith("mailto:")
                or href.lower().endswith(".pdf")
            ):
                continue

            if href.startswith("#"):
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

        return jobs
# =====================================================
    # Generic Notification Filter
    # =====================================================

    def is_valid_notification(
        self,
        title,
        url
    ):

        title = self.clean(title)
        text = f"{title} {url}".lower()

        # Empty
        if not title:
            return False

        # Template / Angular / Jinja
        if (
            "{{" in title
            or "}}" in title
            or "translate" in text
        ):
            return False

        # Very Short
        if len(title) < 6:
            return False

        # Ignore Junk Pages
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
            "site map",
            "notification board",
            "notifications notices",
            "work recruitments",
            "watch this video",
            "image gallery",
            "photo gallery",
            "copyright"

        ]

        if any(word in text for word in ignore):
            return False

        # Valid Updates
        keywords = [

            "recruitment",
            "vacancy",
            "notification",
            "advertisement",
            "advt",

            "apply",
            "apply online",
            "online application",

            "result",
            "merit list",
            "selection list",
            "score card",

            "answer key",

            "admit card",
            "hall ticket",
            "call letter",

            "exam",

            "syllabus",

            "scholarship",

            "interview",

            "walk in",

            "document verification"

        ]

        return any(
            keyword in text
            for keyword in keywords
        )
# =====================================================
    # Category Detection
    # =====================================================

    def detect_category(
        self,
        title
    ):

        title = self.clean(title).lower()

        # Admit Card
        if any(x in title for x in [
            "admit card",
            "hall ticket",
            "call letter",
            "e-admit card"
        ]):
            return "Admit Card"

        # Results
        if any(x in title for x in [
            "result",
            "results",
            "merit list",
            "selection list",
            "score card",
            "final result",
            "provisional result"
        ]):
            return "Results"

        # Answer Key
        if any(x in title for x in [
            "answer key",
            "provisional answer key",
            "final answer key",
            "response sheet"
        ]):
            return "Answer Key"

        # Syllabus
        if any(x in title for x in [
            "syllabus",
            "exam pattern",
            "scheme of examination"
        ]):
            return "Syllabus"

        # Scholarship
        if any(x in title for x in [
            "scholarship",
            "fellowship",
            "stipend"
        ]):
            return "Scholarship"

        # Government Schemes
        if any(x in title for x in [
            "scheme",
            "yojana",
            "yojna"
        ]):
            return "Government Schemes"

        # Recruitment / Jobs
        if any(x in title for x in [
            "recruitment",
            "vacancy",
            "notification",
            "advertisement",
            "advt",
            "apply",
            "walk in interview",
            "engagement",
            "appointment",
            "posts"
        ]):
            return "Latest Jobs"

        # Default
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

            title = self.clean(
                job.get("title", "")
            ).lower()

            url = job.get(
                "url",
                ""
            ).strip().lower()

            if not title or not url:
                continue

            key = (title, url)

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

            href = self.absolute(
                source["url"],
                href
            )

            if not title or not href:
                continue

            if not self.is_valid_notification(
                title,
                href
            ):
                continue

            job = self.build_job(

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

            jobs.append(job)

        return self.remove_duplicates(jobs)
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

                job = self.enrich_job(job)

                # Ensure important links
                if not job.get("apply_link"):
                    job["apply_link"] = job.get("url", "")

                if not job.get("notification_pdf"):
                    job["notification_pdf"] = job.get("url", "")

                if not job.get("official_website"):
                    job["official_website"] = job.get("url", "")

                enriched.append(job)

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

        if not source.get("url"):
            return []

        jobs = self.scrape_site(source)

        jobs = self.remove_duplicates(jobs)

        jobs = self.enrich_jobs(jobs)

        return jobs
# =====================================================
    # Health Check
    # =====================================================

    def validate(self):

        return True


    # =====================================================
    # Adapter Name
    # =====================================================

    @property
    def name(self):

        return "GenericAdapter"
