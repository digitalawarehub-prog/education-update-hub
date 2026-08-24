"""Bounded deep crawler for recruitment detail pages and notification PDFs.

The crawler deliberately follows the chain:
listing/card -> detail page -> advertisement/document link -> real PDF.
It is title-aware and keeps a strict identity check so one post cannot borrow
another post's vacancy/salary/selection data.
"""
from __future__ import annotations

import re
from collections import deque
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup


class RecruitmentDetailCrawler:
    def __init__(self, adapter, max_pages=10, max_depth=3):
        # Hard caps protect GitHub Actions from a single bad government site.
        self.adapter = adapter
        self.max_pages = min(max(1, int(max_pages)), 7)
        self.max_depth = min(max(1, int(max_depth)), 3)

    @staticmethod
    def _domain(url):
        return urlparse(url).netloc.lower().removeprefix("www.")

    @staticmethod
    def _clean_url(url):
        return str(url or "").strip().split("#", 1)[0]

    def _tokens(self, title):
        stop = {
            "recruitment", "notification", "advertisement", "advt", "online",
            "application", "apply", "post", "posts", "vacancy", "vacancies",
            "2024", "2025", "2026", "2027", "dated", "for", "the", "of", "and",
            "to", "in", "on", "at", "with", "engagement", "regarding", "through",
            "click", "here", "link", "details", "detailed", "notice", "latest",
            "basis", "from", "registration", "customer", "support", "sales",
        }
        words = re.findall(r"[a-z0-9]{3,}|[\u0900-\u097F]{3,}", str(title or "").lower())
        return [w for w in words if w not in stop]

    def _identity_numbers(self, text):
        text = str(text or "")
        pats = [
            r"(?:advertisement|advt\.?|notification|notice)\s*(?:no\.?|number)?\s*[:#-]?\s*([A-Z0-9][A-Z0-9./_-]{3,})",
            r"\b(CRPD/[A-Z0-9./_-]{4,})\b",
            r"\b([A-Z]{1,8}/\d{1,6}/\d{2,4})\b",
        ]
        out = set()
        for p in pats:
            for m in re.finditer(p, text, re.I):
                out.add(re.sub(r"\s+", "", m.group(1)).casefold())
        return out

    def _score(self, title, href, label, context, root):
        blob = f"{label} {context} {href}".lower()
        score = 0
        tokens = self._tokens(title)
        hits = sum(1 for t in tokens if t in blob)
        score += min(hits, 7) * 9
        if self._domain(href) == self._domain(root):
            score += 10
        low = self._clean_url(href).lower()
        if low.endswith(".pdf"):
            score += 60
        if any(x in blob for x in (
            "detailed advertisement", "detailed notification", "recruitment notification",
            "advertisement", "notification", "advt", "विज्ञापन", "अधिसूचना",
            "download advertisement", "download notification", "डाउनलोड",
        )):
            score += 30
        if any(x in blob for x in ("view", "download", "document", "notice", "pdf", "loadpdf", "attachment")):
            score += 10
        if any(x in blob for x in (
            "result", "answer key", "admit card", "hall ticket", "call letter",
            "joining", "scorecard", "syllabus", "guidelines", "question paper"
        )):
            score -= 45
        if any(x in blob for x in ("contact", "privacy", "login", "register", "feedback", "home")):
            score -= 50
        return score

    def _links(self, soup, base, title, root):
        candidates = []
        if soup is None:
            return candidates

        for a in soup.find_all("a", href=True):
            raw = str(a.get("href", "")).strip()
            href = urljoin(base, raw)
            label = self.adapter.clean(a.get_text(" ", strip=True))
            if not href or href.startswith(("javascript:", "mailto:", "tel:", "#")):
                continue

            # Use the whole nearest card/table/list container as context. This
            # is important for portals where the link itself only says "NEW" or
            # "Click here" while the job title sits beside it.
            context_parts = []
            for parent in list(a.parents)[:4]:
                if getattr(parent, "name", None) in ("tr", "li", "article", "section", "div"):
                    txt = self.adapter.clean(parent.get_text(" ", strip=True))
                    if txt:
                        context_parts.append(txt[:1800])
                        if len(txt) >= 120:
                            break
            context = " ".join(context_parts)
            score = self._score(title, href, label, context, root)
            candidates.append((score, href, label, context))

        # Embedded viewers and PDF objects.
        for tag, attr in (("iframe", "src"), ("embed", "src"), ("object", "data")):
            for node in soup.find_all(tag):
                href = urljoin(base, str(node.get(attr, "")).strip())
                if href:
                    label = self.adapter.clean(node.get("title", "") or node.get("type", ""))
                    candidates.append((self._score(title, href, label, "document viewer", root) + 20, href, label, "document viewer"))

        # CMS pages often hide the real PDF URL in JavaScript.
        for script in soup.find_all("script"):
            raw = script.string or script.get_text(" ", strip=True)
            for m in re.findall(r"(?:https?:)?//[^\"'\s<>]+(?:\.pdf|/download/|/uploads/|/documents?/|loadpdf)[^\"'\s<>]*", raw, re.I):
                href = urljoin(base, m)
                candidates.append((self._score(title, href, "script advertisement pdf", "", root) + 15, href, "script", ""))

        candidates.sort(key=lambda x: (x[0], len(x[1])), reverse=True)
        seen = set()
        out = []
        for item in candidates:
            clean = self._clean_url(item[1])
            if clean in seen:
                continue
            seen.add(clean)
            out.append(item)
            if len(out) >= 20:
                break
        return out

    def _accept_pdf(self, title, root, pdf_url, text):
        if not text or len(text.strip()) < 80:
            return False
        dummy = {"title": title, "url": root, "source": ""}
        if self.adapter._notification_matches_title(dummy, text):
            return True
        # A second, narrowly-scoped fallback: if the exact advertisement number
        # is present in both the recruitment page/title and the PDF, identity is
        # stronger than generic title-word overlap.
        title_ids = self._identity_numbers(title)
        body_ids = self._identity_numbers(text[:120000])
        if title_ids and title_ids.intersection(body_ids):
            return True
        return False

    def find(self, start_url, title):
        """Return (pdf_url, pdf_text, detail_url)."""
        if not start_url or not title:
            return "", "", ""

        root = start_url
        queue = deque([(start_url, 0)])
        seen = set()
        pages = 0

        while queue and pages < self.max_pages:
            current, depth = queue.popleft()
            current = self._clean_url(current)
            if not current or current in seen or depth > self.max_depth:
                continue
            seen.add(current)
            pages += 1

            try:
                r = self.adapter.session.get(
                    current,
                    timeout=(4, 10),
                    allow_redirects=True,
                    verify=False,
                    headers={"Accept": "text/html,application/xhtml+xml,application/pdf,*/*;q=0.5"},
                )
                final = str(r.url or current)
                content = r.content or b""
                ctype = r.headers.get("Content-Type", "").lower()
                low_final = self._clean_url(final).lower()

                if content[:4] == b"%PDF" or "application/pdf" in ctype or low_final.endswith(".pdf"):
                    text = self.adapter.extract_pdf_text(final)
                    if self._accept_pdf(title, root, final, text):
                        return final, text, current
                    continue

                if "html" not in ctype and "xhtml" not in ctype:
                    continue

                soup = BeautifulSoup(r.text or "", "html.parser")
                links = self._links(soup, final, title, root)

                # First pass: inspect only the strongest document candidates.
                for score, href, label, context in links[:12]:
                    low = self._clean_url(href).lower()
                    blob = f"{label} {context} {href}".lower()
                    looks_document = (
                        low.endswith(".pdf") or
                        any(x in blob for x in ("advertisement", "notification", "download", "document", "loadpdf", "विज्ञापन", "अधिसूचना"))
                    )
                    if not looks_document or score < 20:
                        continue
                    resolved = self.adapter.resolve_document_pdf(href, max_depth=2) or (href if low.endswith(".pdf") else "")
                    if not resolved:
                        continue
                    try:
                        text = self.adapter.extract_pdf_text(resolved)
                    except Exception:
                        text = ""
                    if self._accept_pdf(title, root, resolved, text):
                        return resolved, text, current

                # Second pass: follow only plausible detail/document pages.
                if depth < self.max_depth:
                    for score, href, label, context in links:
                        low = self._clean_url(href).lower()
                        if low.endswith(".pdf"):
                            continue
                        blob = f"{label} {context} {href}".lower()
                        if score >= 28 or any(x in blob for x in ("download advertisement", "detailed notification", "recruitment notification", "विज्ञापन", "अधिसूचना")):
                            queue.append((href, depth + 1))
            except Exception:
                continue

        return "", "", ""
