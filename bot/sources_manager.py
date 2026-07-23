"""
Source Manager
--------------
यह तय करता है कि किस वेबसाइट को किस तरीके से पढ़ना है।
"""

from config import SOURCES


class SourceManager:

    def __init__(self):
        self.sources = SOURCES

    def get_all_sources(self):
        return self.sources

    def get_html_sources(self):
        """HTML वेबसाइटें"""
        return [
            s for s in self.sources
            if s.get("type", "html") == "html"
        ]

    def get_rss_sources(self):
        """RSS स्रोत"""
        return [
            s for s in self.sources
            if s.get("type") == "rss"
        ]

    def get_pdf_sources(self):
        """PDF आधारित नोटिफिकेशन"""
        return [
            s for s in self.sources
            if s.get("type") == "pdf"
        ]

    def get_source(self, name):
        """नाम से स्रोत खोजें"""
        for source in self.sources:
            if source["name"].lower() == name.lower():
                return source
        return None

    def count(self):
        return len(self.sources)
