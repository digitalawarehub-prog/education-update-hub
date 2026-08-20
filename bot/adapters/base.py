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
        r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
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
        return self.extract_value(text, [
            r'(?:total\s+)?(?:number\s+of\s+)?(?:posts?|vacancies?|vacant\s+posts?)\s*[:\-–]?\s*(\d{1,5})\b',
            r'(?:total\s*posts?|total\s*vacancies?)\s*[:\-–]?\s*(\d{1,5})\b',
            r'\b(\d{1,5})\s+(?:posts?|vacancies?)\b',
            r'(?:कुल\s*)?(?:पदों?\s*की\s*संख्या|कुल\s*पद|रिक्त\s*पद|रिक्तियां|रिक्ति)\s*[:\-–]?\s*(\d{1,5})\b',
            r'\b(\d{1,5})\s*(?:पद|रिक्त\s*पद)\b',
        ])

    def extract_salary(self, text):
        text = self.clean(text)
        return self.extract_value(text, [
            r'(?:pay\s*scale|pay\s*level|salary|remuneration|pay\s+matrix|level)\s*[:\-–]?\s*([^.;|]{2,180})',
            r'(?:वेतनमान|वेतन\s*स्तर|वेतन|मानदेय|पे\s*मैट्रिक्स)\s*[:\-–]?\s*([^.;|]{2,180})',
        ])

    def extract_qualification(self, text):
        text = self.clean(text)
        return self.extract_value(text, [
            r'(?:educational\s+)?qualification(?:s)?\s*[:\-–]?\s*([^.;|]{2,300})',
            r'(?:essential\s+)?eligibility\s*(?:criteria)?\s*[:\-–]?\s*([^.;|]{2,300})',
            r'(?:educational\s+qualification|minimum\s+qualification)\s*[:\-–]?\s*([^.;|]{2,300})',
            r'(?:शैक्षणिक|शैक्षिक)\s*(?:योग्यता|अर्हता)\s*[:\-–]?\s*([^.;|]{2,300})',
            r'(?:न्यूनतम\s*)?योग्यता\s*[:\-–]?\s*([^.;|]{2,300})',
        ])

    def extract_last_date(self, text):
        text = self.clean(text)
        labels = (
            r'last\s+date', r'closing\s+date', r'last\s+date\s+for\s+(?:submission|receipt)',
            r'application\s+(?:last\s+date|deadline)', r'closing\s+time', r'apply\s+online\s+upto',
            r'अंतिम\s+तिथि', r'अंतिम\s+तारीख', r'आवेदन\s+की\s+अंतिम\s+तिथि'
        )
        label_re='(?:'+'|'.join(labels)+')'
        for pat in self.DATE_PATTERNS:
            m=re.search(label_re+r'[^.;]{0,160}?'+pat,text,re.I)
            if m:return self.clean(m.group(1))
        return ''

    def extract_notification_date(self, title, text='', soup=None):
        combined=' '.join([str(title or ''),str(text or '')])
        patterns=[
            r'(?:dated|date\s*of\s*advertisement|advertisement\s*dated|notification\s*dated)\s*[:\-–]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(?:दिनांक|दिनांकित|विज्ञापन\s*दिनांक|अधिसूचना\s*दिनांक)\s*[:\-–]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b',
        ]
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
                if any(k in key for k in ('datepublished','article:published_time','publishdate')) and value:return self.clean(value)
        return ''

    def extract_pdf_text(self, pdf_url):
        if not pdf_url:return ''
        try:
            r=self.session.get(pdf_url,timeout=(8,30),allow_redirects=True,verify=False)
            r.raise_for_status(); content=r.content
            if not content or content[:4]!=b'%PDF':
                logger.warning('PDF response is not PDF: %s',pdf_url); return ''
            if fitz is not None:
                try:
                    doc=fitz.open(stream=content,filetype='pdf'); text=self.clean(' '.join(page.get_text('text') or '' for page in doc[:40]))
                    if len(text)>=80:
                        logger.info('PDF extracted PyMuPDF | %s | %d chars',pdf_url,len(text)); return text[:90000]
                except Exception as exc: logger.warning('PyMuPDF failed | %s | %s',pdf_url,exc)
            if pdfplumber is not None:
                try:
                    chunks=[]
                    with pdfplumber.open(io.BytesIO(content)) as pdf:
                        for page in pdf.pages[:40]: chunks.append(page.extract_text() or '')
                    text=self.clean(' '.join(chunks))
                    if len(text)>=80:
                        logger.info('PDF extracted pdfplumber | %s | %d chars',pdf_url,len(text)); return text[:90000]
                except Exception as exc: logger.warning('pdfplumber failed | %s | %s',pdf_url,exc)
            if PdfReader is not None:
                try:
                    reader=PdfReader(io.BytesIO(content)); text=self.clean(' '.join(page.extract_text() or '' for page in reader.pages[:40]))
                    if text:
                        logger.info('PDF extracted pypdf | %s | %d chars',pdf_url,len(text)); return text[:90000]
                except Exception as exc: logger.warning('pypdf failed | %s | %s',pdf_url,exc)
        except Exception as exc:
            logger.warning('PDF download failed | %s | %s',pdf_url,exc)
        return ''

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
            "%d-%m-%Y", "%d/%m/%Y", "%d-%m-%y", "%d/%m/%y",
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
        for a in soup.find_all("a", href=True):
            href = self.absolute(base_url, a.get("href"))
            text = self.clean(a.get_text(" ", strip=True)).lower()
            if not href or href.startswith("javascript:"):
                continue
            score = 0
            if href.lower().endswith(".pdf"): score += 5
            if any(k in text for k in ("notification", "advertisement", "advt", "download", "विज्ञप्ति", "अधिसूचना")): score += 4
            if score: scored.append((score, href))
        return max(scored, key=lambda x: x[0])[1] if scored else ""

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
            "last_date": "", "notification_pdf": "", "apply_link": "", "official_website": url,
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
            job['notification_date']=self.extract_notification_date(job.get('title',''),text)
            job['description']='Official notification details extracted from notification PDF.'
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
        job['notification_pdf']=job.get('notification_pdf') or self.find_pdf(soup,url)
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
                job['notification_date']=job.get('notification_date') or self.extract_notification_date(job.get('title',''),pdf_text)
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
