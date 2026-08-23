"""Production source manager with source-library support and scheduling tiers."""
import json
from pathlib import Path
from datetime import datetime, timedelta
from config import SOURCES as CORE_SOURCES

ROOT=Path(__file__).resolve().parent
LIBRARY=ROOT / "sources.json"

class SourceManager:
    def __init__(self):
        core=[dict(s) for s in CORE_SOURCES if s.get("enabled", True)]
        library=[]
        try:
            data=json.loads(LIBRARY.read_text(encoding="utf-8"))
            if isinstance(data,list): library=[dict(s) for s in data if s.get("enabled", True)]
        except Exception:
            library=[]
        merged={}
        for s in library + core:
            sid=str(s.get("id") or s.get("name") or s.get("url") or "").strip().lower()
            if not sid: continue
            s["id"]=sid
            merged[sid]=s
        self.sources=list(merged.values())
        core_ids={str(s.get("id") or s.get("name") or "").strip().lower() for s in core}
        for s in self.sources:
            sid=str(s.get("id","")).lower()
            s.setdefault("tier", "core" if sid in core_ids else "extended")
            s.setdefault("interval_minutes", 30 if s["tier"]=="core" else 120)

    def get_all_sources(self): return self.sources
    def get_html_sources(self): return [s for s in self.sources if s.get("type","html")=="html"]
    def get_rss_sources(self): return [s for s in self.sources if s.get("type")=="rss"]
    def get_pdf_sources(self): return [s for s in self.sources if s.get("type")=="pdf"]
    def get_source(self,name):
        name=str(name or "").strip().lower()
        return next((s for s in self.sources if str(s.get("name","")).lower()==name or str(s.get("id","")).lower()==name),None)
    def count(self): return len(self.sources)

    def get_due_sources(self, force_all=False):
        """Return sources due for this 30-minute workflow.

        Core sources (IBPS/SBI/SSC/UPSC/UK/Railway) run every cycle. The
        wider official-source library is staggered to reduce load while still
        covering the full source set automatically.
        """
        if force_all: return self.get_html_sources()
        state_file=ROOT.parent / "database" / "source_state.json"
        try: state=json.loads(state_file.read_text(encoding="utf8")) if state_file.exists() else {}
        except Exception: state={}
        now=datetime.now()
        due=[]
        for src in self.get_html_sources():
            sid=str(src.get("id") or src.get("name") or src.get("url"))
            last=state.get(sid)
            interval=int(src.get("interval_minutes",120) or 120)
            if str(src.get("tier","extended")).lower()=="core" or not last:
                due.append(src); continue
            try:
                if now-datetime.fromisoformat(last) >= timedelta(minutes=interval): due.append(src)
            except Exception:
                due.append(src)
        return due

    def mark_scraped(self, sources):
        state_file=ROOT.parent / "database" / "source_state.json"
        try: state=json.loads(state_file.read_text(encoding="utf8")) if state_file.exists() else {}
        except Exception: state={}
        stamp=datetime.now().isoformat()
        for src in sources or []:
            sid=str(src.get("id") or src.get("name") or src.get("url"))
            state[sid]=stamp
        state_file.parent.mkdir(parents=True,exist_ok=True)
        state_file.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding="utf8")
