"""Source registry and rotating batch selection."""
from __future__ import annotations
import json
from pathlib import Path
from config import SITE_URL

ROOT=Path(__file__).resolve().parent
SOURCE_FILE=ROOT/"sources.json"
STATE_FILE=ROOT/"source_rotation.json"

PRIORITY_NAMES={"UPSC","SSC","IBPS","UKPSC","UKSSSC","SBI Careers","Reserve Bank of India"}

class SourceManager:
    def __init__(self):
        self.sources=self._load()
    def _load(self):
        try:
            data=json.loads(SOURCE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
        return [dict(s) for s in data if isinstance(s,dict) and s.get("enabled",True)]
    def get_all_sources(self): return list(self.sources)
    def get_html_sources(self): return [s for s in self.sources if s.get("type","html")=="html"]
    def get_rss_sources(self): return [s for s in self.sources if s.get("type")=="rss"]
    def get_pdf_sources(self): return [s for s in self.sources if s.get("type")=="pdf"]
    def get_source(self,name):
        n=str(name or "").strip().casefold()
        return next((s for s in self.sources if str(s.get("name","")).strip().casefold()==n),None)
    def count(self): return len(self.sources)
    def _state(self):
        try:
            d=json.loads(STATE_FILE.read_text(encoding="utf-8"))
            return int(d.get("offset",0))
        except Exception:
            return 0
    def _save_state(self,offset):
        STATE_FILE.write_text(json.dumps({"offset":int(offset)},indent=2),encoding="utf-8")
    def get_run_sources(self,batch_size=40):
        src=self.get_html_sources()
        if not src: return []
        batch_size=max(1,int(batch_size))
        priority=[]; rest=[]
        for s in src:
            if str(s.get("name","")).strip() in PRIORITY_NAMES:
                priority.append(s)
            else: rest.append(s)
        wanted=max(0,batch_size-len(priority))
        offset=self._state()%len(rest) if rest else 0
        picked=[]
        if rest and wanted:
            for i in range(min(wanted,len(rest))): picked.append(rest[(offset+i)%len(rest)])
            self._save_state((offset+wanted)%len(rest))
        result=[]; seen=set()
        for s in priority+picked:
            sid=s.get("id") or s.get("name")
            if sid in seen: continue
            seen.add(sid); result.append(s)
        return result
