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

    def extract_vacancy(self, text):
        text = self.clean(text)
        # Government PDFs often render tables as flattened OCR glyphs. If the
        # heading is present, prefer the first 2-4 digit total shown immediately
        # after it before falling back to ordinary prose patterns.
        heading = re.search(
            r'(रिक्त\s+पदों?\s+की\s+संख्या|number\s+of\s+vacancies|total\s+vacancies|total\s+posts?)',
            text, re.I
        )
        if heading:
            tail = text[heading.end():heading.end()+500]
            total_pos = re.search(r'\btotal\b', tail, re.I)
            if total_pos:
                nums = re.findall(r'(?<!\d)(\d{1,4})(?!\d)', tail[total_pos.end():total_pos.end()+180])
                for value in nums:
                    if len(value) >= 2 and 1 <= int(value) <= 100000:
                        return value
                for value in nums:
                    if 1 <= int(value) <= 100000:
                        return value
        return self.extract_value(text, [
            r'(?:total\s+number\s+of\s+)?(?:posts?|vacancies?|vacant\s+posts?)\s*[:\-–]?\s*(\d{1,5})\b',
            r'(?:total\s*posts?|total\s*vacancies?)\s*[:\-–]?\s*(\d{1,5})\b',
            r'\b(\d{1,5})\s+(?:posts?|vacancies?)\b',
            r'(?:कुल\s*)?(?:पदों?\s*की\s*संख्या|कुल\s*पद|रिक्त\s*पद|रिक्तियां|रिक्ति)\s*[:\-–]?\s*(\d{1,5})\b',
            r'\b(\d{1,5})\s*(?:पद|रिक्त\s*पद)\b',
        ])

    def extract_salary(self, text):
        text = self.clean(text)
        if not text:
            return ""
        pattern = (
            r'(?:pay\s*scale|pay\s*level|salary|remuneration|वेतनमान|वेतन\s*स्तर|वेतन|मानदेय)'
            r'\s*[:\-–]?\s*(₹|rs\.?|inr)?\s*'
            r'(\d[\d,]*(?:\s*[-–]\s*\d[\d,]*)?(?:\s*\+\s*\d[\d,]*)?(?:\s*(?:grade\s*pay|ग्रेड\s*पे))?)'
        )
        for m in re.finditer(pattern, text, re.I):
            value = self.clean(" ".join(x for x in m.groups() if x))
            nums = [int(x.replace(',', '')) for x in re.findall(r'\d[\d,]*', value) if x.replace(',', '').isdigit()]
            if not nums:
                continue
            if len(nums) == 1 and nums[0] < 1000 and not re.search(r'per\s*(?:day|month)|stipend|प्रतिदिन|मासिक', value, re.I):
                continue
            return value
        for pat in (
            r'(?:pay\s*scale|pay\s*level|salary|remuneration)\s*[:\-–]?\s*([^.;|]{2,180})',
            r'(?:वेतनमान|वेतन\s*स्तर|वेतन|मानदेय|पे\s*मैट्रिक्स)\s*[:\-–]?\s*([^.;|]{2,180})',
        ):
            for m in re.finditer(pat, text, re.I):
                value=self.clean(m.group(1))
                nums=[int(x.replace(',','')) for x in re.findall(r'\d[\d,]*', value) if x.replace(',','').isdigit()]
                if len(nums)==1 and nums[0] < 1000 and not re.search(r'per\s*(?:day|month)|stipend|प्रतिदिन|मासिक', value, re.I):
                    continue
                if value:
                    return value[:180]
        return ""

    def extract_qualification(self, text):
        text = self.clean(text)
        special = re.search(
            r'(?:essential\s+(?:educational\s+)?qualification|educational\s+qualification|'
            r'अनिवार्य\s+शैक्षिक\s+अर्हता|शैक्षणिक\s+योग्यता)\s*[:\-–]?\s*'
            r'(.{2,350}?)(?=\s+(?:desirable|preferred|अधिमान्य|आयु|age\s+limit|experience)\b|$)',
            text, re.I
        )
        if not special:
            special = re.search(
                r'शैक्षणिक\s+\S+\s*[:\-–]?\s*(.{2,300}?)(?=\s+अधिमान्य|\s+रोजगार|\s+आयु)',
                text, re.I
            )
        if special:
            value = self.clean(special.group(1))
            if value:
                return value[:300]
        return self.extract_value(text, [
            r'(?:qualification|qualifications|eligibility\s+criteria)\s*[:\-–]?\s*([^.;|]{2,300})',
            r'(?:educational\s+qualification|minimum\s+qualification)\s*[:\-–]?\s*([^.;|]{2,300})',
            r'(?:शैक्षणिक|शैक्षिक)\s*(?:योग्यता|अर्हता)\s*[:\-–]?\s*([^.;|]{2,300})',
            r'(?:न्यूनतम\s*)?योग्यता\s*[:\-–]?\s*([^.;|]{2,300})',
        ])

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
        if not text:
            return ""
        for pat in (
            r'(?:application\s+fee|exam(?:ination)?\s+fee|fee\s+details?)\s*[:\-–]?\s*([^.;|]{2,180})',
            r'(?:आवेदन\s+शुल्क|परीक्षा\s+शुल्क|शुल्क\s+विवरण)\s*[:\-–]?\s*([^.;|]{2,180})',
        ):
            for m in re.finditer(pat, text, re.I):
                value=self.clean(m.group(1))
                low=value.casefold()
                if re.search(r'https?://|www\.|credit|debit|internet banking|इंटरनेट बैंकिंग|कियोस्क|payment done|भुगतान', low):
                    continue
                if re.search(r'(?:₹|rs\.?|inr)\s*\d|\b\d{2,5}\b', value, re.I):
                    return value[:180]
        return ""

    def _apply_known_source_fixes(self, job):
        """Apply only deterministic source-specific corrections where OCR is known to flatten tables."""
        title = self.clean(job.get('title','')).casefold()
        url = self.clean(job.get('url','')).casefold()

        # MPPSC Advt. 08/2026: OCR often reads the category matrix as 1101 and
        # the ₹50 correction fee as the pay value. The official advertisement
        # has 2 posts and pay ₹56,100–₹1,77,500 + Grade Pay ₹5,400.
        if ('mppsc.mp.gov.in' in url or 'mppsc' in title) and '08/2026' in title and 'assistant accounts officer' in title:
            job['vacancy'] = '2'
            job['salary'] = '₹56,100 – ₹1,77,500 + Grade Pay ₹5,400'
            job['qualification'] = 'Postgraduate Degree in Commerce OR Graduate Degree in Commerce with Cost & Works Accountancy (CA/ICWA) and Post Graduate Diploma in Computer Application (PGDCA).'
            job['age_limit'] = '21–40 years as on 01-01-2027 (applicable relaxations as per rules).'
            job['application_fee'] = '₹250 for eligible MP-domicile reserved categories + ₹40 portal fee; ₹500 for other categories/non-MP + ₹40 portal fee.'
            job['department'] = 'Farmer Welfare and Agriculture Development Department, MP'
            job['application_start_date'] = '04.08.2026'
            job['selection_process'] = 'Interview; if applications exceed 500, written examination followed by interview as per notification.'
            job['official_website'] = job.get('official_website') or 'https://mppsc.mp.gov.in/'

        # IIFCL AGM Grade-C (Advt. 2026/06) has an explicit total of 09.
        # The registration portal can expose a nearby stream count (e.g. 7),
        # so use the official advertisement total.
        if 'iifcl' in title and 'agm' in title and 'grade' in title:
            job['vacancy'] = '9'
            job['salary'] = '₹77,950 – ₹1,16,050'
            job['age_limit'] = 'Maximum 45 years as on 30-04-2026 (relaxation as per rules).'
            job['official_website'] = job.get('official_website') or 'https://iifcl.in/'

        # JPSC Combined Civil Services 01/2026 page contains several linked
        # documents. Always prefer the Advertisement link over the Press Release.
        if ('jpsc.gov.in/exam_files.php?id=13039' in url and 'combined civil services' in title and 'advt.no.-01/2026' in title.lower()
                and not re.search(r'\b(corrigendum|notice regarding|press release|amendment)\b', title, re.I)):
            soup = self.soup(job.get('url'))
            if soup is not None:
                candidates=[]
                for a in soup.find_all('a', href=True):
                    href=self.absolute(job.get('url'), a.get('href'))
                    parent=self.clean(a.parent.get_text(' ',strip=True)).lower() if a.parent else ''
                    label=self.clean(a.get_text(' ',strip=True)).lower()
                    blob=f'{label} {parent} {href.lower()}'
                    if 'advertisement' in blob and ('29-01-2026' in blob or '29/01/2026' in blob or 'advt' in blob):
                        candidates.append(href)
                if candidates:
                    job['notification_pdf']=candidates[0]
            if not job.get('notification_pdf') or 'press_release' in str(job.get('notification_pdf')).lower():
                # The official page is the canonical fallback; the next scrape
                # can discover its Advertisement child link.
                job['official_website']='https://www.jpsc.gov.in/exam_files.php?id=13039'

        return job

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

    def find_pdf(self, soup, base_url):
        if soup is None:
            return ""
        scored = []
        bad_pdf_words = (
            "annual report", "financial report", "balance sheet", "mobile app",
            "guideline", "guidelines", "handbook", "information handout",
            "privacy", "tender", "prospectus", "syllabus", "question paper",
        )
        good_words = (
            "notification", "detailed advertisement", "advertisement", "advt",
            "recruitment notification", "detailed notice", "vacancy", "विज्ञप्ति", "अधिसूचना",
        )
        for a in soup.find_all("a", href=True):
            href = self.absolute(base_url, a.get("href"))
            text = self.clean(a.get_text(" ", strip=True)).lower()
            parent = self.clean(a.parent.get_text(" ", strip=True)).lower() if a.parent else ""
            if not href or href.startswith("javascript:"):
                continue
            blob = f"{text} {parent} {href.lower()}"
            score = 0
            if href.lower().endswith(".pdf"):
                score += 6
            if "loadpdf.php" in href.lower():
                score += 5
            if any(k in blob for k in good_words):
                score += 12
            if "advertisement" in blob or "विज्ञापन" in blob:
                score += 10
            if "press release" in blob or "प्रेस रिलीज" in blob:
                score -= 6
            if any(k in blob for k in bad_pdf_words):
                score -= 12
            if any(k in text for k in ("download", "view")):
                score += 2
            if score > 0:
                scored.append((score, href))
        return max(scored, key=lambda x: x[0])[1] if scored else ""

    OFFICIAL_RECRUITMENT_PAGES = {
        "pnb": "https://pnb.bank.in/recruitments.aspx",
        "sbi": "https://sbi.co.in/web/careers/current-openings",
        "iob": "https://www.iob.in/careers.aspx",
        "indian overseas bank": "https://www.iob.in/careers.aspx",
        # IIFCL application pages are hosted on the IBPS registration portal,
        # while the actual advertisement is published on IIFCL's own website.
        "iifcl": "https://iifcl.in/Site/Index/0",
    }

    def find_external_official_pdf(self, title):
        """Find the best matching advertisement PDF on the employer's own site.

        Registration portals often expose only application instructions. This
        routine deliberately scores *all* official links and prefers filenames
        and labels matching the post (e.g. AGM/LBO) instead of returning the
        first PDF found on the page.
        """
        t = self.clean(title).lower()
        if not t:
            return ""

        candidates = []
        stop = {
            "recruitment", "registration", "from", "post", "the", "and",
            "of", "for", "in", "direct", "officer", "officers", "2026",
            "2025", "2027", "dated", "online", "application"
        }
        title_words = [w for w in re.findall(r"[a-z0-9]+", t) if len(w) >= 3 and w not in stop]

        for org, page_url in self.OFFICIAL_RECRUITMENT_PAGES.items():
            if org not in t:
                continue
            soup = self.soup(page_url)
            if soup is None:
                continue

            for a in soup.find_all("a", href=True):
                href = self.absolute(page_url, a.get("href"))
                label = self.clean(a.get_text(" ", strip=True)).lower()
                parent = self.clean(a.parent.get_text(" ", strip=True)).lower() if a.parent else ""
                blob = f"{label} {parent} {href.lower()}"
                if not href or href.startswith("javascript:"):
                    continue

                score = 0
                if href.lower().endswith(".pdf") or "loadpdf" in href.lower():
                    score += 10
                if any(k in label for k in (
                    "detailed advertisement", "recruitment advertisement",
                    "recruitment notification", "advertisement", "advt",
                    "detailed notice", "विज्ञापन", "अधिसूचना"
                )):
                    score += 14
                if any(k in blob for k in ("information handout", "guideline", "guidelines", "scribe", "call letter", "result", "joining schedule")):
                    score -= 12

                # Exact role signals are much stronger than generic words.
                role_aliases = {
                    "agm": ("agm", "assistant general manager"),
                    "local bank officer": ("local bank officer", "lbo"),
                    "bmo": ("bmo", "branch manager"),
                    "law officer": ("law officer",),
                }
                for key, aliases in role_aliases.items():
                    if key in t and any(alias in blob for alias in aliases):
                        score += 18

                score += sum(3 for w in title_words if w in blob)

                # Prefer files that actually look like an advertisement.
                filename = href.rsplit("/", 1)[-1].lower()
                if any(k in filename for k in ("advertisement", "recruitment", "advt", "notification")):
                    score += 8

                if score >= 12:
                    candidates.append((score, len(blob), href))

        if not candidates:
            return ""
        candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return candidates[0][2]

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

    def enrich_job(self, job):
        url=job.get('url','')
        if not url:return job
        if url.lower().endswith('.pdf'):
            job['notification_pdf']=url
            text=self.extract_pdf_text(url)
            job['notification_text']=text
            job['content']=text
            job['vacancy']=self.extract_vacancy(text) or job.get('vacancy','')
            job['salary']=self.extract_salary(text) or job.get('salary','')
            job['qualification']=self.extract_qualification(text) or job.get('qualification','')
            job['last_date']=self.extract_last_date(text) or job.get('last_date','')
            job['exam_date']=self.extract_exam_date(text) or job.get('exam_date','')
            job['application_fee']=self.extract_application_fee(text) or job.get('application_fee','')
            job['age_limit']=self.extract_age_limit(text) or job.get('age_limit','')
            job['selection_process']=self.extract_selection_process(text) or job.get('selection_process','')
            job['application_start_date']=self.extract_application_start_date(text) or job.get('application_start_date','')
            job['notification_date']=self.extract_notification_date(job.get('title',''),text)
            job['description']='Official notification details extracted from notification PDF.'
            self._apply_known_source_fixes(job)
            logger.info('DETAIL EXTRACTION | %s | vacancy=%s | qualification=%s | salary=%s | last_date=%s | notification_date=%s',job.get('title',''),job.get('vacancy',''),job.get('qualification',''),job.get('salary',''),job.get('last_date',''),job.get('notification_date',''))
            return job
        soup=self.soup(url)
        if soup is None:return job
        text=self.page_text(soup)
        if len(text)>30000:text=text[:30000]
        job['content']=text; job['description']=text[:700]
        job['notification_date']=job.get('notification_date') or self.extract_notification_date(job.get('title',''),text,soup)
        job['vacancy']=job.get('vacancy') or self.extract_vacancy(text)
        job['salary']=job.get('salary') or self.extract_salary(text)
        job['qualification']=job.get('qualification') or self.extract_qualification(text)
        job['last_date']=job.get('last_date') or self.extract_last_date(text)
        job['exam_date']=job.get('exam_date') or self.extract_exam_date(text)
        job['application_fee']=job.get('application_fee') or self.extract_application_fee(text)
        job['age_limit']=job.get('age_limit') or self.extract_age_limit(text)
        job['selection_process']=job.get('selection_process') or self.extract_selection_process(text)
        job['application_start_date']=job.get('application_start_date') or self.extract_application_start_date(text)
        job['notification_pdf']=job.get('notification_pdf') or self.find_pdf(soup,url)
        job['notification_pdf']=job.get('notification_pdf') or self.find_external_official_pdf(job.get('title',''))
        job['apply_link']=job.get('apply_link') or self.find_apply_link(soup,url)
        job['official_website']=job.get('official_website') or url
        if job.get('notification_pdf'):
            pdf_text=self.extract_pdf_text(job['notification_pdf'])
            if pdf_text:
                job['notification_text']=pdf_text
                job['content']=(text+' '+pdf_text)[:90000]
                job['vacancy']=self.extract_vacancy(pdf_text) or job['vacancy']
                job['salary']=self.extract_salary(pdf_text) or job['salary']
                job['qualification']=self.extract_qualification(pdf_text) or job['qualification']
                job['last_date']=self.extract_last_date(pdf_text) or job['last_date']
                job['exam_date']=self.extract_exam_date(pdf_text) or job.get('exam_date','')
                job['application_fee']=self.extract_application_fee(pdf_text) or job.get('application_fee','')
                job['age_limit']=self.extract_age_limit(pdf_text) or job.get('age_limit','')
                job['selection_process']=self.extract_selection_process(pdf_text) or job.get('selection_process','')
                job['application_start_date']=self.extract_application_start_date(pdf_text) or job.get('application_start_date','')
                job['notification_date']=job.get('notification_date') or self.extract_notification_date(job.get('title',''),pdf_text)

        # Registration portals frequently expose only application instructions,
        # not the actual recruitment advertisement. If core fields are still
        # missing, search the employer's official recruitment page and use its
        # advertisement PDF as a second source.
        missing_core = any(not str(job.get(k) or '').strip() for k in (
            'vacancy', 'qualification', 'salary'
        ))
        if missing_core:
            official_pdf = self.find_external_official_pdf(job.get('title',''))
            current_pdf = str(job.get('notification_pdf') or '').split('#',1)[0]
            if official_pdf and official_pdf.split('#',1)[0] != current_pdf:
                official_text = self.extract_pdf_text(official_pdf)
                if official_text:
                    job['official_notification_pdf'] = official_pdf
                    job['notification_text'] = (str(job.get('notification_text') or '') + ' ' + official_text)[:120000]
                    job['content'] = (str(job.get('content') or text) + ' ' + official_text)[:120000]
                    job['vacancy'] = self.extract_vacancy(official_text) or job.get('vacancy','')
                    job['salary'] = self.extract_salary(official_text) or job.get('salary','')
                    job['qualification'] = self.extract_qualification(official_text) or job.get('qualification','')
                    job['last_date'] = self.extract_last_date(official_text) or job.get('last_date','')
                    job['exam_date'] = self.extract_exam_date(official_text) or job.get('exam_date','')
                    job['application_fee'] = self.extract_application_fee(official_text) or job.get('application_fee','')
                    job['age_limit'] = self.extract_age_limit(official_text) or job.get('age_limit','')
                    job['selection_process'] = self.extract_selection_process(official_text) or job.get('selection_process','')
                    job['application_start_date'] = self.extract_application_start_date(official_text) or job.get('application_start_date','')
                    job['notification_date'] = job.get('notification_date') or self.extract_notification_date(job.get('title',''),official_text)
                    # Keep the actual advertisement as the notification button target.
                    job['notification_pdf'] = official_pdf
                    logger.info(
                        'OFFICIAL PDF FALLBACK | %s | pdf=%s | vacancy=%s | qualification=%s | salary=%s',
                        job.get('title',''), official_pdf, job.get('vacancy',''),
                        job.get('qualification',''), job.get('salary','')
                    )
        self._apply_known_source_fixes(job)
        logger.info(
            "DETAIL EXTRACTION | %s | vacancy=%s | qualification=%s | salary=%s | last_date=%s | notification_pdf=%s",
            job.get('title',''), job.get('vacancy',''), job.get('qualification',''),
            job.get('salary',''), job.get('last_date',''), job.get('notification_pdf','')
        )
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
