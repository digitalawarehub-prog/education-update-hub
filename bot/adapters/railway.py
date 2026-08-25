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
        # Scrape only the selected railway zone. The previous code scraped the
        # same RRB Chandigarh + RRC home pages for every one of 27 zone sources.
        source = source or {}
        url = str(source.get("url", "")).strip() or self.RRB_URL
        name = str(source.get("name", "Railway")).strip()
        return self.enrich_and_filter(self._collect(url, name))
