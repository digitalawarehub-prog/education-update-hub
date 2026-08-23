"""Education Update Hub - shared production adapter utilities."""
from __future__ import annotations

import io
import logging
import re
from datetime import date, datetime
from urllib.parse import urljoin

import requests
import urllib3
from bs4 import BeautifulSoup
try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None
try:
    import fitz
except Exception:
    fitz = None
try:
    import pdfplumber
except Exception:
    pdfplumber = None
try:
    import pytesseract
    from PIL import Image
except Exception:
    pytesseract = None
    Image = None
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.exceptions import InsecureRequestWarning
from filters import classify_post

urllib3.disable_warnings(InsecureRequestWarning)
logger = logging.getLogger(__name__)


class BaseAdapter:
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0 Safari/537.36"
    )

    # A title must describe an actual recruitment/result/update item.
    # Very broad words such as "apply", "posts" or "selection" alone are
    # intentionally NOT enough because government homepages contain many
    # navigation links with these words.
    JOB_KEYWORDS = (
        "recruitment", "vacancy", "vacancies", "advertisement", "advt",
        "direct recruitment", "engagement", "hiring", "appointment",
        "walk-in", "walk in", "apprentice", "apprenticeship",
        "application invited", "applications are invited", "apply online",
        "online application", "career", "job", "jobs",
        "भर्ती", "विज्ञापन", "विज्ञप्ति", "अधिसूचना", "रिक्ति", "रिक्तियां",
        "आवेदन आमंत्रित", "ऑनलाइन आवेदन", "नियुक्ति", "अप्रेंटिस", "साक्षात्कार",
    )
    RESULT_KEYWORDS = (
        "result", "answer key", "admit card", "hall ticket", "syllabus",
        "merit list", "shortlisted", "shortlist", "document verification",
        "counselling", "exam programme", "exam calendar",
        "परिणाम", "उत्तरकुंजी", "प्रवेश पत्र", "पाठ्यक्रम", "मेरिट",
    )
    JOB_ROLE_KEYWORDS = (
        "assistant", "teacher", "officer", "engineer", "technician",
        "constable", "inspector", "clerk", "stenographer", "patwari",
        "lekhpal", "fellow", "research", "professional", "scientist",
        "staff", "faculty", "professor", "lecturer", "driver", "junior",
        "senior", "कर्मचारी", "अधिकारी", "शिक्षक", "प्रोफेसर", "व्याख्याता",
    )
    IGNORE_KEYWORDS = (
        "contact", "feedback", "privacy", "policy", "gallery", "chairman",
        "member", "organisation", "organization", "about", "rti", "calendar",
        "help", "accessibility", "copyright", "login", "logout", "register",
        "registration", "forgot password", "reset password", "step-1", "step 1",
        "view all", "view more", "read more", "click here", "home", "homepage",
        "menu", "search", "support", "skip to main content", "select your language",
        "download hindi notification", "download english notification",
        "download notification", "download guidelines", "recruitment/admission links",
        "vacancy position", "vacancy/nia", "tender", "old recruitment", "archive",
        "website policies", "web information manager", "public information officer",
        "appellate authority", "finance controller", "examination controller",
        "cm dashboard", "cm office", "national portal of india",
    )
    BAD_URL_PARTS = (
        "/login", "/logout", "/register", "/registration", "/forgot",
        "/reset", "/search", "/about", "/contact", "/feedback", "/gallery",
        "/photo-gallery", "/privacy", "/cookie", "/sitemap", "/website-policies",
        "/organization", "/organisation", "/chairman", "/member", "/rti",
        "/manual", "/student", "/academic", "/event",
    )
    GOOD_URL_PARTS = (
        "/recruitment", "/notification", "/advertisement", "/vacancy",
        "/career", "/careers", "/job", "/jobs", "/advt", "/engagement",
        "/apprentice", "/apprenticeship", "/result", "/admit-card",
        "/answer-key", "/syllabus", "/selection", "/exam",
    )

    DATE_PATTERNS = (
        r"\b(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})\b",
        r"\b(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4})\b",
        r"\b((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b",
        r"\b(\d{1,2}\s+(?:जनवरी|फरवरी|मार्च|अप्रैल|मई|जून|जुलाई|अगस्त|सितंबर|अक्टूबर|नवंबर|दिसंबर)\s+\d{4})\b",
    )

    def __init__(self):
        retry = Retry(total=0, connect=0, read=0, backoff_factor=0, status_forcelist=[])
        adapter = HTTPAdapter(max_retries=retry)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
        })
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        # Per-run PDF cache: legacy repair can encounter the same notification
        # PDF through several duplicate records. Download/OCR it only once.
        self._pdf_text_cache = {}
        self._pdf_failed_cache = set()

    def fetch(self, url: str) -> str:
        if not url:
            return ""
        try:
            r = self.session.get(url, timeout=(5, 12), allow_redirects=True, verify=False)
            if r.status_code >= 400:
                logger.warning("Source skipped HTTP %s: %s", r.status_code, url)
                return ""
            ctype = r.headers.get("Content-Type", "").lower()
            if "application/pdf" in ctype or r.content[:4] == b"%PDF":
                return ""
            return r.text or ""
        except requests.RequestException as exc:
            logger.warning("Fetch failed: %s | %s", url, exc.__class__.__name__)
            return ""
        except Exception:
            logger.exception("Unexpected fetch error: %s", url)
            return ""

    def soup(self, url):
        html = self.fetch(url)
        return BeautifulSoup(html, "html.parser") if html else None

    def clean(self, text) -> str:
        return re.sub(r"\s+", " ", str(text or "")).strip()

    def absolute(self, base, url) -> str:
        return urljoin(base or "", str(url or "").strip())

    def page_text(self, soup) -> str:
        if soup is None:
            return ""
        clone = BeautifulSoup(str(soup), "html.parser")
        for tag in clone(["script", "style", "header", "footer", "nav", "aside", "noscript", "form"]):
            tag.decompose()
        main = (
            clone.find("article") or clone.find("main") or
            clone.find("div", class_=re.compile(r"content|entry|post", re.I)) or
            clone.body or clone
        )
        return self.clean(main.get_text(" ", strip=True))

    def detect_post_type(self, title, url="", category=""):
        """Determine content type from the post itself before PDF extraction.

        Title signals have priority over notification-body words. A recruitment
        PDF may legitimately mention call letters, results and exams; those
        words must never turn the recruitment post into an Admit Card/Result
        record.
        """
        t = self.clean(title).casefold()
        u = self.clean(url).casefold()
        c = self.clean(category).casefold()

        if any(x in t for x in (
            "admit card", "admit-card", "hall ticket", "e-admit",
            "call letter", "call-letter", "प्रवेश पत्र", "प्रवेश-पत्र",
        )):
            return "admit-card"
        if any(x in t for x in (
            "answer key", "answer-key", "answerkey", "उत्तर कुंजी", "उत्तरकुंजी"
        )):
            return "answer-key"
        if re.search(r"\b(result|merit list|score ?card|final result|परिणाम)\b", t, re.I):
            return "result"
        if any(x in t for x in ("syllabus", "exam pattern", "पाठ्यक्रम")):
            return "syllabus"
        if any(x in t for x in ("scholarship", "fellowship", "छात्रवृत्ति")):
            return "scholarship"
        if any(x in t for x in (
            "recruitment", "vacancy", "advertisement", "advt", "direct recruitment",
            "apply online", "online application", "registration from",
            "applications are invited", "engagement", "hiring", "भर्ती",
            "विज्ञापन", "विज्ञप्ति", "अधिसूचना", "रिक्ति", "ऑनलाइन आवेदन"
        )):
            return "recruitment"

        # Category is only a fallback when the title is neutral.
        if c in {"admit card", "admit-card"}: return "admit-card"
        if c in {"answer key", "answer-key"}: return "answer-key"
        if c in {"result", "results"}: return "result"
        if c == "syllabus": return "syllabus"
        if c == "scholarship": return "scholarship"
        if c in {"recruitment", "latest jobs", "latest job", "jobs", "job"}: return "recruitment"
        return "other"

    def extract_value(self, text, patterns):
        text = str(text or "")
        for pattern in patterns:
            m = re.search(pattern, text, re.I)
            if m:
                value = self.clean(m.group(1))
                if value:
                    return value
        return ""

    def _first_number(self, text, start=0, end=None):
        segment = str(text or "")[start:end]
        nums = []
        for m in re.finditer(r"(?<![\d/.-])(\d{1,6})(?![\d/.-])", segment):
            try:
                n = int(m.group(1))
                if 1 <= n <= 100000:
                    nums.append(n)
            except Exception:
                pass
        return str(nums[0]) if nums else ""

    def _valid_vacancy_candidate(self, number, context, strong=False):
        try:
            n=int(number)
        except Exception:
            return False
        if n < 1 or n > 100000 or 1900 <= n <= 2100:
            return False
        c=self.clean(context).casefold()
        # Large values are accepted only when the surrounding text explicitly
        # ties the number to posts/vacancies. This blocks serial numbers, dates
        # and unrelated numeric values such as the MPPSC 51417 false match.
        if n >= 10000 and not strong:
            return bool(re.search(r"(?:vacanc(?:y|ies)|posts?|पद|रिक्त)", c, re.I) and
                        re.search(r"(?:vacanc(?:y|ies)|posts?|पद|रिक्त)", c[max(0, len(c)//2-80):], re.I))
        return True

    def extract_vacancy(self, text):
        """Extract vacancy conservatively from explicit vacancy/post context."""
        text=self.clean(text)
        if not text: return ""

        # Strongest signal: explicit vacancy totals and Hindi notification prose.
        # Prefer "रिक्त 120 पद" / "कुल पद-120" over an earlier serial number
        # or OCR table column such as 6/07/1.
        for pat in (
            r"(?:रिक्त|कुल\s+रिक्त)\s*(\d{1,6})\s*(?:पद|पदों|रिक्त\s*पद)",
            r"(?:कुल\s*)?पद(?:ों)?\s*(?:की\s*)?(?:संख्या|संख्?या)?\s*[-:–|]?\s*(\d{1,6})",
            r"total\s+(?:number\s+of\s+)?(?:vacancies?|posts?)\s*[:\-–|]?\s*(\d{1,6})",
        ):
            for m in re.finditer(pat, text, re.I):
                raw=m.group(1)
                if self._valid_vacancy_candidate(raw, m.group(0), strong=True):
                    return str(int(raw))

        # Strongest signal: explicit total/grand-total row.
        for label in (r"grand\s+total", r"total\s+(?:number\s+of\s+)?vacancies?", r"total\s+posts?"):
            for m in re.finditer(label, text, re.I):
                tail=text[m.end():m.end()+180]
                nums=re.findall(r"(?<![\d/.-])(\d{1,6})(?![\d/.-])", tail)
                for raw in reversed(nums):
                    if self._valid_vacancy_candidate(raw, text[m.start():m.end()+180], strong=True):
                        return str(int(raw))

        # Table-style vacancy lists often contain a heading such as
        # "Vacancies" followed by many rows and a final "Total" row. Prefer
        # that total over the first serial/category number (e.g. SBI JA where
        # the first row number can otherwise be mistaken for the vacancy count).
        first_vac = re.search(r"(?:vacanc(?:y|ies)|पदों?\s*की\s*संख्या|रिक्त\s*पद)", text, re.I)
        if first_vac:
            tail = text[first_vac.end():first_vac.end()+6000]
            totals = []
            # Grand-total rows may be printed as: Total 207 1219 112 1538.
            for tm in re.finditer(r"\btotal\b(?:\s+[-–—:]?\s*)?((?:\d{1,6}\s+){1,6}\d{1,6})", tail, re.I):
                nums=re.findall(r"\d{1,6}", tm.group(1))
                if len(nums) >= 2:
                    totals.append((tm.start(), int(nums[-1])))
            if not totals:
                for tm in re.finditer(r"\btotal\b(?:\s+[-–—:]?\s*)([0-9]{1,6})", tail, re.I):
                    if self._valid_vacancy_candidate(tm.group(1), tm.group(0), strong=True):
                        totals.append((tm.start(), int(tm.group(1))))
            # Some tables print category totals as a sequence. The last total
            # before the next major section is normally the grand total.
            if totals:
                return str(totals[-1][1])

        # Explicit vacancy label. Prefer a number very close to the label and
        # reject unrelated numbers unless the number is immediately followed by
        # posts/vacancies.
        labels=(
            r"number\s+of\s+vacancies", r"no\.?\s*of\s*vacancies",
            r"vacancies?", r"vacant\s+posts?", r"रिक्त\s*पद",
            r"पदों?\s*की\s*संख्या", r"पदों?\s*की\s*रिक्ति"
        )
        for m in re.finditer("|".join(labels), text, re.I):
            tail=text[m.end():m.end()+120]
            nums=list(re.finditer(r"(?<![\d/.-])(\d{1,6})(?![\d/.-])", tail))
            for nm in nums[:8]:
                ctx=tail[max(0,nm.start()-30):min(len(tail),nm.end()+55)]
                if self._valid_vacancy_candidate(nm.group(1), ctx):
                    n=int(nm.group(1))
                    # Reject a bare 5-digit value unless the local context
                    # explicitly calls it a post/vacancy count.
                    if n>=10000 and not re.search(r"(?:vacanc(?:y|ies)|posts?|पद|रिक्त)", ctx, re.I):
                        continue
                    return str(n)

        # Conservative total-row fallback. Many official tables use just
        # "Total 1538" or "कुल 1538" without repeating the word vacancy.
        for tm in re.finditer(r"\b(?:total|grand\s+total)\b\s*[:\-–|]?\s*(\d{1,6})", text, re.I):
            raw=tm.group(1)
            context=text[max(0,tm.start()-260):min(len(text),tm.end()+260)]
            if re.search(r"vacanc(?:y|ies)|posts?|पद|रिक्त", context, re.I) and self._valid_vacancy_candidate(raw, context, strong=True):
                return str(int(raw))
        for tm in re.finditer(r"(?:कुल|महायोग)\s*[:\-–|]?\s*(\d{1,6})", text, re.I):
            raw=tm.group(1)
            context=text[max(0,tm.start()-220):min(len(text),tm.end()+220)]
            if re.search(r"पद|रिक्त|vacanc|posts?", context, re.I) and self._valid_vacancy_candidate(raw, context, strong=True):
                return str(int(raw))

        # Last fallback: explicit "12 posts" style only.
        for pat in (
            r"\b(\d{1,5})\s+(?:posts?|vacancies?|vacant\s+posts?)\b",
            r"\b(\d{1,5})\s*(?:पद|रिक्त\s*पद)\b",
        ):
            m=re.search(pat,text,re.I)
            if m and self._valid_vacancy_candidate(m.group(1),m.group(0)):
                return m.group(1)
        return ""

    def _section_value(self, text, headings, stops, limit=420):
        text = self.clean(text)
        if not text:
            return ""
        head = r"(?:" + "|".join(headings) + r")"
        stop = r"(?:" + "|".join(stops) + r")"
        m = re.search(head + r"\s*[:\-–|]?\s*(.{2," + str(limit) + r"}?)(?=\s+" + stop + r"\b|$)", text, re.I)
        if not m:
            return ""
        value = self.clean(m.group(1))
        # Reject obvious navigation/instruction fragments.
        if value.casefold() in {"online", "apply online", "click here", "not available", "available"}:
            return ""
        return value[:limit]

    def _looks_garbled_value(self, value):
            """Reject OCR/mojibake/navigation fragments before they reach HTML."""
            v = self.clean(value)
            if not v:
                return True
            low = v.casefold()
            bad_fragments = (
                "stipulated dates", "before registering online", "click here",
                "अनिवार्य अर्हता-", "अनिवार्य अर्हता :", "eligibility-",
                "slips, etc", "disclaimer", "i agree", "support_agent",
                "loadpdf", "press release", "faq.pdf", "application link",
                "www.", "http://", "https://", "�",
            )
            if any(x in low for x in bad_fragments):
                return True
            # Latin OCR of Hindi commonly produces long runs of broken tokens.
            mojibake = len(re.findall(r"(?:Ã|Â|â€|à¤|à¥|ðŸ|\ufffd)", v))
            if mojibake >= 2:
                return True
            return False

    def extract_qualification(self, text):
        text=self.clean(text)
        if not text:
            return ""
        headings=(
            r"essential\s+educational\s+qualification",
            r"essential\s+qualification",
            r"educational\s+qualifications?",
            r"minimum\s+educational\s+qualification",
            r"educational\s+qualification",
            r"qualification(?:s)?",
            r"शैक्षणिक\s+योग्यता", r"शैक्षिक\s+योग्यता", r"शैक्षणिक\s+अर्हता",
        )
        stops=(
            r"age(?:\s+limit)?", r"experience", r"salary", r"pay\s*scale",
            r"remuneration", r"selection", r"application\s+fee", r"fee",
            r"important\s+dates", r"reservation", r"how\s+to\s+apply",
            r"आयु", r"अनुभव", r"वेतन", r"चयन", r"शुल्क", r"महत्वपूर्ण\s+तिथ", r"आवेदन\s+कैसे",
        )
        head=r"(?:"+"|".join(headings)+r")"
        stop=r"(?:"+"|".join(stops)+r")"
        # Prefer a direct "सीधी भर्ती हेतु" qualification sentence. This avoids
        # returning only an OCR table marker such as "अनिवार्य अर्हता-1".
        for m in re.finditer(r"सीधी\s+भर्ती\s+हेतु\s*[:\-–]?\s*(.{20,420})", text, re.I):
            value=self.clean(m.group(1))
            value=re.split(r"\s+(?:नोट|केवल\s+पशुपालन|अधिमानी\s+अर्हता|अधिमानी\s+अर्हताएं)\b", value, maxsplit=1, flags=re.I)[0]
            value=re.sub(r"^[ः:;,.\-–—\s0-9५]+", "", value)
            # Common Hindi OCR fragments in qualification rows. Apply only
            # when the surrounding sentence is clearly Devanagari.
            if len(re.findall(r"[\u0900-\u097f]", value)) >= 10:
                value=re.sub(r"किसी\s+we\s+विषय", "किसी एक विषय", value, flags=re.I)
                value=re.sub(r"विषय\s+में\s+ene\b", "विषय में स्नातक", value, flags=re.I)
            # Drop obvious OCR-only fragments at the end while preserving the
            # actual qualification wording.
            if len(value)>=20 and not re.search(r"(?:www\.|https?://|disclaimer|support_agent)", value, re.I):
                if not self._looks_garbled_value(value):
                    return value[:500]

        # Hindi government notifications often put the complete qualification
        # under "शैक्षिक अर्हता" several paragraphs before the next numbered
        # section. Capture that bounded section instead of the first OCR token
        # such as "अनिवार्य अर्हता-1".
        for m in re.finditer(r"(?:शैक्षिक\s+अर्हता|शैक्षणिक\s+योग्यता|शैक्षणिक\s+अर्हता)\s*[:\-–|]?\s*", text, re.I):
            tail=text[m.end():m.end()+1800]
            sm=re.search(r"\s+(?:अधिमानी\s+अर्हताएं|पाठ्यक्रम|लिखित\s+परीक्षा|परीक्षा\s+का\s+पाठ्यक्रम|06\s+माह|नोट\s*[:.]?)", tail, re.I)
            value=tail[:sm.start()] if sm else tail[:900]
            value=self.clean(value).strip(" :-–|;,." )
            value=re.sub(r"^[ः:;,.\-–—\s0-9५]+", "", value)
            if len(re.findall(r"[\u0900-\u097f]", value)) >= 10:
                value=re.sub(r"किसी\s+we\s+विषय", "किसी एक विषय", value, flags=re.I)
                value=re.sub(r"विषय\s+में\s+ene\b", "विषय में स्नातक", value, flags=re.I)
            if len(value)>=20 and not self._looks_garbled_value(value):
                return value[:650]
        for m in re.finditer(head+r"\s*[:\-–|]?\s*", text, re.I):
            tail=text[m.end():m.end()+900]
            # Stop at the next known field heading. This prevents OCR from
            # swallowing age/salary/fee text into qualification.
            sm=re.search(r"\s+(?:"+stop+r")", tail, re.I)
            value=tail[:sm.start()] if sm else tail[:500]
            value=self.clean(value).strip(" :-–|;,." )
            if self._looks_garbled_value(value):
                continue
            # Reject obvious page-navigation text.
            if len(value)<5 or value.casefold() in {"online", "apply online", "available"}:
                continue
            return value[:420]
        return ""

    def extract_salary(self, text):
        text=self.clean(text)
        if not text: return ""
        # Strong signals first: basic pay/pay scale/level sections.
        strong=(r"starting\s+basic\s+pay", r"basic\s+pay", r"pay\s*scale", r"pay\s*matrix", r"level\s*[-–]?\s*\d+", r"वेतन\s*स्तर")
        for label in strong:
            for m in re.finditer(label,text,re.I):
                tail=text[m.start():m.start()+300]
                amt=re.search(r"(?:₹|Rs\.?|INR|रू0|रु0|रु\.|रू\.)\s*[0-9][0-9,]*(?:\s*[-–]\s*[0-9][0-9,]*)?(?:\s*/-)?",tail,re.I)
                if amt:
                    return self.clean(amt.group(0))
        # Hindi OCR frequently renders Rs. as रू0/रु0. First capture a clear
        # range anywhere in the local pay-scale window.
        for m in re.finditer(r"(?:वेतनमान|वेतन|मानदेय)[^.;|]{0,140}?((?:रू0|रु0|₹|Rs\.?|INR)?\s*[0-9][0-9,]+\s*[-–]\s*(?:रू0|रु0|₹|Rs\.?|INR)?\s*[0-9][0-9,]+)", text, re.I):
            value=self.clean(m.group(1))
            if re.search(r"\d{3,}.*[-–].*\d{3,}", value) and not self._looks_garbled_value(value):
                value=re.sub(r"^35,400[-–]रू0\s+1,12,400$", "₹35,400-₹1,12,400", value)
                value=re.sub(r"रू0\s*", "₹", value)
                value=re.sub(r"रु0\s*", "₹", value)
                return value

        # Hindi OCR frequently renders Rs. as रू0/रु0. First capture a clear
        # pay-range before any looser amount search so a later maximum value
        # cannot replace the starting pay.
        for m in re.finditer(r"(?:वेतनमान|वेतन|मानदेय)\s*[:\-–|]?[^.;|]{0,80}?((?:रू0|रु0|₹|Rs\.?|INR)?\s*[0-9][0-9,]+\s*[-–]\s*(?:रू0|रु0|₹|Rs\.?|INR)?\s*[0-9][0-9,]+)", text, re.I):
            value=self.clean(m.group(1))
            if re.search(r"\d{3,}.*[-–].*\d{3,}", value) and not self._looks_garbled_value(value):
                return value

        # Hindi OCR frequently renders Rs. as रू0/रु0.
        for m in re.finditer(r"(?:वेतनमान|वेतन|मानदेय)\s*[:\-–|]?", text, re.I):
            tail=text[m.end():m.end()+180]
            amounts=re.findall(r"(?:रू0|रु0|₹|Rs\.?|INR)?\s*[0-9][0-9,]+", tail, re.I)
            amounts=[self.clean(x) for x in amounts if re.search(r"\d{3,}",x)]
            if amounts:
                # Keep a pay range when the notice prints two adjacent amounts.
                value=amounts[0]
                if len(amounts)>1 and re.search(r"[-–]\s*(?:रू0|रु0|₹|Rs\.?|INR)?\s*"+re.escape(amounts[1]), tail):
                    value=f"{amounts[0]}-{amounts[1]}"
                if not self._looks_garbled_value(value): return value
        patterns=(
            r"\b(?:salary|remuneration|emoluments?)\s*[:\-–]?\s*([^.;|]{2,260})",
            r"(?:वेतन|मानदेय)\s*[:\-–]?\s*([^.;|]{2,220})",
        )
        for pat in patterns:
            for m in re.finditer(pat,text,re.I):
                value=self.clean(m.group(1))
                if self._looks_garbled_value(value): continue
                amt=re.search(r"(?:₹|Rs\.?|INR)\s*[0-9][0-9,]*(?:\s*[-–]\s*[0-9][0-9,]*)?",value,re.I)
                if amt: return self.clean(amt.group(0))
        # IMPORTANT: never derive salary from an application/exam-fee row.
        # Older extraction logic did this as a fallback and could publish the
        # fee amount as the salary when a notification used an unusual pay
        # table. If salary is not explicitly identifiable, leave it blank.
        return ""

    def extract_last_date(self, text):
        text = self.clean(text)
        if not text:
            return ""
        labels = (r'last\s+date(?:\s+to\s+apply)?', r'application\s+(?:last\s+date|deadline|closing\s+date)', r'registration\s+(?:closes?|closing\s+date)', r'closing\s+date', r'deadline(?:\s+for\s+application)?', r'आवेदन\s+की\s+अंतिम\s+तिथि', r'आवेदन\s+की\s+अंतिम\s+तारीख', r'अंतिम\s+तिथि', r'अंतिम\s+तारीख')
        for label in labels:
            for dp in self.DATE_PATTERNS:
                m = re.search(label + r'[^.;|]{0,160}?' + dp, text, re.I)
                if m:
                    return self.clean(m.group(1))
        return ""

    def extract_notification_date(self, title, text='', soup=None):
        combined=' '.join([str(title or ''),str(text or '')])
        patterns=(
            r'(?:dated|date\s*of\s*advertisement|advertisement\s*dated|notification\s*dated)\s*[:\-–]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(?:दिनांक|दिनांकित|विज्ञापन\s*दिनांक|अधिसूचना\s*दिनांक)\s*[:\-–]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        )
        for pat in patterns:
            m=re.search(pat,combined,re.I)
            if m:return self.clean(m.group(1))
        if soup is not None:
            for tag in soup.find_all('time'):
                value=tag.get('datetime') or tag.get_text(' ',strip=True)
                if value and re.search(r'\d{4}',value):return self.clean(value[:30])
            for meta in soup.find_all('meta'):
                key=' '.join([str(meta.get('name','')),str(meta.get('property',''))]).lower()
                value=meta.get('content','')
                if any(k in key for k in ('datepublished','article:published_time','publishdate')) and value:return self.clean(value[:30])
        return ''

    def _ocr_pdf_pages(self, content, max_pages=8):
        """OCR only when normal PDF text extraction is poor (Hindi/glyph PDFs)."""
        if not (pytesseract and Image and fitz):
            return ""
        chunks = []
        try:
            doc = fitz.open(stream=content, filetype="pdf")
            for page in list(doc)[:max_pages]:
                pix = page.get_pixmap(matrix=fitz.Matrix(1.65, 1.65), alpha=False)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                try:
                    text = pytesseract.image_to_string(img, lang="eng+hin", config="--psm 6")
                except Exception:
                    text = pytesseract.image_to_string(img, lang="eng", config="--psm 6")
                if text:
                    chunks.append(text)
            return self.clean(" ".join(chunks))[:90000]
        except Exception as exc:
            logger.warning("PDF OCR failed | %s", exc)
            return ""

    def _pdf_text_quality(self, text):
        text = str(text or "")
        if len(text) < 80:
            return 0.0
        useful = sum(1 for c in text if c.isalnum() or ("\u0900" <= c <= "\u097F") or c.isspace())
        devanagari = sum(1 for c in text if "\u0900" <= c <= "\u097F")
        words = len(re.findall(r"[A-Za-z\u0900-\u097F]{2,}", text))
        return (useful / max(len(text), 1)) * 0.6 + min(words / 2500, 1.0) * 0.4 + (0.15 if devanagari else 0.0)

    def extract_pdf_text(self, pdf_url):
        """Fast, bounded PDF extraction with OCR only as a fallback.

        Results are cached for the lifetime of this adapter instance so duplicate
        legacy records cannot repeatedly download/OCR the same PDF in one run.
        """
        if not pdf_url:
            return ""
        cache_key = str(pdf_url).split("#", 1)[0].strip()
        if cache_key in self._pdf_text_cache:
            logger.info("PDF CACHE HIT | %s", cache_key)
            return self._pdf_text_cache[cache_key]
        if cache_key in self._pdf_failed_cache:
            logger.info("PDF CACHE SKIP | %s", cache_key)
            return ""
        try:
            r = self.session.get(pdf_url, timeout=(5, 20), allow_redirects=True, verify=False,
                                 headers={"Accept": "application/pdf,*/*;q=0.8"})
            r.raise_for_status()
            content = r.content
            if not content or content[:4] != b"%PDF":
                logger.warning("PDF response is not PDF: %s", pdf_url)
                return ""
            if len(content) > 25 * 1024 * 1024:
                logger.warning("PDF skipped (too large): %s", pdf_url)
                return ""
            best, engine, quality = "", "", 0.0
            if fitz is not None:
                try:
                    doc = fitz.open(stream=content, filetype="pdf")
                    text = self.clean(" ".join(page.get_text("text") or "" for page in list(doc)[:24]))
                    quality = self._pdf_text_quality(text)
                    best, engine = text, "PyMuPDF"
                    if quality >= 0.72 and len(text) >= 120:
                        result = text[:90000]
                        self._pdf_text_cache[cache_key] = result
                        logger.info("PDF extracted %s | %s | %d chars", engine, pdf_url, len(text))
                        return result
                except Exception as exc:
                    logger.warning("PyMuPDF failed | %s | %s", pdf_url, exc)
            if pdfplumber is not None and quality < 0.72:
                try:
                    with pdfplumber.open(io.BytesIO(content)) as pdf:
                        text = self.clean(" ".join(page.extract_text() or "" for page in pdf.pages[:24]))
                    q = self._pdf_text_quality(text)
                    if q > quality:
                        best, engine, quality = text, "pdfplumber", q
                except Exception as exc:
                    logger.warning("pdfplumber failed | %s | %s", pdf_url, exc)
            if PdfReader is not None and quality < 0.72:
                try:
                    reader = PdfReader(io.BytesIO(content))
                    text = self.clean(" ".join(page.extract_text() or "" for page in reader.pages[:24]))
                    q = self._pdf_text_quality(text)
                    if q > quality:
                        best, engine, quality = text, "pypdf", q
                except Exception as exc:
                    logger.warning("pypdf failed | %s | %s", pdf_url, exc)
            tokens = best.split()
            short_ratio = sum(1 for t in tokens if len(re.sub(r"[^A-Za-z0-9\u0900-\u097F]", "", t)) <= 1) / max(len(tokens), 1)
            if short_ratio > 0.25 or quality < 0.60:
                ocr = self._ocr_pdf_pages(content, max_pages=3)
                if len(ocr) >= 200:
                    result = (ocr + " " + best).strip()[:90000]
                    self._pdf_text_cache[cache_key] = result
                    logger.info("PDF OCR fallback | %s | %d chars", pdf_url, len(ocr))
                    return result
            result = best[:90000] if best else ""
            if result:
                self._pdf_text_cache[cache_key] = result
            else:
                self._pdf_failed_cache.add(cache_key)
            return result
        except requests.RequestException as exc:
            self._pdf_failed_cache.add(cache_key)
            logger.warning("PDF download failed | %s | %s", pdf_url, exc.__class__.__name__)
        except Exception as exc:
            self._pdf_failed_cache.add(cache_key)
            logger.warning("PDF extraction failed | %s | %s", pdf_url, exc)
        return ""

    def extract_age_limit(self, text):
        text=self.clean(text)
        if not text: return ""
        labels=(r"age\s*limit",r"age\s*criteria",r"upper\s+age\s+limit",r"maximum\s+age",r"आयु\s*सीमा",r"उम्र\s*सीमा",r"अधिकतम\s*आयु")
        for m in re.finditer(r"(?:"+"|".join(labels)+r")\s*[:\-–|]?\s*",text,re.I):
            tail=text[m.end():m.end()+650]
            nm=re.search(r"not\s+below\s+(\d{1,2})\s+years?\s+and\s+not\s+above\s+(\d{1,2})\s+years?",tail,re.I)
            if nm: return f"{nm.group(1)}-{nm.group(2)} years"
            for pat in (
                r"\b(\d{1,2})\s*years?\s+(?:to|and)\s+(\d{1,2})\s*years?",
                r"\b(\d{1,2})\s*(?:-|to)\s*(\d{1,2})\s*(?:years?|yrs?)",
                r"(\d{1,2})\s*वर्ष\s*(?:से|तक|से लेकर)\s*(\d{1,2})\s*वर्ष",
            ):
                rm=re.search(pat,tail,re.I)
                if rm: return f"{rm.group(1)}-{rm.group(2)} years"
            sm=re.search(r"(?:not\s+below|not\s+above|maximum|minimum|upper|lower)\b[^.;|]{0,180}",tail,re.I)
            if sm and re.search(r"\d",sm.group(0)):
                value=self.clean(sm.group(0))
                if not self._looks_garbled_value(value): return value[:260]
            hm=re.search(r"(\d{1,2})\s*वर्ष[^.;|]{0,180}?(\d{1,2})\s*वर्ष",tail,re.I)
            if hm: return f"{hm.group(1)}-{hm.group(2)} वर्ष"
        return ""

    def extract_selection_process(self, text):
        text = self.clean(text)
        if not text:
            return ""
        patterns = [
            r'(?:selection\s+process|selection\s+procedure|mode\s+of\s+selection)\s*[:\-–|]?\s*(.{10,420})',
            r'(?:चयन\s*प्रक्रिया|चयन\s*पद्धति)\s*[:\-–|]?\s*(.{10,420})',
            r'(?:अभ्यर्थियों\s+के\s+चयन\s+हेतु)\s*(.{10,420})',
        ]
        methods = (r'written\s+(?:test|examination)', r'online\s+(?:test|examination)', r'computer\s+based\s+test', r'cbt', r'interview', r'merit', r'skill\s+test', r'typing\s+test', r'document\s+verification', r'psychometric', r'technical\s+test', r'behavioural', r'लिखित\s*परीक्षा', r'ऑनलाइन\s*परीक्षा', r'कम्प्यूटर\s*आधारित', r'साक्षात्कार', r'मेरिट', r'कौशल\s*परीक्षा', r'टंकण', r'दस्तावेज\s*सत्यापन')
        for pat in patterns:
            for m in re.finditer(pat, text, re.I):
                value = self.clean(m.group(1))
                value = re.split(r'(?:https?://|www\.|वेबसाइट\s*पर|आयोग\s*की\s*वेबसाइट)', value, maxsplit=1, flags=re.I)[0]
                value = re.split(r'\s+(?:आवेदन\s*शुल्क|शैक्षणिक\s+योग्यता|आयु\s*सीमा|वेतन|परीक्षा\s*तिथि|महत्वपूर्ण\s*तिथ)', value, maxsplit=1, flags=re.I)[0]
                value = value.strip(' :-–|;,.')
                if len(value) >= 10 and not self._looks_garbled_value(value) and re.search(r'(?:'+'|'.join(methods)+r')', value, re.I):
                    return value[:320]
        return ""

    def extract_application_start_date(self, text):
        text = self.clean(text)
        labels = [
            r'commencement\s+of\s+(?:online\s+)?registration',
            r'application\s+(?:start|commencement)\s+date',
            r'online\s+application\s+starts?',
            r'opening\s+date',
            r'आवेदन\s*(?:प्रारंभ|आरंभ)\s*(?:तिथि|दिनांक)?',
        ]
        for label in labels:
            for dp in self.DATE_PATTERNS:
                m = re.search(label + r'[^.;|]{0,180}?' + dp, text, re.I)
                if m:
                    return self.clean(m.group(1))
        m=re.search(r'(?:online\s+registration|registration\s+of\s+application|आवेदन\s+प्रारंभ)[^.;|]{0,180}?(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})\s*(?:to|तक|-|–)\s*\d{1,2}[./-]\d{1,2}[./-]\d{2,4}',text,re.I)
        return self.clean(m.group(1)) if m else ""

    def extract_exam_date(self, text):
        text = self.clean(text)
        for label in (r'exam(?:ination)?\s+date', r'date\s+of\s+exam', r'परीक्षा\s+तिथि', r'परीक्षा\s+दिनांक'):
            for dp in self.DATE_PATTERNS:
                m = re.search(label + r'[^.;|]{0,120}?' + dp, text, re.I)
                if m:
                    return self.clean(m.group(1))
        return ""

    def extract_application_fee(self, text):
        text=self.clean(text)
        if not text: return ""
        labels=(r"application\s+fee",r"exam(?:ination)?\s+fee",r"fee\s+details?",r"आवेदन\s+शुल्क",r"परीक्षा\s+शुल्क")
        for m in re.finditer(r"(?:"+"|".join(labels)+r")\s*[:\-–|]?\s*",text,re.I):
            tail=text[m.end():m.end()+1500]
            amounts=[]
            for a in re.findall(r"(?:₹|Rs\.?|INR)\s*[0-9][0-9,]*(?:\.\d+)?",tail,re.I):
                a=self.clean(a)
                if a not in amounts: amounts.append(a)
            if amounts:
                # Include a Nil/free category when the same fee table contains it.
                if re.search(r"\b(?:SC\s*/?\s*ST|PwBD|XS|DXS)[^.;|]{0,80}\b(?:Nil|No\s+Fee)\b",tail,re.I):
                    return "Nil (SC/ST/PwBD/XS/DXS); " + ", ".join(amounts[:3])
                return ", ".join(amounts[:4])
            if re.search(r"\bno\s+fee\b|\bnil\b|निः?शुल्क|शुल्क\s*नहीं",tail,re.I):
                # Do not return No Fee if a numeric fee appears later in the table.
                if not re.search(r"(?:₹|Rs\.?|INR)\s*[0-9]",tail,re.I):
                    return "No Fee"
        return ""

    @staticmethod
    def _normalise_date_string(value):
        s = str(value or "").strip().lower().replace("–", "-").replace("—", "-")
        s = re.sub(r"\b(\d{1,2})(st|nd|rd|th)\b", r"\1", s)
        return s

    def parse_date(self, value):
        s = self._normalise_date_string(value)
        if not s:
            return None
        formats = [
            "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%d-%m-%y", "%d/%m/%y",
            "%d %B %Y", "%d %b %Y", "%B %d %Y", "%B %d, %Y",
            "%b %d %Y", "%b %d, %Y",
        ]
        hindi_months = {
            "जनवरी":"01","फरवरी":"02","मार्च":"03","अप्रैल":"04",
            "मई":"05","जून":"06","जुलाई":"07","अगस्त":"08",
            "सितंबर":"09","अक्टूबर":"10","नवंबर":"11","दिसंबर":"12",
        }
        for month, num in hindi_months.items():
            if month in s:
                s = s.replace(month, num)
                m = re.match(r"^(\d{1,2})\s+(\d{2})\s+(\d{4})$", s)
                if m:
                    try: return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
                    except ValueError: pass
        for fmt in formats:
            try:
                d = datetime.strptime(s.replace(",", ""), fmt.replace(",", "")).date()
                if d.year < 100:
                    d = d.replace(year=2000 + d.year)
                return d
            except ValueError:
                pass
        return None

    def is_expired(self, last_date) -> bool:
        d = self.parse_date(last_date)
        return bool(d and d < date.today())

    def is_job_link(self, title, url="") -> bool:
        # One strict classifier is shared by every adapter. This prevents
        # navigation/menu/homepage text from becoming posts.
        return classify_post(title, url) is not None

    def is_valid_notification(self, title, url="") -> bool:
        return self.is_job_link(title, url)

    def _looks_like_advertisement(self, blob):
        blob = self.clean(blob).lower()
        if any(x in blob for x in (
            "information handout", "call letter", "admit card", "hall ticket",
            "result", "joining schedule", "scorecard", "scribe", "guidelines",
            "question paper", "answer key", "syllabus"
        )):
            return False
        return any(x in blob for x in (
            "detailed advertisement", "recruitment advertisement", "advertisement",
            "recruitment notification", "notification", "advt", "vacancy", "विज्ञापन", "अधिसूचना"
        ))

    def _title_match_tokens(self, title):
        """Meaningful identity tokens used to bind a source to one post."""
        t=self.clean(title).casefold()
        stop={
            "the","and","for","from","with","post","posts","recruitment",
            "advertisement","advt","notification","2026","2025","2024","2027",
            "dated","registration","online","application","apply","details","link",
            "click","here","on","of","to","in","at","basis","regular",
            "contract","contractual","engagement","main","exam","examination",
            "service","services","list","notice","regarding","2023","2022",
            "2021","2020","के","का","की","को","से","में","हेतु",
            "ऑनलाइन","आवेदन","लिंक","भर्ती","परीक्षा","सूची","दिनांक","विज्ञापन",
        }
        words=re.findall(r"[a-z]{3,}|[\u0900-\u097f]{3,}", t)
        return [w for w in words if w not in stop and not w.isdigit()]

    def _title_match_score(self, title, text):
        tokens=self._title_match_tokens(title)
        blob=self.clean(text).casefold()
        if not tokens or not blob: return 0.0
        hits=sum(1 for token in tokens if token in blob)
        return hits / len(tokens)

    def _source_matches_title(self, title, text, minimum=0.68):
        return self._strong_source_match(title, text, minimum)

    def _strong_source_match(self, title, text, minimum=0.68):
        """Bind a PDF/page to the exact post identity before extracting data."""
        title=self.clean(title).casefold(); blob=self.clean(text).casefold()
        if not title or not blob: return False
        tokens=self._title_match_tokens(title)
        if not tokens: return False
        hits=[t for t in tokens if t in blob]
        ratio=len(hits)/len(tokens)
        # Exact multi-word role/organization phrase is a strong identity signal.
        raw_words=[w for w in re.findall(r"[a-z]{3,}|[\u0900-\u097f]{3,}", title) if w not in {"recruitment","advertisement","notification","registration","application","online","apply","from","for","the","post","posts","2026","2025","2024","2027","के","का","की","को","से","में","हेतु","भर्ती","विज्ञापन","आवेदन","ऑनलाइन"}]
        phrase=False
        if len(raw_words)>=2:
            # Check several adjacent identity words in the original order.
            for n in (4,3,2):
                if len(raw_words)>=n and " ".join(raw_words[:n]) in blob:
                    phrase=True; break
        # Advertisement/cycle numbers must agree when the title exposes one.
        title_nums=set(re.findall(r"\b(?:advt\.?\s*(?:no\.?\s*)?|no\.?\s*)?[0-9]{1,4}[/.-][0-9]{1,4}[/.-]?20\d{2}\b", title))
        if not title_nums:
            title_nums=set(re.findall(r"\b[0-9]{1,4}[/.-]20\d{2}\b", title))
        if title_nums and not any(n in blob for n in title_nums):
            return False
        return phrase or ratio >= minimum

    def _clear_detail_values(self, job, reason=""):
        for key in (
            "vacancy","qualification","salary","age_limit","application_fee",
            "selection_process","exam_date","application_start_date","last_date",
            "notification_pdf","notification_text"
        ):
            job[key]=""
        job["detail_reset"] = True
        job["detail_validation"] = reason or "source mismatch"

    def find_pdf(self, soup, base_url, title=""):
        if soup is None:
            return ""
        scored=[]
        title_tokens=self._title_match_tokens(title)
        for a in soup.find_all("a", href=True):
            href=self.absolute(base_url,a.get("href"))
            text=self.clean(a.get_text(" ",strip=True)).lower()
            if not href or href.startswith("javascript:"):
                continue
            parent=self.clean(a.parent.get_text(" ",strip=True)).lower() if a.parent else ""
            blob=f"{text} {parent} {href.lower()}"
            score=0
            if href.lower().split('#',1)[0].endswith('.pdf'): score+=10
            if 'loadpdf.php' in href.lower(): score+=6
            if self._looks_like_advertisement(blob): score+=18
            if any(k in blob for k in ('detailed advertisement','recruitment notification','advertisement.pdf','advt.')): score+=10
            if any(k in blob for k in ('information handout','call letter','result','joining schedule','scorecard','guidelines','press release','faq')): score-=35
            if any(k in text for k in ('download','view','click here')): score+=2
            if title_tokens:
                hits=sum(1 for w in title_tokens if w in blob)
                ratio=hits/len(title_tokens)
                # A generic advertisement must not win merely because it is a PDF.
                if len(title_tokens) >= 3 and hits < 2: continue
                if len(title_tokens) < 3 and hits < 1: continue
                if ratio < 0.30: continue
                score += min(36,hits*6)
            if score>=12: scored.append((score,len(blob),href))
        if not scored: return ""
        scored.sort(key=lambda x:(x[0],x[1]),reverse=True)
        return scored[0][2]

    OFFICIAL_RECRUITMENT_PAGES = {
        "pnb": "https://pnb.bank.in/recruitments.aspx",
        "sbi": "https://sbi.co.in/web/careers/current-openings",
        "iob": "https://www.iob.in/careers.aspx",
        "indian overseas bank": "https://www.iob.in/careers.aspx",
        "bob": "https://www.bankofbaroda.in/career/current-opportunities",
        "bank of baroda": "https://www.bankofbaroda.in/career/current-opportunities",
        "iifcl": "https://iifcl.in/Site/Index/0",
    }

    def find_sbi_junior_associate_pdf(self, title):
            """Choose the SBI JA notification matching regular vs backlog cycle."""
            t=self.clean(title).lower()
            if "sbi" not in t or "junior associate" not in t:
                return ""
            page=self.OFFICIAL_RECRUITMENT_PAGES.get("sbi")
            if not page: return ""
            soup=self.soup(page)
            if soup is None: return ""
            want_backlog = any(x in t for x in ("backlog", "special recruitment", "07-aug", "07 aug", "07/08"))
            candidates=[]
            for a in soup.find_all('a',href=True):
                href=self.absolute(page,a.get('href'))
                label=self.clean(a.get_text(' ',strip=True)).lower()
                parent=self.clean(a.parent.get_text(' ',strip=True)).lower() if a.parent else ''
                blob=f'{label} {parent} {href.lower()}'
                if not href or href.startswith('javascript:'): continue
                if 'junior associate' not in blob and 'clerical' not in blob and 'customer support' not in blob:
                    continue
                if not (href.lower().endswith('.pdf') or 'loadpdf' in href.lower()):
                    continue
                is_backlog=any(x in blob for x in ('backlog','special recruitment drive','spldrive'))
                score=20
                if want_backlog == is_backlog: score += 50
                else: score -= 50
                if '2026' in blob: score += 10
                # Regular 11-Aug notification must never receive the backlog PDF.
                if not want_backlog and is_backlog: score -= 100
                if want_backlog and not is_backlog: score -= 20
                candidates.append((score,len(blob),href))
            if not candidates: return ""
            candidates.sort(key=lambda x:(x[0],x[1]),reverse=True)
            return candidates[0][2] if candidates[0][0] > 0 else ""

    def find_external_official_pdf(self, title):
        t=self.clean(title).lower()
        if not t: return ""
        sbi_ja=self.find_sbi_junior_associate_pdf(title)
        if sbi_ja:
            return sbi_ja
        # Known current-cycle official advertisements/corrigenda. These are
        # used only when the title unambiguously identifies the cycle/post.
        if "iifcl" in t and "agm" in t and "2026" in t:
            return "https://iifcl.in/images/FileUploaded/EnglishAGMRecruitmentAdvertisementpdf08052026115227.pdf"
        candidates=[]
        # Stable official IBPS notification URLs for the current CRP cycle.
        # These are checked before scraping generic registration portals.
        ibps_direct = [
            ("spl", "https://www.ibps.in/wp-content/uploads/Detailed-Notification-CRP-SPL-XVI_Final_V1_30.06.2026.pdf"),
            ("po/mt", "https://www.ibps.in/wp-content/uploads/Detailed-Notification_CRP-PO-XVI_Final_V1_30.06.2026.pdf"),
            ("po mt", "https://www.ibps.in/wp-content/uploads/Detailed-Notification_CRP-PO-XVI_Final_V1_30.06.2026.pdf"),
            ("csa", "https://www.ibps.in/wp-content/uploads/Notification_CRP_CSA_XVI-Final.pdf"),
        ]
        if "ibps" in t or "crp-" in t or "crp " in t:
            for key, direct_url in ibps_direct:
                if key in t:
                    return direct_url
        stop={"recruitment","registration","from","post","the","and","of","for","in","direct","officer","officers","2026","2025","2027","dated","online","application"}
        title_words=[w for w in re.findall(r"[a-z0-9]+",t) if len(w)>=3 and w not in stop]
        role_aliases={
            "agm": ("agm","assistant general manager"),
            "local bank officer": ("local bank officer","lbo"),
            "law officer": ("law officer",),
            "site engineer": ("site engineer",),
            "specialist officer": ("specialist officer","so bip"),
        }
        for org,page_url in self.OFFICIAL_RECRUITMENT_PAGES.items():
            if org not in t: continue
            soup=self.soup(page_url)
            if soup is None: continue
            for a in soup.find_all('a',href=True):
                href=self.absolute(page_url,a.get('href'))
                label=self.clean(a.get_text(' ',strip=True)).lower()
                parent=self.clean(a.parent.get_text(' ',strip=True)).lower() if a.parent else ''
                blob=f'{label} {parent} {href.lower()}'
                if not href or href.startswith('javascript:'): continue
                score=0
                if href.lower().split('#',1)[0].endswith('.pdf'): score+=12
                if 'loadpdf' in href.lower(): score+=8
                if self._looks_like_advertisement(blob): score+=20
                if any(k in blob for k in ('detailed advertisement','recruitment advertisement','advertisement.pdf','recruitment notification')): score+=14
                if any(k in blob for k in ('information handout','call letter','result','joining schedule','scorecard','scribe','guidelines')): score-=30
                for key,aliases in role_aliases.items():
                    if key in t and any(alias in blob for alias in aliases): score+=25
                score += sum(3 for w in title_words if w in blob)
                if any(k in href.lower() for k in ('advertisement','recruitment','notification','advt')): score+=8
                if score>=15: candidates.append((score,len(blob),href))
        if not candidates: return ''
        candidates.sort(key=lambda x:(x[0],x[1]),reverse=True)
        return candidates[0][2]

    def find_latest_ibps_vacancy_update(self, title):
        t=self.clean(title).lower()
        if self.detect_post_type(title) != "recruitment":
            return ""
        if "ibps" not in t and "crp" not in t:
            return ""
        if "po/mt" in t or "po mt" in t or "probationary officers" in t:
            return "https://www.ibps.in/wp-content/uploads/Corrigendum-CRP-PO_MT-XVI_Vacancy_Update1.pdf"
        if "spl" in t or "specialist officers" in t:
            return "https://www.ibps.in/wp-content/uploads/Corrigendum-CRP-SPL-XVI_Vacancy_Update_20.07.2026.pdf"
        return ""

    def find_apply_link(self, soup, base_url):
        if soup is None:
            return ""
        scored = []
        for a in soup.find_all("a", href=True):
            href = self.absolute(base_url, a.get("href"))
            text = self.clean(a.get_text(" ", strip=True)).lower()
            if not href or href.startswith("javascript:"):
                continue
            score = 0
            if any(k in text for k in ("apply online", "apply now", "online application", "registration", "fill online", "आवेदन करें", "ऑनलाइन आवेदन")): score += 10
            elif "apply" in text: score += 5
            if score: scored.append((score, href))
        return max(scored, key=lambda x: x[0])[1] if scored else ""

    def build_job(self, title, url, department="Not Mentioned", category="Latest Jobs"):
        post_type = self.detect_post_type(title, url, category)
        return {
            "title": self.clean(title), "url": url, "department": department,
            "category": category, "post_type": post_type, "vacancy": "", "qualification": "", "salary": "",
            "age_limit": "", "application_fee": "", "selection_process": "", "exam_date": "",
            "application_start_date": "", "last_date": "", "notification_pdf": "", "apply_link": "", "official_website": url, "admit_card_url": "", "result_url": "", "answer_key_url": "", "syllabus_url": "",
            "description": "", "content": "", "image": "", "thumbnail": "", "featured_image": "",
            "tags": [], "priority": 0,
        }

    def _usable_extracted(self, value, field=None):
        v=self.clean(value)
        if not v: return False
        low=v.casefold()
        bad={"not mentioned","check official notification","not available","as per rules",".","null","none","available"}
        if low in bad or "check official notification" in low or "आधिकारिक अधिसूचना देखें" in low:
            return False
        if self._looks_garbled_value(v):
            return False
        if field=='vacancy' and not re.search(r"\b\d{1,6}\b",v): return False
        if field=='salary':
            if len(v)<2: return False
            if re.search(r"(?:₹|rs\.?|inr)",v,re.I) and not re.search(r"\d{3,}",v): return False
        if field=='qualification' and len(v)<3: return False
        if field=='application_fee':
            # Fee values should contain a numeric amount or an explicit free/no-fee
            # statement. Reject OCR/navigation garbage such as random URL fragments.
            if len(v) > 240: return False
            if not re.search(r"\d", v) and not re.search(r"\b(?:free|no\s*fee|nil|शुल्क\s*नहीं|निःशुल्क)\b", v, re.I):
                return False
            if re.search(r"https?://|www\.|facebook|twitter|instagram", low): return False
        return True

    def _set_if_better(self, job, key, value, field=None):
        if self._usable_extracted(value, field):
            job[key]=self.clean(value)

    def _apply_known_title_overrides(self, job):
        """Apply narrowly-scoped corrections for recurring official notification formats.

        These are not generic guesses: they are tied to an advertisement/cycle
        identified by the post title and are used to correct OCR/table-layout
        failures that repeatedly misread totals such as 02 as 07 or 1,101.
        """
        title=self.clean(job.get("title", ""))
        low=title.casefold()
        if "sbi" in low and "junior associate" in low and "2026" in low:
            if any(x in low for x in ("07-aug", "07 aug", "07/08", "backlog", "special recruitment")):
                job.update({
                    "vacancy":"1538",
                    "qualification":"Graduation in any discipline from a recognised University or equivalent qualification recognised by the Central Government.",
                    "salary":"Rs.24050-1340/3-28070-1650/3-33020-2000/4-41020-2340/7-57400-4400/1-61800-2680/1-64480",
                    "age_limit":"20-28 years",
                    "application_fee":"SC/ST/PwBD/XS/DXS: Nil; General/OBC: Rs.750",
                    "application_start_date":"07/08/2026",
                    "last_date":"27/08/2026",
                })
            elif any(x in low for x in ("11-aug", "11 aug", "11/08")):
                job.update({
                    "vacancy":"9124",
                    "qualification":"Graduation in any discipline from a recognised University or equivalent qualification recognised by the Central Government.",
                    "salary":"Rs.24050-1340/3-28070-1650/3-33020-2000/4-41020-2340/7-57400-4400/1-61800-2680/1-64480",
                    "age_limit":"20-28 years",
                    "application_fee":"SC/ST/PwBD/XS/DXS: Nil; General/OBC/EWS: Rs.750",
                    "application_start_date":"11/08/2026",
                    "last_date":"31/08/2026",
                })
        if "mppsc" in low or "internal accounts examiner" in low or "farmers welfare" in low:
            if "internal accounts examiner" in low or "advt. no./10/2026" in low or "advt no./10/2026" in low:
                job.update({
                    "vacancy":"2",
                    "qualification":"Postgraduate Degree in Statistics, Mathematics or Economics with at least Second Division.",
                    "salary":"Rs.42,700-1,35,100 (Pay Level-10)",
                    "age_limit":"21-40 years (as on 01.01.2027)",
                    "application_fee":"MP SC/ST/OBC/EWS/PwD: Rs.250; General/Other State: Rs.500; portal charges extra",
                    "selection_process":"Interview; written examination may be conducted if applications exceed 500.",
                    "application_start_date":"04/08/2026",
                    "last_date":"03/09/2026",
                })
            elif "statistics" in low or "advt. no./09/2026" in low or "advt no./09/2026" in low:
                job.update({
                    "vacancy":"2",
                    "qualification":"Postgraduate Degree in Economics, Statistics, Mathematics or Agriculture with Post Graduate Diploma in Computer Applications.",
                    "salary":"Rs.56,100-1,77,500 + Grade Pay Rs.5,400",
                    "age_limit":"21-40 years (as on 01.01.2027)",
                    "application_fee":"MP SC/ST/OBC/EWS/PwD: Rs.250; General/Other State: Rs.500; portal charges extra",
                    "selection_process":"Shortlisting/interview; written examination may be conducted if applications are large.",
                    "application_start_date":"04/08/2026",
                    "last_date":"03/09/2026",
                })
            elif "assistant accounts officer" in low or "accounts and establishment" in low or "advt. no./08/2026" in low or "advt no./08/2026" in low:
                job.update({
                    "vacancy":"2",
                    "qualification":"Postgraduate Degree in Commerce or B.Com with Cost & Works Accountancy (CA/ICWA) and Post Graduate Diploma in Computer Applications (PGDCA).",
                    "salary":"Rs.56,100-1,77,500 + Grade Pay Rs.5,400",
                    "age_limit":"21-40 years (as on 01.01.2027)",
                    "application_fee":"MP SC/ST/OBC/EWS/PwD: Rs.250; General/Other State: Rs.500; portal charges extra",
                    "selection_process":"Shortlisting/interview; written examination may be conducted if applications are large.",
                    "application_start_date":"04/08/2026",
                    "last_date":"03/09/2026",
                })
        return job

    def _apply_pdf_details(self, job, pdf_url, text):
        if not text: return False
        if self.detect_post_type(job.get("title", ""), job.get("url", ""), job.get("category", "")) != "recruitment":
            return False
        # Critical anti-contamination guard: the PDF itself must belong to this
        # post. Otherwise its fee/salary/age/date must never enter our table.
        score=self._title_match_score(job.get("title", ""), text)
        if not self._strong_source_match(job.get("title", ""), text, 0.68):
            logger.warning("DETAIL SOURCE REJECTED | title=%s | pdf=%s | score=%.2f", job.get("title", ""), pdf_url, score)
            self._clear_detail_values(job, "official PDF does not match post title")
            return False
        # Accepted PDF is authoritative for this refresh. Clear any stale
        # values first so an older unrelated notification cannot survive.
        for key in ("vacancy","qualification","salary","age_limit","application_fee","selection_process","exam_date","application_start_date","last_date"):
            job[key]=""
        self._set_if_better(job,'vacancy',self.extract_vacancy(text),'vacancy')
        # IIFCL AGM 2026/06 has an explicit TOTAL of 09 in the official
        # advertisement. Generic OCR can pick a nearby category number (e.g. 7),
        # so use the explicit total only when the official AGM advertisement is
        # clearly identified.
        title_low = self.clean(job.get('title','')).lower()
        pdf_low = str(pdf_url or '').lower()
        if ('iifcl' in title_low and 'agm' in title_low and '2026' in title_low
                and ('englishagmrecruitmentadvertisement' in pdf_low or 'iifcl.in' in pdf_low)
                and re.search(r'(?i)assistant\s+general\s+manager.{0,500}09', text)):
            job['vacancy'] = '9'
            job['vacancy_source'] = 'official IIFCL AGM advertisement total'
        self._set_if_better(job,'qualification',self.extract_qualification(text),'qualification')
        self._set_if_better(job,'salary',self.extract_salary(text),'salary')
        self._set_if_better(job,'age_limit',self.extract_age_limit(text))
        self._set_if_better(job,'application_fee',self.extract_application_fee(text),'application_fee')
        self._set_if_better(job,'selection_process',self.extract_selection_process(text))
        self._set_if_better(job,'exam_date',self.extract_exam_date(text))
        self._set_if_better(job,'application_start_date',self.extract_application_start_date(text))
        self._set_if_better(job,'last_date',self.extract_last_date(text))
        nd=self.extract_notification_date(job.get('title',''),text)
        if nd: job['notification_date']=nd
        job['notification_text']=text
        if pdf_url:
            job['notification_pdf']=pdf_url
        self._apply_known_title_overrides(job)
        return any(self._usable_extracted(job.get(k,''),k) for k in ('vacancy','qualification','salary'))

    def enrich_job(self, job):
        url=str(job.get("url") or "").strip()
        if not url: return job
        post_type = self.detect_post_type(job.get("title", ""), url, job.get("category", ""))
        job["post_type"] = post_type

        # Non-recruitment records must never inherit recruitment vacancy,
        # qualification or salary from a related notification PDF.
        if post_type != "recruitment":
            soup=self.soup(url) if not url.lower().split('#',1)[0].endswith('.pdf') else None
            if soup is not None:
                text=self.page_text(soup)
                job["content"]=text
                job["description"]=text[:700]
                nd=self.extract_notification_date(job.get("title",""),text,soup)
                if nd: job["notification_date"]=nd
                job["apply_link"]=job.get("apply_link") or self.find_apply_link(soup,url)
            # Explicitly clear recruitment-only fields on non-recruitment posts.
            for key in ("vacancy","qualification","salary","age_limit","application_fee","selection_process"):
                job[key]=""
            job["detail_refresh_complete"] = True
            logger.info("DETAIL EXTRACTION SKIPPED | %s | post_type=%s", job.get("title",""), post_type)
            return job
        if url.lower().split('#',1)[0].endswith('.pdf'):
            text=self.extract_pdf_text(url)
            job['notification_pdf']=url
            self._apply_pdf_details(job,url,text)
            job["detail_refresh_complete"] = True
            logger.info('DETAIL EXTRACTION | %s | vacancy=%s | qualification=%s | salary=%s | last_date=%s | notification_pdf=%s',job.get('title',''),job.get('vacancy',''),job.get('qualification',''),job.get('salary',''),job.get('last_date',''),job.get('notification_pdf',''))
            return job

        soup=self.soup(url)
        if soup is None: return job
        text=self.page_text(soup)
        if len(text)>30000: text=text[:30000]
        job['content']=text
        job['description']=text[:700]
        source_score=self._title_match_score(job.get("title",""),text)
        strong_page_match=self._strong_source_match(job.get("title",""),text,0.68)
        if strong_page_match:
            nd=self.extract_notification_date(job.get("title",""),text,soup)
            if nd: job['notification_date']=nd
        else:
            logger.warning("DETAIL PAGE REJECTED | title=%s | score=%.2f",job.get("title",""),source_score)

        # Prefer an exact notification PDF. Once a PDF is found, NEVER extract
        # recruitment table fields from the listing/page HTML; that page often
        # contains navigation, unrelated notices or multiple advertisements.
        pdf=self.find_pdf(soup,url,job.get("title", ""))
        accepted_pdf=False
        if pdf and not str(pdf).lower().startswith(('javascript:','#')):
            ptext=self.extract_pdf_text(pdf)
            if ptext:
                accepted_pdf=self._apply_pdf_details(job,pdf,ptext)
                if not accepted_pdf:
                    logger.warning("UNRELATED PDF IGNORED | title=%s | pdf=%s",job.get("title",""),pdf)

        if not accepted_pdf and strong_page_match:
            # Only use page-level structured data when no exact PDF is available.
            for key, fn in [('vacancy',self.extract_vacancy),('salary',self.extract_salary),('qualification',self.extract_qualification),('last_date',self.extract_last_date),('exam_date',self.extract_exam_date),('application_fee',self.extract_application_fee),('age_limit',self.extract_age_limit),('selection_process',self.extract_selection_process),('application_start_date',self.extract_application_start_date)]:
                value=fn(text)
                field=key if key in ('vacancy','salary','qualification','application_fee') else None
                if self._usable_extracted(value,field):
                    job[key]=self.clean(value)

        # Dates may be present in the listing title even when the PDF uses an
        # image/table layout. Title dates are accepted only for application
        # deadline/start labels, never for salary/qualification/etc.
        title_text=self.clean(job.get("title", ""))
        tm=re.search(r"(?:अंतिम\s*तिथि|last\s*date)\s*[:：-]?\s*(\d{1,2}[./-]\d{1,2}[./-]20\d{2})", title_text, re.I)
        if tm: job["last_date"]=tm.group(1)
        tm=re.search(r"(?:last\s*date)\s*[:：-]?\s*(\d{1,2}\s+[A-Za-z]+\s+20\d{2})", title_text, re.I)
        if tm and not job.get("last_date"): job["last_date"]=tm.group(1)

        # SBI Junior Associates has separate regular and backlog notices. If a
        # generic page supplied the wrong cycle, replace it with the title-matched
        # official PDF before accepting any extracted fields.
        sbi_ja=self.find_sbi_junior_associate_pdf(job.get('title',''))
        if sbi_ja and sbi_ja.split('#',1)[0] != str(job.get('notification_pdf') or '').split('#',1)[0]:
            sbi_text=self.extract_pdf_text(sbi_ja)
            if sbi_text:
                for key in ('vacancy','qualification','salary','age_limit','application_fee','selection_process','exam_date','application_start_date','last_date'):
                    job[key]=''
                self._apply_pdf_details(job,sbi_ja,sbi_text)
                job['notification_pdf']=sbi_ja
                logger.info('SBI JA CYCLE MATCH | %s | pdf=%s | vacancy=%s',job.get('title',''),sbi_ja,job.get('vacancy',''))

        missing_core=not all(self._usable_extracted(job.get(k,''),k) for k in ('vacancy','qualification','salary'))
        if missing_core and not job.get("detail_reset"):
            official_pdf=self.find_external_official_pdf(job.get('title',''))
            current=str(job.get('notification_pdf') or '').split('#',1)[0]
            if official_pdf and official_pdf.split('#',1)[0] != current:
                official_text=self.extract_pdf_text(official_pdf)
                if official_text:
                    job['official_notification_pdf']=official_pdf
                    self._apply_pdf_details(job,official_pdf,official_text)
                    # The actual advertisement should be the notification button.
                    job['notification_pdf']=official_pdf
                    logger.info('OFFICIAL PDF FALLBACK | %s | pdf=%s | vacancy=%s | qualification=%s | salary=%s',job.get('title',''),official_pdf,job.get('vacancy',''),job.get('qualification',''),job.get('salary',''))

        # IBPS periodically issues vacancy corrigenda after the main notice.
        # Use the latest official corrigendum for vacancy only; keep the main
        # notification for qualification/pay/eligibility.
        ibps_update=self.find_latest_ibps_vacancy_update(job.get('title',''))
        if ibps_update:
            update_text=self.extract_pdf_text(ibps_update)
            if update_text:
                updated_vac=self.extract_vacancy(update_text)
                if self._usable_extracted(updated_vac,'vacancy'):
                    job['vacancy']=updated_vac
                    job['vacancy_source']='latest official corrigendum'
                    logger.info('LATEST VACANCY UPDATE | %s | vacancy=%s | pdf=%s',job.get('title',''),updated_vac,ibps_update)

        self._apply_known_title_overrides(job)
        job["detail_refresh_complete"] = True
        job['apply_link']=job.get('apply_link') or self.find_apply_link(soup,url)
        job['official_website']=job.get('official_website') or url
        logger.info('DETAIL EXTRACTION | %s | vacancy=%s | qualification=%s | salary=%s | last_date=%s | notification_pdf=%s',job.get('title',''),job.get('vacancy',''),job.get('qualification',''),job.get('salary',''),job.get('last_date',''),job.get('notification_pdf',''))
        return job

    def enrich_and_filter(self, jobs, require_active=False):
        result = []
        for job in jobs:
            try:
                job = self.enrich_job(job)
            except Exception:
                logger.exception("Job enrichment failed: %s", job.get("title", ""))
            # Do not discard expired source records here. The publisher also
            # reconciles old database posts, and an expired notification may be
            # needed to repair its stored vacancy/qualification/salary/date.
            # Active/expired filtering belongs to the publishing/category layer.
            result.append(job)
        return self.remove_duplicates(result)

    def remove_duplicates(self, jobs):
        seen, out = set(), []
        for job in jobs or []:
            key = (self.clean(job.get("title")).lower(), self.clean(job.get("url")).lower())
            if not key[0] or not key[1] or key in seen:
                continue
            seen.add(key)
            out.append(job)
        return out

    def extract_links(self, soup, base_url, department="Government", category="Latest Jobs"):
        jobs = []
        if soup is None:
            return jobs
        for a in soup.find_all("a", href=True):
            title = self.clean(a.get_text(" ", strip=True))
            href = self.absolute(base_url, a.get("href"))
            if not title or not href or href.startswith(("javascript:", "mailto:")):
                continue
            if self.is_valid_notification(title, href):
                jobs.append(self.build_job(title, href, department, category))
        return self.remove_duplicates(jobs)

    def scrape_page(self, url, department="Government", category="Latest Jobs"):
        return self.enrich_and_filter(self.extract_links(self.soup(url), url, department, category))
