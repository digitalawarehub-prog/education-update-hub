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
    old_title=base.BaseAdapter.sanitize_title
    old_table=base.BaseAdapter.sanitize_table_text
    def new_title(self,text): return sanitize_title(old_title(self,text))
    def new_table(self,text,field=""): return sanitize_value(old_table(self,text,field))
    base.BaseAdapter.sanitize_title=new_title
    base.BaseAdapter.sanitize_table_text=new_table
    try: base.BaseAdapter.MAX_PDF_PAGES=min(int(getattr(base.BaseAdapter,"MAX_PDF_PAGES",12)),8)
    except Exception: pass
    old_candidates=base.BaseAdapter._pdf_candidates
    def candidates(self,soup,base_url): return old_candidates(self,soup,base_url)[:4]
    base.BaseAdapter._pdf_candidates=candidates

    # Exact notification/card PDF first. This fixes the main SBI/career-page
    # problem where the listing page was read but its inner notification PDF was
    # not tied to the correct recruitment.
    old_enrich=base.BaseAdapter.enrich_job
    def targeted(self,job):
        if not job.get("url") or job.get("notification_pdf") or not is_recruitment(job): return
        try:
            soup=self.soup(job["url"])
            if soup is None: return
            title=_clean(job.get("title","")).casefold()
            stop={"recruitment","notification","advertisement","online","application","apply","post","vacancy","vacancies","the","and","for","with","हेतु","क्लिक","करें"}
            tokens=[x for x in re.findall(r"[a-z0-9]{3,}|[\u0900-\u097F]{3,}",title) if x not in stop]
            scored=[]; seen=set()
            for a in soup.find_all("a",href=True):
                href=self.absolute(job["url"],a.get("href")); key=href.split("#",1)[0]
                if not href or href.startswith(("javascript:","mailto:","tel:")) or key in seen: continue
                seen.add(key)
                label=_clean(a.get_text(" ",strip=True)).casefold(); parent=_clean(a.parent.get_text(" ",strip=True)).casefold() if a.parent else ""
                blob=f"{label} {parent} {key.casefold()}"; score=sum(6 for t in tokens[:8] if t in blob)
                if any(k in blob for k in ("detailed advertisement","recruitment advertisement","advertisement pdf","notification pdf","download advertisement","detailed notification")): score+=28
                if key.lower().endswith(".pdf") or "loadpdf" in key.lower() or "open_pdf" in key.lower(): score+=20
                if any(k in blob for k in ("download","document","notification","advertisement","recruitment")): score+=8
                if any(k in blob for k in ("result","answer key","admit card","hall ticket","call letter","syllabus","selection list","information handout")): score-=25
                if score>=12: scored.append((score,href))
            for _,href in sorted(scored,reverse=True)[:3]:
                pdf=self.resolve_document_pdf(href,max_depth=1) or (href if href.lower().endswith(".pdf") else "")
                if not pdf: continue
                text=self.extract_pdf_text(pdf)
                if not text: continue
                if self.pdf_identity_score(job,pdf,text)>=0.45:
                    job["notification_pdf"]=pdf; job["official_notification_pdf"]=pdf; job["notification_pdf_source"]=job.get("notification_pdf_source") or "targeted_card"; job["notification_text"]=text
                    return
        except Exception: return
    def enrich(self,job):
        targeted(self,job)
        out=old_enrich(self,job)
        out["title"]=sanitize_title(out.get("title","") )
        for k in ("description","summary","qualification","salary","selection_process","age_limit","application_fee","exam_date","application_start_date","last_date"):
            if out.get(k): out[k]=sanitize_value(out[k])
        return out
    base.BaseAdapter.enrich_job=enrich

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
    old=monitor.sanitize_legacy_content
    def sanitize(jobs):
        jobs=old(jobs)
        from adapters.base import BaseAdapter
        a=BaseAdapter()
        for j in jobs:
            if j.get("title"): j["title"]=sanitize_title(j["title"])
            for k in ("description","summary","vacancy","qualification","salary","selection_process","age_limit","application_fee","exam_date","application_start_date","last_date"):
                if j.get(k): j[k]=a._table_clean_value(j[k],k)
        return jobs
    monitor.sanitize_legacy_content=sanitize

def apply(monitor):
    global _APPLIED
    if _APPLIED: return
    _APPLIED=True
    import adapters.base as base
    import html_generator, homepage, category_generator
    patch_base(base); patch_html(html_generator); patch_homepage(homepage); patch_category(category_generator); patch_monitor(monitor)
