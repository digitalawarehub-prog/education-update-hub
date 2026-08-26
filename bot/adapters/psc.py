"""Public Service Commission adapter: one source at a time."""
from .base import BaseAdapter

class PSCAdapter(BaseAdapter):
    def is_recruitment(self,title,url=""):
        t=self.clean(title).lower()
        if any(x in t for x in ("result","answer key","admit card","syllabus","tender","archive","old","question paper")): return False
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
            jobs.append(self.build_job(title,href,source.get("name","PSC"),source.get("category","Latest Jobs")))
        return self.enrich_and_filter(jobs)
