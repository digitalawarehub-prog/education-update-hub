"""Uttarakhand PSC/SSSC recruitment adapter."""
from .base import BaseAdapter


class UKAdapter(BaseAdapter):
    UKSSSC_URL="https://sssc.uk.gov.in/recruitment-notification/"
    UKPSC_URL="https://psc.uk.gov.in/candidate-corner/recruitment"

    def is_recruitment(self,title,url=""):
        t=self.clean(title).lower()
        if any(x in t for x in ("answer key","result","admit card","document verification","cancellation","exam postponed","syllabus","preference","driving test")): return False
        return any(x in t for x in ("विज्ञापन","भर्ती","रिक्त पद","सीधी भर्ती","recruitment","notification","advertisement","vacancy","online application","आवेदन"))

    def _collect(self,url,department):
        soup=self.soup(url)
        if soup is None:return []
        jobs=[]
        for a in soup.find_all("a",href=True):
            title=self.clean(a.get_text(" ",strip=True)); href=self.absolute(url,a.get("href"))
            if not title or not href or not self.is_recruitment(title,href): continue
            job=self.build_job(title,href,department,"Latest Jobs")
            # UKSSSC links commonly point directly to the official PDF/document.
            if href.lower().endswith(".pdf") or "/document/" in href.lower(): job["notification_pdf"]=href
            jobs.append(job)
        return jobs

    def scrape(self,source=None):
        name=str((source or {}).get("name","")).lower()
        if name=="ukpsc": jobs=self._collect(self.UKPSC_URL,"UKPSC")
        elif name=="uksssc": jobs=self._collect(self.UKSSSC_URL,"UKSSSC")
        else: jobs=self._collect(self.UKPSC_URL,"UKPSC")+self._collect(self.UKSSSC_URL,"UKSSSC")
        return self.remove_duplicates(jobs)
