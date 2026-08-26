"""Education Update Hub - robust generic adapter.

Generic sources are deliberately conservative: navigation links are filtered,
real notification links are ranked, PDF enrichment is delegated to BaseAdapter,
and a bounded candidate list prevents one large government page from blocking
the whole run.
"""
from __future__ import annotations

import logging
import os
import re
from urllib.parse import urljoin

from .base import BaseAdapter

logger = logging.getLogger("GenericAdapter")


class GenericAdapter(BaseAdapter):
    def __init__(self):
        super().__init__()
        try:
            self.max_candidates = max(1, int(os.getenv("EHU_GENERIC_MAX_CANDIDATES", "24")))
        except (TypeError, ValueError):
            self.max_candidates = 24

    def clean(self, text):
        return " ".join(str(text or "").split()).strip()

    def absolute(self, base_url, href):
        return urljoin(base_url or "", str(href or "").strip())

    def build_job(self, title, url, department="Government", category="Latest Jobs"):
        return {
            "title": self.clean(title), "url": url, "department": department,
            "category": category, "vacancy": "", "qualification": "", "salary": "",
            "age_limit": "", "application_fee": "", "selection_process": "",
            "exam_date": "", "application_start_date": "", "last_date": "",
            "notification_date": "", "notification_pdf": "", "apply_link": "",
            "official_website": url, "admit_card_url": "", "result_url": "",
            "answer_key_url": "", "syllabus_url": "", "description": "",
            "content": "", "notification_text": "", "image": "", "thumbnail": "",
            "featured_image": "", "tags": [], "priority": 0,
        }

    def _rank_job(self, job):
        title = self.clean(job.get("title")).casefold()
        url = self.clean(job.get("url")).casefold()
        strong = ("recruitment", "vacancy", "advertisement", "notification", "advt",
                  "engagement", "apprentice", "apply online", "applications are invited",
                  "interview", "admit card", "result", "answer key", "syllabus",
                  "shortlisted", "document verification")
        roles = ("assistant", "officer", "engineer", "teacher", "professor", "lecturer",
                 "clerk", "technician", "constable", "inspector", "research", "fellow",
                 "manager", "executive", "driver", "scientist", "analyst")
        score = sum(4 for k in strong if k in title)
        score += sum(2 for k in roles if k in title)
        score += 5 if any(k in url for k in ("recruit", "career", "vacanc", "notification", "advert", "advt", "job", "result", "admit")) else 0
        if any(k in title for k in ("privacy", "contact", "login", "forgot password", "annual report", "tender")):
            score -= 20
        return score

    def _pdf_matches_title(self, job):
        text = self.clean(job.get("notification_text", "")).casefold()
        if not text:
            return True
        title = self.clean(job.get("title", "")).casefold()
        words = [w for w in re.findall(r"[a-z0-9]{3,}", title)
                 if w not in {"the", "and", "for", "from", "post", "posts", "2025", "2026", "2027",
                              "recruitment", "notification", "online", "application", "registration"}]
        if not words:
            return True
        unique = set(words)
        hits = sum(1 for w in unique if w in text)
        ratio = hits / max(len(unique), 1)
        return ratio >= 0.18 or len(unique) <= 2

    def scrape_site(self, source):
        source_url = self.clean(source.get("url"))
        if not source_url:
            return []
        soup = self.soup(source_url)
        if soup is None:
            return []

        main = (soup.find("article") or soup.find("main") or
                soup.find("div", class_=re.compile(r"content|container|listing|career|notice", re.I)) or
                soup.body or soup)
        candidates = []
        for link in main.find_all("a", href=True):
            title = self.clean(link.get_text(" ", strip=True))
            href = self.absolute(source_url, link.get("href", ""))
            if not title or not href or href.startswith(("javascript:", "mailto:", "tel:", "#")):
                continue
            low = title.casefold()
            if "{{" in title or "}}" in title or "translate" in low:
                continue
            if len(title) < 8 or len(title) > 500:
                continue
            if low in {"home", "about", "contact", "login", "register", "view all", "view more", "read more", "click here", "privacy policy", "site map"}:
                continue
            if not self.is_valid_notification(title, href):
                continue
            candidates.append(self.build_job(title, href, source.get("department", "Government"), self.detect_category(title)))

        candidates = self.remove_duplicates(candidates)
        candidates.sort(key=self._rank_job, reverse=True)
        return candidates[:self.max_candidates]

    def is_job_link(self, title, url=""):
        return self.is_valid_notification(title, url)

    def is_valid_notification(self, title, url=""):
        title = self.clean(title)
        text = f"{title} {url}".casefold()
        if not title or len(title) < 8 or "{{" in title or "}}" in title or "translate" in text:
            return False
        ignore = ("about", "contact", "privacy", "policy", "feedback", "gallery", "photo",
                  "video", "chairman", "member", "committee", "login", "register", "help",
                  "faq", "accessibility", "site map", "annual report", "tender", "copyright",
                  "notification board", "recruitment/admission links", "forgot password", "reset password",
                  "step-1", "step 1", "view all", "view more", "read more", "click here", "download guidelines")
        if any(x in text for x in ignore):
            return False
        keywords = ("recruitment", "vacancy", "notification", "advertisement", "advt", "apply", "online application",
                    "result", "merit list", "selection list", "score card", "answer key", "admit card", "hall ticket",
                    "call letter", "exam", "syllabus", "scholarship", "interview", "walk in", "document verification",
                    "shortlisted", "appointment", "engagement", "apprentice", "applications are invited")
        return any(k in text for k in keywords)

    def detect_category(self, title):
        t = self.clean(title).casefold()
        if any(x in t for x in ("admit card", "hall ticket", "call letter")): return "Admit Card"
        if any(x in t for x in ("answer key", "response sheet")): return "Answer Key"
        if any(x in t for x in ("result", "merit list", "selection list", "score card")): return "Results"
        if any(x in t for x in ("syllabus", "exam pattern")): return "Syllabus"
        if any(x in t for x in ("scholarship", "fellowship", "stipend")): return "Scholarship"
        if any(x in t for x in ("scheme", "yojana")): return "Government Schemes"
        return "Latest Jobs"

    def remove_duplicates(self, jobs):
        seen, unique = set(), []
        for job in jobs or []:
            title = self.clean(job.get("title")).casefold()
            url = self.clean(job.get("url")).casefold()
            if not title or not url or (title, url) in seen:
                continue
            seen.add((title, url)); unique.append(job)
        return unique

    def build_jobs(self, links, source):
        jobs=[]
        for title, href in links or []:
            title=self.clean(title); href=self.absolute(source.get("url"),href)
            if title and href and self.is_valid_notification(title,href):
                jobs.append(self.build_job(title,href,source.get("department","Government"),self.detect_category(title)))
        return self.remove_duplicates(jobs)

    def enrich_jobs(self, jobs):
        enriched=[]
        for job in jobs or []:
            try:
                job=self.enrich_job(job)
                if job.get("notification_pdf") and not self._pdf_matches_title(job):
                    logger.warning("PDF IDENTITY REJECTED | %s | pdf=%s", job.get("title",""), job.get("notification_pdf",""))
                    job["notification_pdf"]=""
                    job["official_notification_pdf"]=""
                    job["notification_text"]=""
                    for key in ("vacancy","qualification","salary","age_limit","application_fee","selection_process","exam_date","application_start_date","last_date"):
                        job[key]=""
                enriched.append(job)
            except Exception:
                logger.exception("Generic enrichment failed: %s", job.get("title","")); enriched.append(job)
        return self.remove_duplicates(enriched)

    def scrape(self, source):
        if not source.get("url"):
            return []
        jobs=self.scrape_site(source)
        logger.info("GENERIC CANDIDATES | %s | %d (limit=%d)", source.get("name","Unknown"), len(jobs), self.max_candidates)
        return self.enrich_jobs(jobs)

    def validate(self):
        return True

    @property
    def name(self):
        return "GenericAdapter"
