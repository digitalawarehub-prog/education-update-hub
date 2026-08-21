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

    def extract_vacancy(self, text):
        """Extract total vacancies from explicit total rows before generic matches."""
        text = self.clean(text)
        if not text:
            return ""
        # IBPS annexures are flattened tables. For PO/SPL/CSA, a total row may
        # appear once per bank/post. Prefer an explicit grand/overall total;
        # otherwise sum the distinct per-row totals in the annexure.
        low=text.lower()
        ann=low.find("annexure i")
        if ann >= 0 and "vacanc" in low[ann:ann+1200]:
            region=text[ann:ann+30000]
            overall=[]
            for m in re.finditer(r"(?:grand\s+total|overall\s+total)\b", region, re.I):
                tail=region[m.end():m.end()+180]
                nums=[int(x) for x in re.findall(r"(?<![\d/.-])(\d{1,6})(?![\d/.-])",tail)]
                nums=[n for n in nums if 1 <= n <= 100000 and n not in range(1900,2101)]
                if nums: overall.append(max(nums))
            if overall: return str(max(overall))
            totals=[]
            for m in re.finditer(r"\btotal\b", region, re.I):
                tail=region[m.end():m.end()+90]
                nums=[int(x) for x in re.findall(r"(?<![\d/.-])(\d{1,6})(?![\d/.-])",tail)]
                nums=[n for n in nums if 1 <= n <= 5000 and n not in range(1900,2101)]
                if nums: totals.append(max(nums))
            if totals:
                # Remove duplicates created by repeated headers; if there is a
                # very large total it is almost certainly the overall total.
                uniq=[]
                for n in totals:
                    if n not in uniq: uniq.append(n)
                if max(uniq) >= 500 and sum(x for x in uniq if x != max(uniq)) >= max(uniq):
                    return str(sum(x for x in uniq if x != max(uniq)))
                if max(uniq) >= 500 and len(uniq) > 1:
                    return str(max(uniq))
                if len(uniq) > 1:
                    return str(sum(uniq))
                return str(uniq[0])
        # Prefer explicit Grand Total/Total rows. Flattened PDF tables often
        # look like: Grand Total 24 12 9 2 5 52, where the last number is TOTAL.
        for label in (r"grand\s+total", r"total\s+vacancies?", r"total\s+posts?", r"total\s+number\s+of\s+vacancies?"):
            for m in re.finditer(label, text, re.I):
                tail=text[m.end():m.end()+220]
                nums=[int(x) for x in re.findall(r"(?<![\d/.-])(\d{1,6})(?![\d/.-])", tail)]
                nums=[n for n in nums if 1 <= n <= 100000 and n not in range(1900,2101)]
                if nums:
                    return str(max(nums))
        # Heading/table-local fallback.
        for m in re.finditer(r"(?:number\s+of\s+vacancies|no\.\s*of\s*vacancies|vacancies|रिक्त\s*पद|पदों?\s*की\s*संख्या)", text, re.I):
            tail=text[m.end():m.end()+700]
            nums=[int(x) for x in re.findall(r"(?<![\d/.-])(\d{1,6})(?![\d/.-])", tail)]
            nums=[n for n in nums if 1 <= n <= 100000 and n not in range(1900,2101)]
            if nums:
                return str(max(nums))
        for pat in (
            r"\b(\d{1,6})\s+(?:posts?|vacancies?|vacant\s+posts?)\b",
            r"\b(\d{1,6})\s*(?:पद|रिक्त\s*पद)\b",
        ):
            m=re.search(pat,text,re.I)
            if m:return m.group(1)
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

    def extract_qualification(self, text):
        text=self.clean(text)
        if not text:return ""
        heading_patterns=(
            r"\bessential\s+educational\s+qualification\b",
            r"\bessential\s+qualification\b",
            r"\beducational\s+qualifications?\b",
            r"\bminimum\s+educational\s+qualification\b",
            r"\beducational\s+qualification\b",
        )
        degree_rx=r"(?:\bBachelor\b|\bMaster\b|\bGraduate\b|\bGraduation\b|\bPost\s+Graduate\b|\bDiploma\b|\bDegree\b|\bB\.?\s*Tech\b|\bM\.?\s*Tech\b|\bLLB\b|\bMBA\b|\bBCA\b|\bMCA\b|\bPh\.?D\b|\bIntermediate\b|स्नातक|स्नातकोत्तर|डिग्री|डिप्लोमा|बी\.टेक|एम\.टेक)"
        for hp in heading_patterns:
            for m in re.finditer(hp,text,re.I):
                tail=text[m.end():m.end()+1200]
                q=re.search(r"("+degree_rx+r".{0,360})",tail,re.I)
                if not q: continue
                value=self.clean(q.group(1))
                value=re.split(r"\b(?:desirable|preferred|work\s+experience|experience|age|pay|salary|selection|application\s+fee|important\s+dates|reservation)\b",value,1,flags=re.I)[0]
                value=re.sub(r"^(?:\*\*?\s*)?(?:from\s+a\s+university[^)]*\)\s*)?","",value,flags=re.I).strip()
                if len(value)>=5 and not value.casefold().startswith(('cation fees','cation charges','application fees')):
                    return value[:360]
        for pat in (
            r"\b(?:qualification|qualifications)\s*[:\-–]\s*([^.;|]{3,300})",
            r"\b(?:शैक्षणिक|शैक्षिक)\s*(?:योग्यता|अर्हता)\s*[:\-–]\s*([^.;|]{3,300})",
        ):
            m=re.search(pat,text,re.I)
            if m:return self.clean(m.group(1))[:360]
        return ""

    def extract_salary(self, text):
        text=self.clean(text)
        if not text:return ""
        patterns=(
            r"\b(?:scale\s+of\s+pay|basic\s+pay\s+scale)\s*[:\-–]?\s*([^.;|]{2,260})",
            r"\b(?:pay\s*scale|pay\s*level|pay\s*matrix|salary|remuneration|emoluments?)\s*[:\-–]?\s*([^.;|]{2,260})",
            r"(?:वेतनमान|वेतन\s*स्तर|वेतन|मानदेय)\s*[:\-–]?\s*([^.;|]{2,220})",
        )
        for pat in patterns:
            for m in re.finditer(pat,text,re.I):
                value=self.clean(m.group(1))
                if any(x in value.casefold() for x in ('stipulated dates','before registering online','slips, etc','click here')): continue
                if re.search(r"(?:₹|rs\.?|inr|level\s*[-–]?\s*\d|\d[\d,]*\s*[-–]\s*\d[\d,]*)",value,re.I):
                    return value[:260]
        m=re.search(r"((?:₹|Rs\.?|INR)\s*[0-9][0-9,]*(?:\s*(?:lacs?|lakhs?|crore|per\s+annum|CTC))?)",text,re.I)
        return self.clean(m.group(1)) if m else ""

    def extract_last_date(self, text):
        """Prefer the application-closing date over 'last date for printing'."""
        text = self.clean(text)
        if not text:
            return ""
        labels = [
            r'closure\s+of\s+(?:online\s+)?registration\s+of\s+application',
            r'last\s+date\s+(?:to|for)\s+apply',
            r'last\s+date\s+of\s+(?:online\s+)?application',
            r'application\s+(?:last\s+date|deadline)',
            r'closing\s+date',
            r'apply\s+online\s+upto',
            r'अंतिम\s+तिथि', r'अंतिम\s+तारीख', r'आवेदन\s+की\s+अंतिम\s+तिथि',
        ]
        for label in labels:
            for dp in self.DATE_PATTERNS:
                m = re.search(label + r'[^.;|]{0,180}?' + dp, text, re.I)
                if m:
                    return self.clean(m.group(1))
        for label in labels:
            m = re.search(label + r'\s*(?:\||:|-|–)?\s*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})', text, re.I)
            if m:
                return self.clean(m.group(1))
        return ""

    def extract_notification_date(self, title, text='', soup=None):
        combined=' '.join([str(title or ''),str(text or '')])
        patterns=[
            r'(?:dated|date\s*of\s*advertisement|advertisement\s*dated|notification\s*dated)\s*[:\-–]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(?:दिनांक|दिनांकित|विज्ञापन\s*दिनांक|अधिसूचना\s*दिनांक)\s*[:\-–]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b',
        ]
        # Only explicitly labelled advertisement/notification dates count as
        # publication dates. Do not treat dates embedded in titles such as
        # "Registration From 19-Aug-2026" as the notification date.
        for pat in patterns[:2]:
            m=re.search(pat,combined,re.I)
            if m:return self.clean(m.group(1))
        if soup is not None:
            for tag in soup.find_all('time'):
                value=tag.get('datetime') or tag.get_text(' ',strip=True)
                if value and re.search(r'\d{4}',value):return self.clean(value[:30])
            for meta in soup.find_all('meta'):
                key=' '.join([str(meta.get('name','')),str(meta.get('property',''))]).lower()
                value=meta.get('content','')
                if any(k in key for k in ('datepublished','article:published_time','publishdate')) and value:return self.clean(value)
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
        if not pdf_url:
            return ""
        try:
            r = self.session.get(
                pdf_url, timeout=(10, 45), allow_redirects=True, verify=False,
                headers={"Accept": "application/pdf,*/*;q=0.8"}
            )
            r.raise_for_status()
            content = r.content
            if not content or content[:4] != b"%PDF":
                logger.warning("PDF response is not PDF: %s", pdf_url)
                return ""

            candidates = []
            if fitz is not None:
                try:
                    doc = fitz.open(stream=content, filetype="pdf")
                    text = self.clean(" ".join(page.get_text("text") or "" for page in list(doc)[:40]))
                    if text:
                        candidates.append(("PyMuPDF", text))
                except Exception as exc:
                    logger.warning("PyMuPDF failed | %s | %s", pdf_url, exc)

            if pdfplumber is not None:
                try:
                    chunks = []
                    with pdfplumber.open(io.BytesIO(content)) as pdf:
                        for page in pdf.pages[:40]:
                            chunks.append(page.extract_text() or "")
                    text = self.clean(" ".join(chunks))
                    if text:
                        candidates.append(("pdfplumber", text))
                except Exception as exc:
                    logger.warning("pdfplumber failed | %s | %s", pdf_url, exc)

            if PdfReader is not None:
                try:
                    reader = PdfReader(io.BytesIO(content))
                    text = self.clean(" ".join(page.extract_text() or "" for page in reader.pages[:40]))
                    if text:
                        candidates.append(("pypdf", text))
                except Exception as exc:
                    logger.warning("pypdf failed | %s | %s", pdf_url, exc)

            if candidates:
                candidates.sort(key=lambda x: self._pdf_text_quality(x[1]), reverse=True)
                engine, best = candidates[0]
                quality = self._pdf_text_quality(best)
                tokens = best.split()
                short_ratio = (
                    sum(1 for token in tokens if len(re.sub(r"[^A-Za-z0-9\u0900-\u097F]", "", token)) <= 1)
                    / max(len(tokens), 1)
                )
                # Broken-font Hindi PDFs often look "long" to text extractors but
                # contain a very high number of one-character/glyph fragments.
                needs_ocr = short_ratio > 0.25 or (len(best) > 500 and "\u0900" not in best and "Assistant District" in best and short_ratio > 0.18)
                if quality >= 0.72 and len(best) >= 120 and not needs_ocr:
                    logger.info("PDF extracted %s | %s | %d chars", engine, pdf_url, len(best))
                    return best[:90000]
                ocr = self._ocr_pdf_pages(content, max_pages=8)
                if len(ocr) >= 200:
                    combined = (ocr + " " + best).strip()
                    logger.info("PDF OCR fallback | %s | %d chars | quality=%.2f", pdf_url, len(combined), quality)
                    return combined[:90000]
                logger.info("PDF extracted %s | %s | %d chars | quality=%.2f", engine, pdf_url, len(best), quality)
                return best[:90000]

            ocr = self._ocr_pdf_pages(content, max_pages=8)
            if ocr:
                logger.info("PDF OCR only | %s | %d chars", pdf_url, len(ocr))
                return ocr
        except Exception as exc:
            logger.warning("PDF download failed | %s | %s", pdf_url, exc)
        return ""

    def extract_age_limit(self, text):
        text = self.clean(text)
        return self.extract_value(text, [
            r'(?:age\s*limit|age\s*criteria|upper\s+age\s+limit|maximum\s+age)\s*[:\-–]?\s*([^.;|]{2,180})',
            r'(?:आयु\s*सीमा|उम्र\s*सीमा|अधिकतम\s*आयु)\s*[:\-–]?\s*([^.;|]{2,180})',
        ])

    def extract_selection_process(self, text):
        text = self.clean(text)
        return self.extract_value(text, [
            r'(?:selection\s+process|selection\s+procedure|mode\s+of\s+selection)\s*[:\-–]?\s*([^.;|]{2,220})',
            r'(?:चयन\s*प्रक्रिया|चयन\s*पद्धति)\s*[:\-–]?\s*([^.;|]{2,220})',
        ])

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
                m = re.search(label + r'[^.;|]{0,120}?' + dp, text, re.I)
                if m:
                    return self.clean(m.group(1))
        return ""

    def extract_exam_date(self, text):
        text = self.clean(text)
        for label in (r'exam(?:ination)?\s+date', r'date\s+of\s+exam', r'परीक्षा\s+तिथि', r'परीक्षा\s+दिनांक'):
            for dp in self.DATE_PATTERNS:
                m = re.search(label + r'[^.;|]{0,120}?' + dp, text, re.I)
                if m:
                    return self.clean(m.group(1))
        return ""

    def extract_application_fee(self, text):
        text = self.clean(text)
        return self.extract_value(text, [
            r'(?:application\s+fee|exam(?:ination)?\s+fee|fee\s+details?)\s*[:\-–]?\s*([^.;|]{2,180})',
            r'(?:आवेदन\s+शुल्क|परीक्षा\s+शुल्क)\s*[:\-–]?\s*([^.;|]{2,180})',
        ])

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

    def find_pdf(self, soup, base_url):
        if soup is None:
            return ""
        scored=[]
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
            if any(k in blob for k in ('information handout','call letter','result','joining schedule','scorecard','guidelines')): score-=25
            if any(k in text for k in ('download','view','click here')): score+=2
            if score>=8: scored.append((score,len(blob),href))
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

    def find_external_official_pdf(self, title):
        t=self.clean(title).lower()
        if not t: return ""
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
        return {
            "title": self.clean(title), "url": url, "department": department,
            "category": category, "vacancy": "", "qualification": "", "salary": "",
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
        if field=='vacancy' and not re.search(r"\b\d{1,6}\b",v): return False
        if field=='salary' and len(v)<2: return False
        if field=='qualification' and len(v)<3: return False
        return True

    def _set_if_better(self, job, key, value, field=None):
        if self._usable_extracted(value, field):
            job[key]=self.clean(value)

    def _apply_pdf_details(self, job, pdf_url, text):
        if not text: return False
        self._set_if_better(job,'vacancy',self.extract_vacancy(text),'vacancy')
        self._set_if_better(job,'qualification',self.extract_qualification(text),'qualification')
        self._set_if_better(job,'salary',self.extract_salary(text),'salary')
        self._set_if_better(job,'age_limit',self.extract_age_limit(text))
        self._set_if_better(job,'application_fee',self.extract_application_fee(text))
        self._set_if_better(job,'selection_process',self.extract_selection_process(text))
        self._set_if_better(job,'exam_date',self.extract_exam_date(text))
        self._set_if_better(job,'application_start_date',self.extract_application_start_date(text))
        self._set_if_better(job,'last_date',self.extract_last_date(text))
        nd=self.extract_notification_date(job.get('title',''),text)
        if nd: job['notification_date']=nd
        job['notification_text']=text
        if pdf_url:
            job['notification_pdf']=pdf_url
        return any(self._usable_extracted(job.get(k,''),k) for k in ('vacancy','qualification','salary'))

    def enrich_job(self, job):
        url=str(job.get('url') or '').strip()
        if not url: return job
        if url.lower().split('#',1)[0].endswith('.pdf'):
            text=self.extract_pdf_text(url)
            job['notification_pdf']=url
            self._apply_pdf_details(job,url,text)
            logger.info('DETAIL EXTRACTION | %s | vacancy=%s | qualification=%s | salary=%s | last_date=%s | notification_pdf=%s',job.get('title',''),job.get('vacancy',''),job.get('qualification',''),job.get('salary',''),job.get('last_date',''),job.get('notification_pdf',''))
            return job

        soup=self.soup(url)
        if soup is None: return job
        text=self.page_text(soup)
        if len(text)>30000: text=text[:30000]
        job['content']=text
        job['description']=text[:700]
        nd=self.extract_notification_date(job.get('title',''),text,soup)
        if nd: job['notification_date']=nd
        # Page-level fields are only used if they look like real values.
        for key, fn in [('vacancy',self.extract_vacancy),('salary',self.extract_salary),('qualification',self.extract_qualification),('last_date',self.extract_last_date),('exam_date',self.extract_exam_date),('application_fee',self.extract_application_fee),('age_limit',self.extract_age_limit),('selection_process',self.extract_selection_process),('application_start_date',self.extract_application_start_date)]:
            value=fn(text)
            field=key if key in ('vacancy','salary','qualification') else None
            if self._usable_extracted(value,field) and not self._usable_extracted(job.get(key,''),field): job[key]=self.clean(value)

        pdf=self.find_pdf(soup,url)
        if pdf and not str(pdf).lower().startswith(('javascript:','#')):
            ptext=self.extract_pdf_text(pdf)
            if ptext:
                self._apply_pdf_details(job,pdf,ptext)

        missing_core=not all(self._usable_extracted(job.get(k,''),k) for k in ('vacancy','qualification','salary'))
        if missing_core:
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
