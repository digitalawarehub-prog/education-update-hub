"""State Bank of India current openings adapter.

The SBI careers page lists each recruitment as a block containing the
advertisement PDF and the apply link. The generic scraper used to mistake the
apply link for the post URL and then picked the first PDF on the page, which
caused regular/backlog advertisements to be mixed up.
"""
import re
from urllib.parse import urljoin
from .base import BaseAdapter


class SBIAdapter(BaseAdapter):
    SBI_URL = "https://sbi.bank.in/web/careers/current-openings"

    def _is_recruitment_title(self, text):
        t = self.clean(text).lower()
        return (
            len(t) >= 20 and
            any(k in t for k in (
                "recruitment of", "engagement of", "direct recruitment",
                "special recruitment drive"
            ))
        )

    def _container_for(self, node):
        current = node
        for _ in range(9):
            if current is None:
                break
            text = self.clean(current.get_text(" ", strip=True))
            if "download advertisement" in text.lower() and len(text) < 5000:
                return current
            current = getattr(current, "parent", None)
        return node.parent if getattr(node, "parent", None) else node

    def _pick_pdf(self, container, title):
        candidates = []
        for a in container.find_all("a", href=True):
            href = self.absolute(self.SBI_URL, a.get("href"))
            text = self.clean(a.get_text(" ", strip=True)).lower()
            if not href.lower().split("?", 1)[0].endswith(".pdf"):
                continue
            if "advertisement" not in text and "english" not in text and "hindi" not in text:
                continue
            score = 0
            if "english" in text:
                score += 20
            if "advertisement" in text:
                score += 10
            if "old advertisement" in text:
                score -= 50
            if "revised advertisement" in text:
                score += 5
            candidates.append((score, href))
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            return candidates[0][1]
        return ""

    def _pick_apply(self, container):
        for a in container.find_all("a", href=True):
            text = self.clean(a.get_text(" ", strip=True)).lower()
            href = self.absolute(self.SBI_URL, a.get("href"))
            if "apply online" in text or text == "apply now":
                if href and not href.lower().startswith("javascript:"):
                    return href
        return ""

    def scrape(self, source=None):
        soup = self.soup(self.SBI_URL)
        if soup is None:
            return []

        jobs = []
        seen = set()

        for node in soup.find_all(string=re.compile(r"(?:RECRUITMENT OF|ENGAGEMENT OF|DIRECT RECRUITMENT)", re.I)):
            title = self.clean(str(node))
            if not self._is_recruitment_title(title):
                continue

            container = self._container_for(node)
            block_text = self.clean(container.get_text(" ", strip=True))
            # Prevent a broad parent from swallowing several recruitment blocks.
            if len(block_text) > 5000:
                continue

            pdf = self._pick_pdf(container, title)
            apply = self._pick_apply(container)

            # The SBI page itself is the canonical public source page. Detail
            # extraction later uses the selected PDF rather than scanning the
            # entire page again.
            job = self.build_job(
                title=title,
                url=self.SBI_URL,
                department="SBI",
                category=self.detect_post_type(title, "", "Recruitment")
            )
            job["source"] = "sbi"
            job["notification_pdf"] = pdf
            job["apply_link"] = apply
            job["official_website"] = self.SBI_URL

            # Parse the date embedded in the listing for the application
            # window. The PDF remains the authoritative source for all fields.
            m = re.search(r"apply online from\s+(\d{1,2}[./-]\d{1,2}[./-]\d{4})\s+to\s+(\d{1,2}[./-]\d{1,2}[./-]\d{4})", block_text, re.I)
            if m:
                job["application_start_date"] = m.group(1)
                job["last_date"] = m.group(2)

            key = (title.casefold(), pdf.casefold())
            if key in seen:
                continue
            seen.add(key)
            jobs.append(job)

        return self.enrich_and_filter(jobs)
