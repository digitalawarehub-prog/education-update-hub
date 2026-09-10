"""Source-grounded AI editor."""
import json, logging, os, re, requests
from bs4 import BeautifulSoup
log=logging.getLogger("EUH_AI")
API_URL="https://openrouter.ai/api/v1/chat/completions"
MODEL=os.getenv("OPENROUTER_MODEL","openrouter/free")
API_KEY=os.getenv("OPENROUTER_API_KEY","").strip()
BAD={"","not mentioned","not available","check notification","check official notification","as per rules","उपलब्ध नहीं","आधिकारिक अधिसूचना देखें"}
TYPES={"recruitment":"Recruitment","admit-card":"Admit Card","result":"Result","answer-key":"Answer Key","syllabus":"Syllabus","scholarship":"Scholarship","entrance":"Entrance Exam","interview":"Interview","notice":"Notice","scheme":"Government Scheme"}

def clean(v): return str(v or "").strip()
def real(v): return clean(v).casefold() not in BAD
def source_text(job):
    u=clean(job.get("url"))
    if not u or u.lower().endswith(".pdf"): return clean(job.get("description"))[:14000]
    try:
        r=requests.get(u,timeout=30,headers={"User-Agent":"Mozilla/5.0 Education Update Hub"})
        r.raise_for_status()
        s=BeautifulSoup(r.text,"html.parser")
        for x in s(["script","style","noscript","svg"]): x.decompose()
        return re.sub(r"\s+"," ",s.get_text(" ",strip=True))[:14000]
    except Exception:
        return clean(job.get("description"))[:14000]

def parse_json(text):
    try:return json.loads(text)
    except Exception:
        m=re.search(r"\{.*\}",text,re.S)
        if m:
            try:return json.loads(m.group(0))
            except Exception:pass
    return {}

def enrich(job):
    if not API_KEY: raise RuntimeError("OPENROUTER_API_KEY_MISSING")
    prompt=f"""You are the factual editor for Education Update Hub. Use ONLY the source text. Never invent facts or URLs.
Classify correctly: recruitment, admit-card, result, answer-key, syllabus, scholarship, entrance, interview, notice, scheme.
A notice/exam-date/advt notice is NOT recruitment unless it invites applications for posts. Walk-in interview is interview.
Return empty string when a field is absent. Department must be actual organization or empty. Dates DD-MM-YYYY.
Never turn notification_pdf into apply_link and never create URLs.
Existing title: {clean(job.get('title'))}
Existing url: {clean(job.get('url'))}
Existing category: {clean(job.get('category'))}
Source text:
{source_text(job)}
Return ONLY JSON:
{{"title":"","summary":"","category":"","post_type":"","department":"","vacancy":"","qualification":"","salary":"","age_limit":"","application_fee":"","selection_process":"","exam_date":"","application_start_date":"","last_date":"","notification_date":""}}"""
    r=requests.post(API_URL,headers={"Authorization":f"Bearer {API_KEY}","Content-Type":"application/json","HTTP-Referer":"https://educationupdatehub.in","X-Title":"Education Update Hub"},json={"model":MODEL,"messages":[{"role":"system","content":"Return only valid JSON and remain source-grounded."},{"role":"user","content":prompt}],"temperature":0.1,"max_tokens":1400},timeout=40)
    if r.status_code==429: raise RuntimeError("OPENROUTER_RATE_LIMIT")
    r.raise_for_status()
    data=r.json()
    ai=parse_json(data["choices"][0]["message"]["content"])
    if not ai: raise RuntimeError("AI_INVALID_JSON")
    out=dict(job)
    for k in ("title","summary","category","post_type","department","vacancy","qualification","salary","age_limit","application_fee","selection_process","exam_date","application_start_date","last_date","notification_date"):
        v=clean(ai.get(k))
        if v: out[k]=v
    for k in ("vacancy","qualification","salary","age_limit","application_fee","selection_process","exam_date","application_start_date","last_date","notification_date"):
        if not real(out.get(k)): out[k]=""
    p=clean(out.get("post_type")).casefold()
    if p in TYPES: out["category"]=TYPES[p]
    out["url"]=clean(job.get("url"))
    out["apply_link"]=clean(job.get("apply_link"))
    out["notification_pdf"]=clean(job.get("notification_pdf"))
    out["official_website"]=clean(job.get("official_website")) or out["url"]
    return out
