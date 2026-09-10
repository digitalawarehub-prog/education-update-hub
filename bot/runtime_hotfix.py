"""Education Update Hub V17 runtime hotfix.

This module patches the existing production bot at runtime so the complete
repository does not need to be replaced.  It is intentionally conservative:
PDF data is accepted only after notification identity is checked.
"""
from __future__ import annotations
import os
import re
from datetime import datetime

_APPLIED = False

def _clean(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()

def sanitize_title(text):
    v = _clean(text)
    if not v: return ""
    # Handles both spaced and joined forms: "... पाठ्यक्रमहेतु क्लिक करें".
    patterns = [
        r"\s*(?:के\s+लिए\s*)?हेतु\s*(?:क्लिक|click)\s*(?:करें|कर|here|to)?(?:\s+(?:करें|view|apply|download|open))?\s*$",
        r"\s*(?:के\s+लिए\s*)?क्लिक\s*करें\s*$",
        r"\s*click\s*here(?:\s+to\s+(?:apply|view|download|read|open))?\s*$",
    ]
    for p in patterns: v = re.sub(p, "", v, flags=re.I)
    v = re.sub(r"(पाठ्यक्रम|आवेदन|ऑनलाइन|विज्ञापन|अधिसूचना|सूचना|परिणाम|प्रवेश\s*पत्र)हेतु$", r"\1", v, flags=re.I)
    v = re.sub(r"^(?:\s*(?:\d+|[a-z]|[ivx]+|\([a-z]\)|\([ivx]+\))[.)\-:]?\s*)+", "", v, flags=re.I)
    return _clean(v).strip(" -–—|:")

def sanitize_value(text):
    v = _clean(text)
    if not v: return ""
    v = re.sub(r"(?:हेतु\s*क्लिक\s*करें|के\s+लिए\s*क्लिक\s*करें|क्लिक\s*करें|click\s*here(?:\s+to\s+(?:view|download|apply|read|open))?)", "", v, flags=re.I)
    v = re.sub(r"(?:skip\s+to\s+main\s+content|skip\s+to\s+content)", "", v, flags=re.I)
    v = re.sub(r"https?://\S+|www\.\S+", "", v, flags=re.I)
    v = re.sub(r"^(?:(?:\(?[a-z]\)?|\(?[क-ह]\)?|\(?[ivx]+\)?|\d+)[.)\-:]?\s*)+", "", v, flags=re.I)
    v = re.sub(r"^o\s*:-\s*", "", v, flags=re.I)
    v = re.sub(r"\s+page\s+\d+(?:\s+of\s+\d+)?\b.*$", "", v, flags=re.I)
    v = re.split(r"\b(?:official\s+website|visit\s+website|for\s+details|click\s+here|download\s+here)\b", v, maxsplit=1, flags=re.I)[0]
    v = re.split(r"(?:आधिकारिक\s+वेबसाइट|वेबसाइट\s+पर|के\s+लिए\s+जानकारी|हेतु\s*क्लिक)", v, maxsplit=1, flags=re.I)[0]
    return _clean(v)[:1200]

def is_recruitment(job):
    p=_clean(job.get("post_type","")).casefold(); c=_clean(job.get("category","")).casefold(); t=_clean(job.get("title","")).casefold()
    if p in {"result","admit card","answer key","syllabus","scholarship","other"}: return False
    if any(x in t for x in ("admit card","hall ticket","answer key","result","syllabus","scholarship","पाठ्यक्रम","प्रवेश पत्र","परिणाम","उत्तर कुंजी")): return False
    return p in {"recruitment","job","jobs",""} or c in {"recruitment","latest jobs","latest job","job","jobs"}

def active_recruitment(job):
    if not is_recruitment(job): return False
    s=_clean(job.get("last_date","")).replace("/","-").replace(".","-")
    for fmt in ("%d-%m-%Y","%d-%m-%y","%Y-%m-%d","%d %B %Y","%d %b %Y"):
        try: return datetime.strptime(s,fmt).date() >= datetime.now().date()
        except Exception: pass
    return False

def language(job):
    text=" ".join(_clean(job.get(k,"")) for k in ("notification_text","notification_content","content","description","summary","title","qualification","salary"))
    hi=len(re.findall(r"[\u0900-\u097F]",text)); en=len(re.findall(r"[A-Za-z]",text))
    return "hi" if hi>=20 and hi>en*0.35 else "en"

def patch_base(base):
    """Apply only patches supported by the installed BaseAdapter.
    Older/newer bot builds may not expose every helper, so hotfix must never
    crash the publisher during startup.
    """
    cls = getattr(base, "BaseAdapter", None)
    if cls is None:
        return

    # Title sanitization: install a fallback even when the base class does
    # not provide the helper that older hotfix versions expected.
    old_title = getattr(cls, "sanitize_title", None)
    if callable(old_title):
        def new_title(self, text):
            try:
                text = old_title(self, text)
            except Exception:
                pass
            return sanitize_title(text)
    else:
        def new_title(self, text):
            return sanitize_title(text)
    cls.sanitize_title = new_title

    # Table-value sanitization is optional in some repository revisions.
    old_table = getattr(cls, "sanitize_table_text", None)
    if callable(old_table):
        def new_table(self, text, field=""):
            try:
                text = old_table(self, text, field)
            except TypeError:
                try:
                    text = old_table(self, text)
                except Exception:
                    pass
            except Exception:
                pass
            return sanitize_value(text)
    else:
        def new_table(self, text, field=""):
            return sanitize_value(text)
    cls.sanitize_table_text = new_table

    try:
        cls.MAX_PDF_PAGES = min(int(getattr(cls, "MAX_PDF_PAGES", 12)), 8)
    except Exception:
        pass

    old_candidates = getattr(cls, "_pdf_candidates", None)
    if callable(old_candidates):
        def candidates(self, soup, base_url):
            try:
                result = old_candidates(self, soup, base_url)
                return list(result or [])[:4]
            except Exception:
                return []
        cls._pdf_candidates = candidates

    # enrich_job is optional. Only wrap it when the installed adapter has it.
    old_enrich = getattr(cls, "enrich_job", None)
    if callable(old_enrich):
        def enrich(self, job):
            try:
                if job.get("url") and not job.get("notification_pdf") and is_recruitment(job):
                    soup = self.soup(job["url"])
                    if soup is not None:
                        title = _clean(job.get("title","")).casefold()
                        for a in soup.find_all("a", href=True):
                            href = str(a.get("href",""))
                            label = _clean(a.get_text(" ", strip=True)).casefold()
                            if ".pdf" in href.casefold() and (not title or any(x in label for x in title.split() if len(x)>3)):
                                job["notification_pdf"] = href
                                break
            except Exception:
                pass
            try:
                return old_enrich(self, job)
            except Exception:
                return None
        cls.enrich_job = enrich
def patch_html(h):
    h.detect_content_language=lambda job: language(job)
    h.localize_value=lambda value,job,default: (_clean(value) if _clean(value) and _clean(value).casefold() not in {"not mentioned","not available","n/a","na","none","null"} else default)
    h.localized_title=lambda job: sanitize_title(job.get("title","")) or ("Government Job Update" if language(job)=="en" else "सरकारी नौकरी अपडेट")
    h.localized_summary=lambda job: sanitize_value(job.get("description") or job.get("summary") or job.get("content") or "")[:900] or h.localized_title(job)
    old_body=getattr(h,"build_html_body",None)
    if old_body:
        def body(job):
            out=old_body(job)
            iso=""
            try: iso=h._published_date_iso(job)
            except Exception: pass
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}",str(iso)):
                d=datetime.strptime(iso,"%Y-%m-%d").strftime("%d-%m-%Y")
                out=re.sub(r"(Published\s*:\s*)\d{4}-\d{2}-\d{2}",rf"\g<1>{d}",out,flags=re.I)
                out=re.sub(r"(प्रकाशित\s*:\s*)\d{4}-\d{2}-\d{2}",rf"\g<1>{d}",out,flags=re.I)
            return out
        h.build_html_body=body

