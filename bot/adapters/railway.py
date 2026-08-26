"""Railway adapter using the configured RRB/RRC source only."""
from .base import BaseAdapter

class RailwayAdapter(BaseAdapter):
    def is_recruitment(self,title,url=""):
        t=self.clean(title).lower()
        if any(x in t for x in ("answer key","result","admit card","city intimation","exam responses","mock test","status of application")): return False
        return self.is_valid_notification(title,url)
    def scrape(self,source=None):
        source=source or {}
        url=str(source.get("url") or "").strip()
        if not url: return []
        soup=self.soup(url)
        if soup is None: return []
        jobs=[]
        for a in soup.find_all("a",href=True):
            title=self.clean(a.get_text(" ",strip=True)); href=self.absolute(url,a.get("href"))
            if not title or not href or not self.is_recruitment(title,href): continue
            jobs.append(self.build_job(title,href,source.get("name","Railway"),source.get("category","Railway")))
        return self.enrich_and_filter(jobs)
