"""IBPS home page adapter for current Recent Updates and Other Ongoing Recruitments."""
from .base import BaseAdapter


class IBPSAdapter(BaseAdapter):
    IBPS_URL="https://www.ibps.in/"

    def is_recruitment(self,title,url=""):
        t=self.clean(title).lower()
        if any(x in t for x in ("tender","privacy","contact","faq","mock test","calendar")): return False
        return any(x in t for x in ("crp","recruitment","registration from","application for the post","recruitment of","officers","assistant", "manager"))

    def scrape(self, source=None):
        soup=self.soup(self.IBPS_URL)
        if soup is None: return []
        jobs=[]
        for a in soup.find_all("a",href=True):
            title=self.clean(a.get_text(" ",strip=True)); href=self.absolute(self.IBPS_URL,a.get("href"))
            if not title or not href or not self.is_recruitment(title,href): continue
            jobs.append(self.build_job(title,href,"IBPS","Latest Jobs"))
        return self.enrich_and_filter(self.remove_duplicates(jobs))
