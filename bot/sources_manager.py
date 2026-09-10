"""Production source manager."""
from config import SOURCES


class SourceManager:
    def __init__(self):
        self.sources = [dict(s) for s in SOURCES if s.get("enabled", True)]

    def get_all_sources(self):
        return self.sources

    def get_html_sources(self):
        return [s for s in self.sources if s.get("type", "html") == "html"]

    def get_rss_sources(self):
        return [s for s in self.sources if s.get("type") == "rss"]

    def get_pdf_sources(self):
        return [s for s in self.sources if s.get("type") == "pdf"]

    def get_source(self, name):
        name = str(name or "").strip().lower()
        return next((s for s in self.sources if str(s.get("name", "")).lower() == name), None)

    def count(self):
        return len(self.sources)
