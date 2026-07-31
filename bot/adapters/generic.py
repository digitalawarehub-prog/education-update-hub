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

    main = (
        soup.find("article")
        or soup.find("main")
        or soup.find("div", class_="content")
        or soup.find("body")
    )

    if not main:
        return []

    links = main.find_all("a", href=True)

    for link in links:

        title = self.clean(
            link.get_text(" ", strip=True)
        )
        
        # Template/Jinja/Angular text हटाओ
        if (
            "{{" in title
            or "}}" in title
            or "translate" in title.lower()
            or "notifications notices" in title.lower()
            or "work recruitments" in title.lower()
            ):
            continue

        href = self.absolute(
            source["url"],
            link["href"]
        )

        if not title or not href:
            continue

        title_lower = title.lower()
        href_lower = href.lower()

        # Skip template text
        if "{{" in title or "}}" in title:
            continue

        if "translate" in title_lower:
            continue

        # Skip short titles
        if len(title) < 6:
            continue

        # Skip PDF
        if href_lower.endswith(".pdf"):
            continue

        # Skip javascript/mail links
        if href_lower.startswith("javascript"):
            continue

        if href_lower.startswith("mailto:"):
            continue

        if "#" in href:
            continue

        # Skip unwanted pages
        if any(x in title_lower for x in [
            "gallery",
            "photo",
            "video",
            "chairman",
            "member",
            "contact",
            "feedback",
            "privacy",
            "policy",
            "help",
            "login",
            "dashboard",
            "accessibility",
            "notification board",
            "watch this video",
            "notifications notices",
            "work recruitment"
        ]):
            continue

        if not self.is_valid_notification(title, href):
            continue

        jobs.append(

            self.build_job(

                title=title,

                url=href,

                department=source.get(
                    "department",
                    "Government"
                ),

                category=self.detect_category(title)

            )

        )

    return self.remove_duplicates(jobs)
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

            title_lower = title.lower()

            # Skip template strings
            if "{{" in title or "}}" in title:
                continue

            # Skip translate placeholders
            if "translate" in title_lower:
                continue

            # Skip PDF links
            if href.lower().endswith(".pdf"):
                continue

            # Skip obvious junk
            if any(x in title_lower for x in [
                "watch this video",
                "video",
                "gallery",
                "photo",
                "chairman",
                "member",
                "feedback",
                "privacy",
                "policy",
                "contact",
                "help",
                "accessibility",
                "notifications notices",
                "work recruitment"
            ]):
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