def patch_homepage(homepage):
    def register(job):
        # Latest Updates can contain all live update types; location JOB boxes
        # are strictly recruitment-only.
        homepage.add_to_section("AUTO_LATEST_GRID",homepage.build_latest_post(job))
        homepage.add_to_section("AUTO_LATEST_POSTS",homepage.build_latest_post(job))
        homepage.add_to_section("AUTO_MARQUEE",homepage.build_marquee_item(job))
        homepage.add_to_section("AUTO_BREAKING",homepage.build_breaking_item(job))
        if not active_recruitment(job): return
        item=homepage.build_job_item(job)
        text=" ".join(_clean(job.get(k,"")) for k in ("title","department","organization","source","url")).lower()
        cat=_clean(job.get("category","")).lower()
        if any(x in text or x in cat for x in ("uttarakhand","उत्तराखंड","ukpsc","uksssc","uttarakhand police","uttarakhand forest")):
            homepage.add_to_section("AUTO_UK_JOBS",item)
        elif any(x in text or x in cat for x in ("central","upsc","ssc","ibps","sbi","rbi","bank","railway","defence","government of india")):
            homepage.add_to_section("AUTO_CENTRAL_JOBS",item)
        else:
            homepage.add_to_section("AUTO_STATE_JOBS",item)
    homepage.register_job=register

