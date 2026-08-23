"""Canonical source manager for Education Update Hub."""
import json
from pathlib import Path
from config import SOURCES as FALLBACK_SOURCES
SOURCE_FILE=Path(__file__).resolve().parent/"sources.json"
class SourceManager:
    def __init__(self): self.sources=self._load()
    def _load(self):
        try:
            raw=json.loads(SOURCE_FILE.read_text(encoding="utf-8")); out=[]; seen=set()
            if not isinstance(raw,list): raise ValueError("sources.json must be a list")
            for item in raw:
                if not isinstance(item,dict) or not item.get("name") or not item.get("url"): continue
                key=(str(item["name"]).strip().casefold(),str(item["url"]).strip().casefold())
                if key in seen: continue
                seen.add(key); item=dict(item); item.setdefault("type","html"); item.setdefault("enabled",True); out.append(item)
            if out: return [s for s in out if s.get("enabled",True)]
        except Exception:
            import logging; logging.getLogger(__name__).exception("Canonical source load failed")
        return [dict(s) for s in FALLBACK_SOURCES if s.get("enabled",True)]
    def get_all_sources(self): return self.sources
    def get_html_sources(self): return [s for s in self.sources if s.get("type","html")=="html"]
    def get_rss_sources(self): return [s for s in self.sources if s.get("type")=="rss"]
    def get_pdf_sources(self): return [s for s in self.sources if s.get("type")=="pdf"]
    def get_source(self,name):
        n=str(name or "").strip().casefold(); return next((s for s in self.sources if str(s.get("name","")).strip().casefold()==n),None)
    def count(self): return len(self.sources)
