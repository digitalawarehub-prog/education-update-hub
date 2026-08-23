"""Railway RRB/RRC live recruitment adapter."""
from .base import BaseAdapter


class RailwayAdapter(BaseAdapter):
    RRB_URL="https://www.rrbcdg.gov.in/"
    RRC_URL="https://rrcrail.in/"

    def is_recruitment(self,title,url=""):
        t=self.clean(title).lower()
        if any(x in t for x in ("answer key","result","admit card","city intimation","exam responses","mock test","status of application","corrigendum-4","corrigendum-3")): return False
        return any(x in t for x in ("cen", "centralised employment notice", "recruitment", "vacancy", "assistant loco pilot", "technician", "ntpc", "group-d", "group d", "application link", "employment notice"))

    def _collect(self,url,department):
        soup=self.soup(url)
        if soup is None:return []
        jobs=[]
        for a in soup.find_all("a",href=True):
            title=self.clean(a.get_text(" ",strip=True)); href=self.absolute(url,a.get("href"))
            if not title or not href or not self.is_recruitment(title,href): continue
            jobs.append(self.build_job(title,href,department,"Latest Jobs"))
        return jobs

    def scrape(self,source=None):
        jobs=self._collect(self.RRB_URL,"Railway")
        # RRC home is retained as a fallback but only current recruitment links are accepted.
        jobs.extend(self._collect(self.RRC_URL,"Railway"))
        return self.enrich_and_filter(jobs)