def patch_category(cg):
    old=cg.group_jobs
    if getattr(old,"_euh_v17",False): return
    def group(jobs):
        g=old(jobs)
        for k in list(g):
            low=str(k).casefold()
            if low.endswith("-jobs") or low in {"latest-jobs","central-jobs","central-government-jobs","uttarakhand-jobs","other-state-jobs"}:
                g[k]=[j for j in g[k] if active_recruitment(j)]
        return g
    group._euh_v17=True; cg.group_jobs=group

def patch_monitor(monitor):
    os.environ.setdefault("EUH_DETAIL_QUEUE_CAP","16")
    os.environ.setdefault("EUH_DETAIL_WORKERS","4")
    os.environ.setdefault("EUH_DETAIL_MAX_PAGES","2")
    os.environ.setdefault("EUH_DETAIL_MAX_DEPTH","1")
    os.environ.setdefault("EUH_DETAIL_TIME_BUDGET","14")
    os.environ.setdefault("EUH_MAX_PDF_PAGES","8")
    os.environ.setdefault("EUH_OCR_MAX_PAGES","2")
    os.environ.setdefault("EUH_LEGACY_REPAIR_CAP","8")
    os.environ.setdefault("EUH_ENABLE_OCR","true")
    # Some repository versions do not have legacy sanitizer hooks at all.
    # Never let an optional compatibility patch abort the whole publisher.
    old=getattr(monitor, "sanitize_legacy_content", None)
    if old is None:
        return
    def sanitize(jobs):
        jobs=old(jobs)
        try:
            from adapters.base import BaseAdapter
            a=BaseAdapter()
            cleaner=getattr(a, "_table_clean_value", None)
        except Exception:
            cleaner=None
        for j in jobs or []:
            if j.get("title"): j["title"]=sanitize_title(j["title"])
            for k in ("description","summary","vacancy","qualification","salary","selection_process","age_limit","application_fee","exam_date","application_start_date","last_date"):
                if j.get(k):
                    try:
                        j[k]=cleaner(j[k],k) if callable(cleaner) else sanitize_value(j[k])
                    except Exception:
                        j[k]=sanitize_value(j[k])
        return jobs
    monitor.sanitize_legacy_content=sanitize

def apply(monitor):
    global _APPLIED
    if _APPLIED: return
    _APPLIED=True
    import adapters.base as base
    import html_generator, homepage, category_generator
    patch_base(base); patch_html(html_generator); patch_homepage(homepage); patch_category(category_generator); patch_monitor(monitor)