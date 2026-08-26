"""Production source manager with bounded rotating batches."""
import json
import os
from pathlib import Path
from config import SOURCES


class SourceManager:
    CORE_NAMES = {
        "upsc", "ssc", "ibps", "sbi careers", "reserve bank of india",
        "uttarakhand psc", "uksssc"
    }

    def __init__(self):
        self.sources = [dict(s) for s in SOURCES if s.get("enabled", True)]
        self.batch_size = max(1, int(os.getenv("EHU_SOURCE_BATCH_SIZE", "40")))
        self.state_file = Path(__file__).resolve().parent / "generated" / "source_rotation_state.json"

    def get_all_sources(self): return self.sources
    def get_html_sources(self): return [s for s in self.sources if s.get("type", "html") == "html"]
    def get_rss_sources(self): return [s for s in self.sources if s.get("type") == "rss"]
    def get_pdf_sources(self): return [s for s in self.sources if s.get("type") == "pdf"]
    def get_source(self, name):
        for s in self.sources:
            if s.get("name", "").lower() == name.lower(): return s
        return None
    def count(self): return len(self.sources)

    def get_run_sources(self, batch_size=None):
        if batch_size is not None:
            try:
                self.batch_size = max(1, int(batch_size))
            except (TypeError, ValueError):
                pass
        sources = self.get_html_sources()
        if len(sources) <= self.batch_size:
            return sources
        core, rest = [], []
        for s in sources:
            if s.get("name", "").strip().lower() in self.CORE_NAMES:
                core.append(s)
            else:
                rest.append(s)
        core = core[:self.batch_size]
        slots = max(0, self.batch_size - len(core))
        try:
            state = json.loads(self.state_file.read_text(encoding="utf-8")) if self.state_file.exists() else {}
        except Exception:
            state = {}
        offset = int(state.get("offset", 0)) % len(rest) if rest else 0
        selected = rest[offset:offset + slots]
        if len(selected) < slots and rest:
            selected += rest[:slots-len(selected)]
        next_offset = (offset + slots) % len(rest) if rest else 0
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps({"offset": next_offset}, indent=2), encoding="utf-8")
        return core + selected
