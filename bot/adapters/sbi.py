"""SBI Careers adapter.

SBI's Current Openings page is a grouped asset/listing page, not a detail page.
Each recruitment is represented by one card containing the title, advertisement
number, last date, notification PDF and apply link. A normal link scraper sees
those links independently and loses the card relationship; this adapter keeps
the whole card together and uses the card's own notification PDF for detail
extraction.
"""
from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import BaseAdapter


class SBIAdapter(BaseAdapter):
    SOURCE_URL = "https://sbi.bank.in/hi/web/careers/current-openings"

    def _is_card_candidate(self, text: str) -> bool:
        t = self.clean(text).lower()
        return (
            bool(re.search(r"advertisement\s*no\s*[:.]?\s*[a-z0-9/\-]+", t, re.I))
            and any(k in t for k in ("recruitment", "engagement", "apprentice", "vacancy"))
        )

    def _find_card(self, node):
        """Return the smallest useful ancestor containing one SBI opening."""
        cur = node
        best = None
        for _ in range(8):
            if cur is None or getattr(cur, "name", None) in ("html", "body"):
                break
            text = self.clean(cur.get_text(" ", strip=True))
            links = cur.find_all("a", href=True)
            if self._is_card_candidate(text) and links and len(text) <= 4500:
                best = cur
            # Once the candidate becomes very large it is the asset publisher,
            # not a single opening card.
            if len(text) > 4500:
                break
            cur = cur.parent
        return best

    def _advertisement_no(self, text):
        m = re.search(r"advertisement\s*no\s*[:.]?\s*([A-Z0-9][A-Z0-9/\-]{3,60})", text, re.I)
        return self.clean(m.group(1)) if m else ""

    def _title(self, card_text):
        text = self.clean(card_text)
        # Prefer the first recruitment/engagement line before Advertisement No.
        before = re.split(r"advertisement\s*no\s*[:.]?", text, maxsplit=1, flags=re.I)[0]
        before = re.sub(r"last\s+date\s+to\s+apply\s*[:\-]?\s*\d{1,2}[./-]\d{1,2}[./-]\d{2,4}", " ", before, flags=re.I)
        parts = [self.clean(x) for x in re.split(r"\s{2,}|\n", before) if self.clean(x)]
        for p in parts:
            if any(k in p.lower() for k in ("recruitment", "engagement", "apprentice", "vacancy")):
                return p[:500]
        # Fallback for pages where all text is in one node.
        m = re.search(r"((?:recruitment|engagement|apprentice|vacancy)[^|]{10,500})", text, re.I)
        return self.clean(m.group(1))[:500] if m else text[:300]

    def _date_pair(self, text):
        # SBI card title contains: Apply Online from 11.08.2026 to 31.08.2026
        m = re.search(
            r"apply\s+online\s+from\s+(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})\s+to\s+(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})",
            text, re.I,
        )
        if m:
            return self.clean(m.group(1)), self.clean(m.group(2))
        m = re.search(r"from\s+(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})\s+to\s+(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})", text, re.I)
        if m:
            return self.clean(m.group(1)), self.clean(m.group(2))
        m = re.search(r"last\s+date\s+to\s+apply\s*[:\-]?\s*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})", text, re.I)
        return "", self.clean(m.group(1)) if m else ""

    def _links(self, card, base_url):
        pdf_candidates = []
        apply_candidates = []
        for a in card.find_all("a", href=True):
            href = urljoin(base_url, a.get("href", "").strip())
            txt = self.clean(a.get_text(" ", strip=True))
            low = txt.lower()
            href_low = href.lower()
            if not href or href.startswith("javascript:"):
                continue
            if any(k in low for k in ("download advertisement", "detailed advertisement", "advertisement")) or href_low.endswith(".pdf") or "loadpdf" in href_low:
                score = 0
                if "english" in low: score += 30
                if "download advertisement" in low: score += 20
                if href_low.endswith(".pdf"): score += 10
                pdf_candidates.append((score, href))
            if any(k in low for k in ("apply online", "apply now", "online registration")):
                apply_candidates.append((20, href))
        pdf = max(pdf_candidates, default=(0, ""))[1]
        apply = max(apply_candidates, default=(0, ""))[1]
        return pdf, apply

    def scrape(self, source):
        url = source.get("url") or self.SOURCE_URL
        soup = self.soup(url)
        if soup is None:
            return []

        jobs = []
        seen = set()
        # Search all tags for an advertisement number. The exact SBI HTML class
        # has changed over time, so the parser intentionally relies on semantic
        # content rather than brittle class names.
        for node in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "div", "p", "span", "strong"]):
            text = self.clean(node.get_text(" ", strip=True))
            if not self._is_card_candidate(text):
                continue
            card = self._find_card(node)
            if card is None:
                continue
            card_text = self.clean(card.get_text(" ", strip=True))
            ad_no = self._advertisement_no(card_text)
            if not ad_no or ad_no in seen:
                continue
            title = self._title(card_text)
            if not title or not self.is_valid_notification(title, url):
                continue

            start_date, last_date = self._date_pair(card_text)
            pdf, apply = self._links(card, url)
            job = self.build_job(
                title=title,
                url=url,
                department="SBI",
                category="Banking",
            )
            job["official_website"] = url
            job["advertisement_no"] = ad_no
            job["notification_pdf"] = pdf
            job["apply_link"] = apply
            job["application_start_date"] = start_date
            job["last_date"] = last_date
            job["content"] = card_text[:5000]
            job["description"] = card_text[:700]
            job["post_type"] = self.detect_post_type(title, url, "Banking")

            # The PDF is the authoritative source for vacancy/qualification/
            # salary/age/fee/selection. Crucially, use THIS card's PDF only.
            if pdf:
                pdf_text = self.extract_pdf_text(pdf)
                if pdf_text:
                    self._apply_pdf_details(job, pdf, pdf_text)
                    # Keep card dates when PDF extraction did not expose the
                    # application window in a clean form.
                    if start_date and not job.get("application_start_date"):
                        job["application_start_date"] = start_date
                    if last_date and not job.get("last_date"):
                        job["last_date"] = last_date

            seen.add(ad_no)
            jobs.append(job)

        return jobs
