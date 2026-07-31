"""
=========================================================
Education Update Hub
Production PSC Adapter
Part 1
=========================================================
"""

from .base import BaseAdapter


class PSCAdapter(BaseAdapter):

    PSC_SITES = {

        "UKPSC": "https://psc.uk.gov.in/",
        "RPSC": "https://rpsc.rajasthan.gov.in/",
        "UPPSC": "https://uppsc.up.nic.in/",
        "BPSC": "https://bpsc.bihar.gov.in/",
        "MPPSC": "https://mppsc.mp.gov.in/",
        "CGPSC": "https://psc.cg.gov.in/",
        "JPSC": "https://www.jpsc.gov.in/"

    }


    def scrape(self, source=None):

        jobs = []

        for department, url in self.PSC_SITES.items():

            try:

                jobs.extend(

                    self.scrape_site(
                        department,
                        url
                    )

                )

            except Exception:

                continue

        return jobs


    # =====================================================
    # Generic PSC Scraper
    # =====================================================

    def scrape_site(
        self,
        department,
        base_url
    ):

        soup = self.soup(base_url)

        if soup is None:
            return []

        jobs = []

        table = soup.find("table")

        if table:
            links = table.find_all(
                "a",
                href=True
            )
        else:
            links = soup.select(
                ".content a"
            )

        for link in links:

            title = self.clean(

                link.get_text(
                    " ",
                    strip=True
                )

            )
    title_lower = title.lower()

    if "{{" in title:
        continue

    if "translate" in title_lower:
        continue

    if "%pdf" in title_lower:
        continue

    if len(title) < 6:
        continue

    if any(x in title_lower for x in [
        "chairman",
        "member",
        "setting",
        "font",
        "notification board",
        "help",
        "gallery",
        "contact",
        "privacy",
        "policy",
        "accessibility",
        "dashboard",
        "feedback"
    ]):
        continue

    href = self.absolute(
    base_url,
    link["href"]
    )
            if href == base_url:
                continue

            if "#" in href:
                continue

            if href.lower().startswith("javascript"):
                continue
            # Skip invalid links
            if href == base_url:
                continue

            if "#" in href:
                continue

            if href.lower().startswith("javascript"):
                continue
            if "#" in href:
                continue

            if "javascript" in href.lower():
                continue

            if href == base_url:
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

                    department=department,

                    category="Latest Jobs"

                )

            )

        return jobs
        # =====================================================
    # PSC Notification Filter
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
            "commission",
            "tender",
            "login",
            "help",
            "faq",
            "site map",
            "accessibility"

        ]

        if any(word in text for word in ignore):
            return False

        keywords = [

            "recruitment",
            "vacancy",
            "advertisement",
            "notification",
            "exam",
            "examination",
            "interview",
            "assistant professor",
            "lecturer",
            "medical officer",
            "civil judge",
            "scientific officer",
            "forest",
            "engineering",
            "combined",
            "state service",
            "pcs",
            "assistant engineer",
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

        if "answer key" in title:
            return "Answer Key"

        if "result" in title:
            return "Result"

        if "interview" in title:
            return "Interview"

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
    # Build PSC Jobs
    # =====================================================

    def build_jobs(
        self,
        links,
        department
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

                    department=department,

                    category=self.detect_category(title)

                )

            )

        return self.remove_duplicates(jobs)


    # =====================================================
    # Enrich PSC Jobs
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
    # Final PSC Scraper
    # =====================================================

    def scrape(
        self,
        source=None
    ):

        jobs = []

        for department, url in self.PSC_SITES.items():

            try:

                jobs.extend(

                    self.scrape_site(
                        department,
                        url
                    )

                )

            except Exception as e:

                print(
                    f"{department} Error: {e}"
                )

        jobs = self.remove_duplicates(
            jobs
        )

        jobs = self.enrich_jobs(
            jobs
        )

        return jobs
