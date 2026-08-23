"""Multi-level recruitment detail/PDF crawler.

Purpose: follow a recruitment link beyond the source listing/homepage, resolve
viewer/document wrappers and identify the notification belonging to the exact
job title before extracting structured fields.
"""
from __future__ import annotations

import re
from collections import deque
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup


class RecruitmentDetailCrawler:
    def __init__(self, adapter, max_pages=10, max_depth=3):
        self.adapter = adapter
        self.max_pages = max_pages
        self.max_depth = max_depth

    @staticmethod
    def _domain(url):
        return urlparse(url).netloc.lower().removeprefix("www.")

    def _tokens(self, title):
        stop = {
            "recruitment", "notification", "advertisement", "advt", "online",
            "application", "apply", "post", "posts", "vacancy", "vacancies",
            "2024", "2025", "2026", "2027", "dated", "for", "the", "of", "and",
            "to", "in", "on", "at", "with", "engagement", "regarding", "through",
            "click", "here", "link", "details", "detailed", "notice", "latest",
        }
        words = re.findall(r"[a-z0-9]{3,}|[\u0900-\u097F]{3,}", str(title or "").lower())
        return [w for w in words if w not in stop]

    def _score(self, title, href, label, context, root):
        blob = f"{label} {context} {href}".lower()
        score = 0
        tokens = self._tokens(title)
        hits = sum(1 for t in tokens if t in blob)
        score += min(hits, 6) * 8
        if self._domain(href) == self._domain(root):
            score += 8
        if href.lower().split("#", 1)[0].endswith(".pdf"):
            score += 45
        if any(x in blob for x in (
            "detailed advertisement", "detailed notification", "recruitment notification",
            "advertisement", "notification", "advt", "विज्ञापन", "अधिसूचना", "डाउनलोड"
        )):
            score += 24
        if any(x in blob for x in ("view", "download", "document", "notice", "pdf", "loadpdf")):
            score += 8
        if any(x in blob for x in (
            "result", "answer key", "admit card", "hall ticket", "call letter",
            "joining", "scorecard", "syllabus", "guidelines", "question paper"
        )):
            score -= 30
        if any(x in blob for x in ("contact", "privacy", "login", "register", "feedback", "home")):
            score -= 40
        return score

    def _links(self, soup, base, title, root):
        candidates = []
        if soup is None:
            return candidates
        for a in soup.find_all("a", href=True):
            href = urljoin(base, str(a.get("href", "")).strip())
            label = self.adapter.clean(a.get_text(" ", strip=True))
            if not href or href.startswith(("javascript:", "mailto:", "tel:", "#")):
                continue
            parent = self.adapter.clean(a.parent.get_text(" ", strip=True)) if a.parent else ""
            score = self._score(title, href, label, parent, root)
            if score >= 12:
                candidates.append((score, href, label))
        # embedded document/viewer URLs
        for tag, attr in (("iframe", "src"), ("embed", "src"), ("object", "data")):
            for node in soup.find_all(tag):
                href = urljoin(base, str(node.get(attr, "")).strip())
                if href:
                    label = self.adapter.clean(node.get("title", "") or node.get("type", ""))
                    score = self._score(title, href, label, "document viewer", root) + 15
                    candidates.append((score, href, label))
        # JS variables frequently contain PDF/CDN URLs.
        for script in soup.find_all("script"):
            raw = script.string or script.get_text(" ", strip=True)
            for m in re.findall(r"(?:https?:)?//[^\"'\s<>]+(?:\.pdf|/download/|/uploads/|/documents?/)[^\"'\s<>]*", raw, re.I):
                href = urljoin(base, m)
                candidates.append((self._score(title, href, "script pdf document", "", root) + 10, href, "script"))
        candidates.sort(key=lambda x: (x[0], len(x[1])), reverse=True)
        seen = set()
        out = []
        for item in candidates:
            if item[1] in seen:
                continue
            seen.add(item[1])
            out.append(item)
            if len(out) >= 14:
                break
        return out

    def find(self, start_url, title):
        """Return (pdf_url, pdf_text, detail_url)."""
        if not start_url:
            return "", "", ""
        root = start_url
        queue = deque([(start_url, 0)])
        seen = set()
        pages = 0

        while queue and pages < self.max_pages:
            current, depth = queue.popleft()
            if not current or current in seen or depth > self.max_depth:
                continue
            seen.add(current)
            pages += 1

            try:
                r = self.adapter.session.get(current, timeout=(6, 18), allow_redirects=True, verify=False)
                final = str(r.url or current)
                content = r.content or b""
                ctype = r.headers.get("Content-Type", "").lower()
                if content[:4] == b"%PDF" or "application/pdf" in ctype or final.lower().split("#", 1)[0].endswith(".pdf"):
                    text = self.adapter.extract_pdf_text(final)
                    if text and self.adapter._notification_matches_title(type("J", (), {"get": lambda s,k,d='': title if k=='title' else (root if k=='url' else '')})(), text):
                        return final, text, current
                    continue
                if "html" not in ctype and "xhtml" not in ctype:
                    continue
                soup = BeautifulSoup(r.text or "", "html.parser")
                links = self._links(soup, final, title, root)

                # Try the strongest document candidates first.
                for score, href, label in links[:8]:
                    low = href.lower().split("#", 1)[0]
                    if low.endswith(".pdf") or any(x in (label + " " + low).lower() for x in ("download", "advertisement", "notification", "document", "loadpdf")):
                        resolved = self.adapter.resolve_document_pdf(href, max_depth=2) or (href if low.endswith(".pdf") else "")
                        if not resolved:
                            continue
                        text = self.adapter.extract_pdf_text(resolved)
                        if text:
                            # Strict title/PDF identity check is mandatory.
                            dummy = {"title": title, "url": root, "source": ""}
                            if self.adapter._notification_matches_title(dummy, text):
                                return resolved, text, current

                if depth < self.max_depth:
                    for score, href, label in links:
                        low = href.lower().split("#", 1)[0]
                        if low.endswith(".pdf"):
                            continue
                        # Only follow plausible detail/document pages.
                        if score >= 22:
                            queue.append((href, depth + 1))
            except Exception:
                continue
        return "", "", ""
