"""Production source manager. Loads the canonical 284-source JSON and selects a bounded rotating batch."""
import json
import os
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SOURCES_FILE = ROOT_DIR / "bot" / "sources.json"

class SourceManager:
    def __init__(self, sources_file=None):
        self.sources_file = Path(sources_file or SOURCES_FILE)
        self.sources = self._load()

    def _load(self):
        try:
            data = json.loads(self.sources_file.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                raise ValueError("sources.json must contain a list")
            return [dict(s) for s in data if isinstance(s, dict) and s.get("enabled", True)]
        except Exception as exc:
            print(f"SourceManager: failed to load {self.sources_file}: {exc}")
            return []

    def get_all_sources(self): return list(self.sources)
    def get_html_sources(self): return [s for s in self.sources if s.get("type", "html") == "html"]
    def get_rss_sources(self): return [s for s in self.sources if s.get("type") == "rss"]
    def get_pdf_sources(self): return [s for s in self.sources if s.get("type") == "pdf"]
    def get_source(self, name):
        for s in self.sources:
            if str(s.get("name", "")).casefold() == str(name).casefold(): return s
        return None
    def count(self): return len(self.sources)

    def get_run_sources(self, batch_size=None):
        try:
            n=max(1,int(batch_size or os.getenv("EHU_SOURCE_BATCH_SIZE","80")))
        except Exception:
            n=80
        sources=self.get_html_sources()
        if not sources: return []
        if n >= len(sources): return sources

        # Keep high-value national/state sources in every run when present.
        core_terms=("upsc","ssc","ibps","sbi","rbi","ukpsc","uksssc","railway","rrb")
        core=[]; rest=[]
        for source in sources:
            name=str(source.get("name","")).casefold()
            if any(term in name for term in core_terms): core.append(source)
            else: rest.append(source)
        core=core[:min(n, len(core))]
        remaining=n-len(core)
        if remaining <= 0: return core[:n]

        # Stable 30-minute rotation; no external state file is required.
        slot=int(time.time() // (max(1,int(os.getenv("EHU_SOURCE_ROTATION_MINUTES","30"))) * 60))
        start=(slot*remaining) % len(rest)
        rotated=[rest[(start+i)%len(rest)] for i in range(len(rest))]
        return core + rotated[:remaining]
