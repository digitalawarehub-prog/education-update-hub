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
        if len(t) < 8: return False
        if any(x in t for x in ("view all", "view more", "read more", "click here", "home", "menu")): return False
        return super().is_valid_notification(title, url)

    def scrape(self, source=None):
        source = source or {}
        soup = self.soup(source.get("url", ""))
        if soup is None: return []
        jobs = []
        for a in soup.find_all("a", href=True):
            title = self.clean(a.get_text(" ", strip=True))
            href = self.absolute(source.get("url", ""), a.get("href"))
            if not title or not href or not self.is_valid_notification(title, href): continue
            jobs.append(self.build_job(title, href, source.get("department", "Government"), self.detect_category(title)))
        return self.enrich_and_filter(jobs)

    def validate(self): return True
    @property
    def name(self): return "GenericAdapter"
