"""Other State Public Service Commission recruitment adapter."""
from .base import BaseAdapter


class PSCAdapter(BaseAdapter):
    PSC_SITES={
        "RPSC":"https://rpsc.rajasthan.gov.in/",
        "UPPSC":"https://uppsc.up.nic.in/",
        "BPSC":"https://bpsc.bihar.gov.in/",
        "MPPSC":"https://mppsc.mp.gov.in/",
        "CGPSC":"https://psc.cg.gov.in/",
        "JPSC":"https://www.jpsc.gov.in/",
    }

    def is_recruitment(self,title,url=""):
        t=self.clean(title).lower()
        if any(x in t for x in ("result","answer key","admit card","syllabus","tender","archive","old", "question paper")): return False
        return any(x in t for x in ("recruitment","vacancy","advertisement","notification","apply","online application","posts","civil service","assistant engineer","lecturer","officer","professor"))

    def _collect(self,department,url):
        soup=self.soup(url)
        if soup is None:return []
        jobs=[]
        for a in soup.find_all("a",href=True):
            title=self.clean(a.get_text(" ",strip=True)); href=self.absolute(url,a.get("href"))
            if not title or not href or not self.is_recruitment(title,href):continue
            jobs.append(self.build_job(title,href,department,"Latest Jobs"))
        return jobs

    def scrape(self,source=None):
        jobs=[]
        for dep,url in self.PSC_SITES.items():
            try: jobs.extend(self._collect(dep,url))
            except Exception: pass
        return self.enrich_and_filter(self.remove_duplicates(jobs))
