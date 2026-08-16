"""Generic fallback adapter for a live recruitment page."""
from .base import BaseAdapter


class GenericAdapter(BaseAdapter):
    def detect_category(self, title):
        from filters import classify_post
        return classify_post(title, "") or "Recruitment"

    def is_valid_notification(self, title, url=""):
        from filters import allow_job
        return allow_job(title, url)

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
