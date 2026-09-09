import json, os, re, time, logging
from typing import Dict, Any
import requests

logger = logging.getLogger("EUH-AI")
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")
MAX_AI_POSTS_PER_RUN = int(os.getenv("MAX_AI_POSTS_PER_RUN", "5"))

CATEGORIES = {
    "recruitment": ["recruitment","vacancy","vacancies","job","jobs","hiring","apply online","application"],
    "result": ["result","results","merit list","selection list","marks","qualified candidates"],
    "admit_card": ["admit card","hall ticket","call letter","download letter"],
    "answer_key": ["answer key","answer keys","objection to answer","question paper key"],
    "syllabus": ["syllabus","exam pattern","scheme and syllabus"],
    "entrance_exam": ["entrance exam","entrance test","registration","admission test","cet","neet","cuet"],
    "scholarship": ["scholarship","fellowship","stipend"],
    "interview": ["walk in interview","walk-in interview","interview result","interview schedule","interview"],
    "exam_schedule": ["exam schedule","time table","timetable","exam date","stage-ii","mains examination"],
    "notice": ["notice","notification","public notice","circular","order","corrigendum","reschedule"],
}

def clean_text(value):
    if value is None: return ""
    s=str(value)
    if "%PDF-" in s: s=s[:s.find("%PDF-")]
    s=re.sub(r"<script\b[^>]*>.*?</script>"," ",s,flags=re.I|re.S)
    s=re.sub(r"<style\b[^>]*>.*?</style>"," ",s,flags=re.I|re.S)
    s=re.sub(r"<[^>]+>"," ",s)
    s=re.sub(r"\b(endobj|endstream|xref|trailer|obj)\b"," ",s,flags=re.I)
    return re.sub(r"\s+"," ",s).strip()[:12000]

def classify_category(job: Dict[str,Any]):
    explicit=str(job.get("category") or job.get("type") or "").strip().lower()
    mapping={"result":"result","results":"result","admit card":"admit_card","answer key":"answer_key","syllabus":"syllabus","scholarship":"scholarship","entrance exams":"entrance_exam","entrance exam":"entrance_exam","teaching exams":"exam_schedule","interview":"interview","recruitment":"recruitment","latest jobs":"recruitment"}
    if explicit in mapping: return mapping[explicit]
    text=" ".join(clean_text(job.get(k)) for k in ("title","description","summary","content","text","raw_text","body")).lower()
    for cat in ["result","admit_card","answer_key","syllabus","scholarship","entrance_exam","interview","exam_schedule","notice","recruitment"]:
        if any(k in text for k in CATEGORIES[cat]): return cat
    return "notice"

def field(job,*names):
    for n in names:
        if job.get(n) not in (None,""): return job.get(n)
    return ""

def source(job):
    keys=("title","description","summary","content","text","raw_text","body","department","vacancy","vacancies","total_vacancies","total_posts","qualification","eligibility","salary","pay_scale","last_date","deadline","exam_date","application_start","apply_link","apply_url","notification_pdf","notification_url","official_website","url")
    return "\n".join(f"{k}: {clean_text(job.get(k))}" for k in keys if clean_text(job.get(k)))[:18000]

