"""Multi-level recruitment detail/PDF crawler.

Purpose: follow a recruitment link beyond the source listing/homepage, resolve
viewer/document wrappers and identify the notification belonging to the exact
job title before extracting structured fields.
"""
from __future__ import annotations

import re
import os
from collections import deque
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup


class RecruitmentDetailCrawler:
    def __init__(self, adapter, max_pages=8, max_depth=3):
        self.adapter = adapter
        self.max_pages = int(os.getenv("EUH_DETAIL_MAX_PAGES", max_pages))
        self.max_depth = int(os.getenv("EUH_DETAIL_MAX_DEPTH", max_depth))

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
        """Collect links from the whole recruitment card, not only the anchor parent.

        Government career pages frequently put the title in one element and the
        Advertisement/Apply/PDF links in sibling elements several levels up.
        The old crawler only inspected the immediate parent, so it often never
        discovered the notification belonging to the title.
        """
        candidates = []
        if soup is None:
            return candidates

        title_tokens = self._tokens(title)
        for a in soup.find_all("a"):
            raw_href = (a.get("href") or a.get("data-href") or a.get("data-url") or
                        a.get("data-pdf") or "").strip()
            if not raw_href:
                onclick = str(a.get("onclick") or "")
                m = re.search(r"(?:open|window\.open|location(?:\.href)?|download)[^'\"]*['\"]([^'\"]+)['\"]", onclick, re.I)
                if m:
                    raw_href = m.group(1)
            href = urljoin(base, raw_href)
            if not href or href.startswith(("javascript:", "mailto:", "tel:", "#")):
                continue
            label = self.adapter.clean(a.get_text(" ", strip=True))
            contexts = []
            cur = a
            for _ in range(5):
                if cur is None:
                    break
                txt = self.adapter.clean(cur.get_text(" ", strip=True))
                if txt:
                    contexts.append(txt)
                cur = cur.parent
            context = " ".join(contexts[:4])
            score = self._score(title, href, label, context, root)
            blob = f"{label} {context} {href}".lower()
            hits = sum(1 for t in title_tokens if t in blob)
            score += min(hits, 8) * 4
            # Many government portals use a generic link label while the URL
            # itself is the only clue that this is the recruitment detail page.
            # Follow these paths even when the title text is not repeated in
            # the anchor.
            if any(part in href.lower() for part in (
                "/recruitment", "/recruitments", "/careers", "/career",
                "/notification", "/advertisement", "/vacancy", "/advt",
                "/notice", "/document", "/job", "/jobs", "viewpdf",
                "open_pdf", "loadpdf"
            )):
                score += 18
            if any(k in blob for k in ("download advertisement", "detailed advertisement", "recruitment notification", "advertisement pdf", "notification pdf")):
                score += 22
            if any(k in blob for k in ("apply online", "apply now", "registration")):
                score += 5
            if any(k in blob for k in ("result", "answer key", "admit card", "hall ticket", "call letter", "syllabus", "information handout")):
                score -= 35
            if score >= 8:
                candidates.append((score, href, label))

        # Buttons/divs on modern portals often store the detail/PDF URL in a
        # data-* attribute without an <a> element.
        for node in soup.find_all(["button", "div", "span"]):
            raw = (node.get("data-href") or node.get("data-url") or
                   node.get("data-pdf") or node.get("data-document") or "").strip()
            if not raw:
                continue
            href = urljoin(base, raw)
            label = self.adapter.clean(node.get_text(" ", strip=True))
            score = self._score(title, href, label, "data document", root) + 16
            candidates.append((score, href, label))

        # embedded document/viewer URLs
        for tag, attr in (("iframe", "src"), ("embed", "src"), ("object", "data")):
            for node in soup.find_all(tag):
                href = urljoin(base, str(node.get(attr, "")).strip())
                if href:
                    label = self.adapter.clean(node.get("title", "") or node.get("type", ""))
                    score = self._score(title, href, label, "document viewer", root) + 20
                    candidates.append((score, href, label))

        # JS variables frequently contain PDF/CDN URLs.
        for script in soup.find_all("script"):
            raw = script.string or script.get_text(" ", strip=True)
            for m in re.findall(r"(?:https?:)?//[^\"'\s<>]+(?:\.pdf|/download/|/uploads/|/documents?/|/open_pdf_db\.aspx|/loadpdf(?:\.php)?)\S*", raw, re.I):
                href = urljoin(base, m.rstrip("'\";,))"))
                candidates.append((self._score(title, href, "script pdf document", "", root) + 12, href, "script"))

        candidates.sort(key=lambda x: (x[0], len(x[1])), reverse=True)
        seen = set()
        out = []
        for item in candidates:
            key = item[1].split("#", 1)[0]
            if key in seen:
                continue
            seen.add(key)
            out.append(item)
            if len(out) >= 24:
                break
        return out

    def find(self, start_url, title):
        """Return (pdf_url, pdf_text, detail_url)."""
        if not start_url:
            return "", "", ""
        low_title = str(title or "").casefold()
        # Never deep-crawl obvious result/update/general-notice pages. The word
        # "vacancies" alone is not proof of recruitment.
        reject_signals=(
            "notification regarding re-appointment", "re-appointment of",
            "list of selected proposals", "selected proposals for conducting",
            "selection list", "joining schedule", "minutes of meeting",
        )
        if any(x in low_title for x in reject_signals):
            return "", "", ""
        if any(x in low_title for x in ("click here to apply", "click here to modify", "online application", "recruitment exams", "simplifying the admission process", "personnel selection services")) and not any(x in low_title for x in ("recruitment of", "advertisement for", "engagement of")):
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
                r = self.adapter.session.get(current, timeout=(5, 12), allow_redirects=True, verify=False)
                final = str(r.url or current)
                content = r.content or b""
                ctype = r.headers.get("Content-Type", "").lower()
                if content[:4] == b"%PDF" or "application/pdf" in ctype or final.lower().split("#", 1)[0].endswith(".pdf"):
                    text = self.adapter.extract_pdf_text(final)
                    if text and self.adapter._notification_matches_title({"title": title, "url": root}, text):
                        return final, text, current
                    continue
                if "html" not in ctype and "xhtml" not in ctype:
                    continue
                soup = BeautifulSoup(r.text or "", "html.parser")
                links = self._links(soup, final, title, root)

                # Try the strongest document candidates first.
                for score, href, label in links[:12]:
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
                        if score >= 10:
                            queue.append((href, depth + 1))
            except Exception:
                continue
        return "", "", ""
