"""Other State Public Service Commission recruitment adapter."""
from .base import BaseAdapter
import logging
logger=logging.getLogger(__name__)


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
        # Each source entry represents one PSC. The previous implementation
        # ignored the selected source and scraped all six PSC sites every time,
        # causing massive duplication and unnecessary timeouts.
        source = source or {}
        name = str(source.get("name", "")).strip().upper()
        url = str(source.get("url", "")).strip()
        dep = name if name in self.PSC_SITES else str(source.get("department") or name or "PSC")
        if not url:
            url = self.PSC_SITES.get(name, "")
        try:
            return self.enrich_and_filter(self._collect(dep, url))
        except Exception:
            logger.exception("PSC scrape failed | %s", name)
            return []