def fallback(job,cat):
    src=field(job,"url","source_url","link")
    return {"category":cat,"title":clean_text(job.get("title")) or "Government Update","seo_title":clean_text(job.get("title"))[:68],"meta_description":f"{clean_text(job.get('title'))} की महत्वपूर्ण जानकारी, तिथियां और आधिकारिक लिंक यहां देखें।"[:155],"department":clean_text(job.get("department")),"organization":clean_text(job.get("organization")),"post_name":clean_text(field(job,"post_name","post")),"total_posts":clean_text(field(job,"total_vacancies","vacancies","vacancy","total_posts")),"qualification":clean_text(field(job,"qualification","educational_qualification","eligibility")),"salary":clean_text(field(job,"salary","pay_scale","pay","remuneration")),"age_limit":clean_text(field(job,"age_limit","age")),"application_start":clean_text(field(job,"application_start","start_date")),"last_date":clean_text(field(job,"last_date","deadline","closing_date")),"exam_date":clean_text(field(job,"exam_date","examination_date")),"result_date":clean_text(field(job,"result_date")),"interview_date":clean_text(field(job,"interview_date")),"fee":clean_text(field(job,"application_fee","fee")),"selection_process":clean_text(field(job,"selection_process","selection")),"description":clean_text(job.get("description") or job.get("summary"))[:1600],"apply_url":str(field(job,"apply_link","apply_url","application_url") or ""),"notification_url":str(field(job,"notification_pdf","notification_url","pdf_url") or ""),"official_url":str(field(job,"official_website","official_url") or src or ""),"source_url":str(src or ""),"content_html":"","faqs":[]}

def enrich(job):
    cat=classify_category(job); key=os.getenv("OPENROUTER_API_KEY")
    if not key: return fallback(job,cat)
    system='''You are the senior editor for Education Update Hub. Return ONLY valid JSON. Correctly classify the item. Result, admit-card, answer-key, syllabus, interview and exam-schedule must NEVER become recruitment just because the source contains the word recruitment. Extract ONLY facts supported by source. Missing facts must be empty strings, never guessed and never "Government" or "Check Official Notification". Remove PDF binary garbage. Preserve official URLs from source; never fabricate URLs. Create a natural clickable SEO title. content_html is clean short HTML without h1 and without buttons. Use category-specific fields.'''
    schema={"category":"recruitment|result|admit_card|answer_key|syllabus|entrance_exam|scholarship|interview|exam_schedule|notice","title":"string","seo_title":"string","meta_description":"string","department":"string","organization":"string","post_name":"string","total_posts":"string","qualification":"string","salary":"string","age_limit":"string","application_start":"string","last_date":"string","exam_date":"string","result_date":"string","interview_date":"string","fee":"string","selection_process":"string","description":"string","apply_url":"string","notification_url":"string","official_url":"string","source_url":"string","content_html":"string","faqs":"array"}
    payload={"model":MODEL,"messages":[{"role":"system","content":system},{"role":"user","content":f"Expected category: {cat}\nSOURCE:\n{source(job)}\nSCHEMA:\n{json.dumps(schema,ensure_ascii=False)}"}],"temperature":0.15,"max_tokens":2200}
    try:
        r=requests.post(API_URL,headers={"Authorization":f"Bearer {key}","Content-Type":"application/json","HTTP-Referer":"https://educationupdatehub.in","X-Title":"Education Update Hub"},json=payload,timeout=45)
        if r.status_code==429: raise RuntimeError("OPENROUTER_RATE_LIMIT")
        r.raise_for_status(); c=r.json()["choices"][0]["message"]["content"]
        c=re.sub(r"^```json\s*|\s*```$","",c.strip(),flags=re.I); obj=json.loads(c)
        base=fallback(job,cat)
        for k,v in obj.items():
            if k in base and v is not None: base[k]=v
        base["category"]=classify_category({"title":base.get("title"),"category":base.get("category")})
        for k in ("department","total_posts","qualification","salary","age_limit","application_start","last_date","exam_date","result_date","interview_date","fee","selection_process"):
            if str(base.get(k,"" )).strip().lower() in {"government","check official notification","not mentioned","not available"}: base[k]=""
        return base
    except RuntimeError: raise
    except Exception as e:
        logger.error("AI failed for %s: %s",job.get("title",""),e); return fallback(job,cat)

def enrich_batch(jobs,limit=MAX_AI_POSTS_PER_RUN):
    out=[]
    for job in jobs[:max(0,limit)]:
        try: out.append(enrich(job)); time.sleep(.25)
        except RuntimeError as e:
            if str(e)=="OPENROUTER_RATE_LIMIT": break
            raise
    return out
