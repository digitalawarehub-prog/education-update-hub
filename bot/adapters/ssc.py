"""SSC live Notice Board adapter.
Only recruitment/application notices are emitted; results, answer keys and old archive items are ignored.
"""
from .base import BaseAdapter


class SSCAdapter(BaseAdapter):
    SSC_URL = "https://ssc.gov.in/"

    def is_recruitment(self, title):
        t = self.clean(title).lower()
        return any(k in t for k in (
            "recruitment", "selection post", "online application",
            "application invited", "constable", "stenographer",
            "junior engineer", "combined graduate", "combined higher", "translator",
            "phase-xiv", "phase xiv"
        )) and not any(k in t for k in (
            "answer key", "result", "admit card", "response sheet", "marks", "allocation",
            "tentative answer", "exam date", "exam schedule"
        ))

    def scrape(self, source=None):
        soup = self.soup(self.SSC_URL)
        if soup is None: return []
        jobs=[]
        # SSC home currently exposes the live Notice Board; do not crawl pagination/archive pages.
        for a in soup.find_all("a", href=True):
            title=self.clean(a.get_text(" ", strip=True))
            href=self.absolute(self.SSC_URL,a.get("href"))
            if not title or not href or not self.is_recruitment(title): continue
            jobs.append(self.build_job(title,href,"SSC","Latest Jobs"))
        return self.enrich_and_filter(self.remove_duplicates(jobs))
