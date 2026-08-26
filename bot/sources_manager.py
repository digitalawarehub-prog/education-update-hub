"""
Source Manager
--------------
Controls the production source list and keeps source/adapter mapping explicit.
"""

from config import SOURCES


class SourceManager:

    def __init__(self):
        self.sources = [
            dict(source)
            for source in SOURCES
            if source.get("enabled", True)
        ]

    def get_all_sources(self):
        return self.sources

    def get_html_sources(self):
        """Return enabled HTML sources only."""
        return [
            s for s in self.sources
            if s.get("type", "html") == "html"
        ]

    def get_rss_sources(self):
        return [
            s for s in self.sources
            if s.get("type") == "rss"
        ]

    def get_pdf_sources(self):
        return [
            s for s in self.sources
            if s.get("type") == "pdf"
        ]

    def get_source(self, name):
        """Find an enabled source by name."""
        for source in self.sources:
            if source.get("name", "").lower() == name.lower():
                return source
        return None

    def count(self):
        return len(self.sources)
