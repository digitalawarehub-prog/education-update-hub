"""Production source manager backed by bot/sources.json.

The JSON file is the single source of truth. config.SOURCES is retained only
as a legacy fallback for installations that do not yet have sources.json.
"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SOURCE_FILE = BASE_DIR / "sources.json"


class SourceManager:
    def __init__(self):
        self.sources = self._load()

    def _load(self):
        data = []
        try:
            with SOURCE_FILE.open("r", encoding="utf-8") as fh:
                raw = json.load(fh)
            if isinstance(raw, list):
                data = [dict(s) for s in raw if isinstance(s, dict) and s.get("enabled", True)]
        except Exception:
            data = []
        if not data:
            try:
                from config import SOURCES
                data = [dict(s) for s in SOURCES if s.get("enabled", True)]
            except Exception:
                data = []
        # De-duplicate by stable source id/name/url while preserving JSON order.
        seen, out = set(), []
        for s in data:
            key = str(s.get("id") or s.get("name") or s.get("url") or "").strip().casefold()
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(s)
        return out

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
