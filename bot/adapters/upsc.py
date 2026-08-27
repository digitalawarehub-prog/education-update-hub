"""UPSC current Recruitment page adapter."""
from .base import BaseAdapter


class UPSCAdapter(BaseAdapter):
    UPSC_URL = "https://www.upsc.gov.in/recruitment/recruitment-advertisement"

    def is_recruitment(self,title,url=""):
        t=self.clean(title).lower()
        if len(t)<8: return False
        if any(x in t for x in ("about","contact","privacy","tender","login","faq","site map","archive")): return False
        return any(x in t for x in ("posts of","post of","recruitment","assistant", "officer", "scientific", "chemist", "director", "medical", "engineer", "professor", "manager"))

    def scrape(self, source=None):
        soup=self.soup(self.UPSC_URL)
        if soup is None: return []
        jobs=[]
        # Page 1 only. UPSC pagination contains historical recruitment cases; never crawl next pages.
        for a in soup.find_all("a", href=True):
            title=self.clean(a.get_text(" ", strip=True))
            href=self.absolute(self.UPSC_URL,a.get("href"))
            if not title or not href or not self.is_recruitment(title,href): continue
            jobs.append(self.build_job(title,href,"UPSC","Latest Jobs"))
        return self.enrich_and_filter(jobs)
