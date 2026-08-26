"""Source selection with bounded rotating batches."""
import os, time
from config import SOURCES

class SourceManager:
    def __init__(self):
        self.sources=[dict(s) for s in SOURCES if s.get("enabled",True)]
    def get_all_sources(self): return self.sources
    def get_html_sources(self): return [s for s in self.sources if s.get("type","html")=="html"]
    def get_rss_sources(self): return [s for s in self.sources if s.get("type")=="rss"]
    def get_pdf_sources(self): return [s for s in self.sources if s.get("type")=="pdf"]
    def get_source(self,name):
        for s in self.sources:
            if str(s.get("name","")).casefold()==str(name).casefold(): return s
        return None
    def count(self): return len(self.sources)
    def get_run_sources(self,batch_size=None):
        try: n=max(1,int(batch_size or os.getenv("EHU_SOURCE_BATCH_SIZE","40")))
        except Exception: n=40
        sources=list(self.sources)
        if not sources: return []
        # Keep high-value sources in every run when present.
        core_terms=("upsc","ssc","ibps","sbi","rbi","ukpsc","uksssc","railway","rrb")
        core=[]; rest=[]
        for s in sources:
            name=str(s.get("name","")).casefold()
            if any(t in name for t in core_terms): core.append(s)
            else: rest.append(s)
        core=core[:n]
        remaining=max(0,n-len(core))
        if not rest or remaining<=0: return core[:n]
        slot=int(time.time()//1800)
        start=(slot*remaining)%len(rest)
        rotated=[rest[(start+i)%len(rest)] for i in range(len(rest))]
        return core+rotated[:remaining]
