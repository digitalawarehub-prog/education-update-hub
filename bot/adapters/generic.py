"""Generic fallback adapter for a live recruitment page."""
from .base import BaseAdapter


class GenericAdapter(BaseAdapter):
    def detect_category(self, title):
        t = self.clean(title).lower()
        if any(x in t for x in ("admit card", "hall ticket", "call letter")): return "Admit Card"
        if "answer key" in t: return "Answer Key"
        if "result" in t or "merit list" in t: return "Result"
        if "syllabus" in t: return "Syllabus"
        if "scholarship" in t: return "Scholarship"
        return "Latest Jobs"

    def is_valid_notification(self, title, url=""):
        t = self.clean(title).lower()
        if len(t) < 8:
            return False

        # Generic adapters scrape homepages, so navigation labels must be
        # rejected explicitly before the positive keyword test.
        bad = (
            "home", "homepage", "view all", "view more", "read more",
            "click here", "menu", "search", "login", "register",
            "registration", "forgot password", "reset password",
            "step-1", "step 1", "download notification",
            "download hindi notification", "download english notification",
            "download guidelines", "vacancy position", "vacancy/nia",
            "recruitment/admission links", "skip to main content",
            "select your language", "website policies", "privacy policy",
        )
        if any(t == x or t.startswith(x + " -") or t.startswith(x + " |") for x in bad):
            return False
        if any(x in t for x in (
            "forgot password", "reset password", "new registration",
            "download notification", "download hindi notification",
            "download english notification", "download guidelines",
            "recruitment/admission links", "skip to main content",
            "vacancy position", "vacancy/nia",
        )):
            return False
        return super().is_valid_notification(title, url)

    def scrape(self, source=None):
        source = source or {}
        soup = self.soup(source.get("url", ""))
        if soup is None: return []
        jobs = []
        source_url = source.get("url", "")
        for a in soup.find_all("a", href=True):
            title = self.clean(a.get_text(" ", strip=True))
            href = self.absolute(source_url, a.get("href"))
            if not title or not href:
                continue
            if not self.is_valid_notification(title, href):
                continue
            jobs.append(self.build_job(title, href, source.get("department", "Government"), self.detect_category(title)))
        return self.enrich_and_filter(jobs)

    def validate(self): return True
    @property
    def name(self): return "GenericAdapter"
