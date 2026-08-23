"""IBPS adapter: current CRP updates + Other Ongoing Recruitments."""
from .base import BaseAdapter
import re


class IBPSAdapter(BaseAdapter):
    IBPS_URL = "https://www.ibps.in/"

    EXCLUDE = (
        "call letter", "admit card", "hall ticket", "result", "answer key",
        "tender", "request for proposal", "fraudulent", "caution", "mock test",
        "calendar", "iso 9001", "grievance", "advisory", "sop",
    )

    def _is_recruitment_title(self, text):
        t = self.clean(text).casefold()
        if len(t) < 12 or any(x in t for x in self.EXCLUDE):
            return False
        return any(x in t for x in (
            "recruitment", "registration from", "apply online", "application",
            "notification", "advertisement", "engagement", "vacancy", "crp-",
            "crp ", "online form", "posts of", "post of"
        ))

    def _container(self, a):
        node = a
        for _ in range(6):
            if node is None:
                break
            text = self.clean(node.get_text(" ", strip=True))
            if 20 < len(text) < 3500 and (
                "registration from" in text.casefold() or
                "apply online" in text.casefold() or
                "notification" in text.casefold()
            ):
                return node
            node = getattr(node, "parent", None)
        return a.parent or a

    def _find_pdf(self, container, title):
        candidates = []
        title_tokens = self._title_match_tokens(title)
        for a in container.find_all("a", href=True):
            href = self.absolute(self.IBPS_URL, a.get("href"))
            label = self.clean(a.get_text(" ", strip=True)).casefold()
            if not href or href.startswith("javascript:"):
                continue
            low = href.casefold()
            if not (low.endswith(".pdf") or "pdf" in low or "wp-content/uploads" in low):
                continue
            blob = f"{label} {low}"
            if any(x in blob for x in ("call letter", "result", "answer key", "tender", "guideline")):
                continue
            score = 10 if low.endswith(".pdf") else 5
            if "notification" in blob or "detailed" in blob or "advertisement" in blob:
                score += 15
            hits = sum(1 for tok in title_tokens if tok in blob)
            score += min(hits * 5, 25)
            candidates.append((score, href))
        if not candidates:
            return ""
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1] if candidates[0][0] >= 12 else ""

    def scrape(self, source=None):
        soup = self.soup(self.IBPS_URL)
        if soup is None:
            return []
        jobs, seen = [], set()
        for a in soup.find_all("a", href=True):
            title = self.clean(a.get_text(" ", strip=True))
            href = self.absolute(self.IBPS_URL, a.get("href"))
            if not title or not href or not self._is_recruitment_title(title):
                continue
            # Avoid duplicate menu links and unrelated CRP navigation.
            key = (title.casefold(), href.casefold())
            if key in seen:
                continue
            seen.add(key)
            job = self.build_job(title, href, "IBPS", "Recruitment")
            job["source"] = "ibps"
            job["official_website"] = self.IBPS_URL
            container = self._container(a)
            pdf = self._find_pdf(container, title)
            if pdf:
                job["notification_pdf"] = pdf
            # The homepage's surrounding text frequently contains the exact
            # registration window. Keep only explicit dates; PDF remains the
            # authority for eligibility/details.
            blob = self.clean(container.get_text(" ", strip=True))
            m = re.search(
                r"registration\s+from\s+(\d{1,2}[./-]\d{1,2}[./-]\d{4})\s*(?:to|[-–])\s*(\d{1,2}[./-]\d{1,2}[./-]\d{4})",
                blob, re.I,
            )
            if m:
                job["application_start_date"] = m.group(1)
                job["last_date"] = m.group(2)
            jobs.append(job)
        return self.enrich_and_filter(jobs)
