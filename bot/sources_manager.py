"""Robust source manager for Education Update Hub.

The repository may keep sources in config.SOURCES OR in sources.json.
This module supports both layouts so a missing SOURCES export in config.py
cannot stop the entire GitHub Actions workflow.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

log = logging.getLogger("SourceManager")
ROOT = Path(__file__).resolve().parent.parent
BOT_DIR = Path(__file__).resolve().parent


def _load_sources():
    try:
        from config import SOURCES as configured_sources
        if configured_sources:
            return [dict(s) for s in configured_sources if isinstance(s, dict)]
    except (ImportError, AttributeError):
        log.warning("config.SOURCES not found; loading sources.json instead.")

    for path in (BOT_DIR / "sources.json", ROOT / "sources.json"):
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return [dict(s) for s in data if isinstance(s, dict)]
        except Exception:
            log.exception("Could not load source file: %s", path)

    return []


class SourceManager:
    def __init__(self):
        all_sources = _load_sources()
        self.sources = [s for s in all_sources if s.get("enabled", True)]
        log.info("Loaded %d enabled sources.", len(self.sources))

    def get_all_sources(self):
        return list(self.sources)

    def get_html_sources(self):
        return [s for s in self.sources if s.get("type", "html") == "html"]

    def get_rss_sources(self):
        return [s for s in self.sources if s.get("type") == "rss"]

    def get_pdf_sources(self):
        return [s for s in self.sources if s.get("type") == "pdf"]

    def get_source(self, name):
        name = str(name or "").strip().casefold()
        return next(
            (s for s in self.sources if str(s.get("name", "")).strip().casefold() == name),
            None,
        )

    def count(self):
        return len(self.sources)
