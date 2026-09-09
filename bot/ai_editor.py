import os,re,json,logging,time
from typing import Any,Dict
import requests

log=logging.getLogger("EUH-AI")
API="https://openrouter.ai/api/v1/chat/completions"
MODEL=os.getenv("OPENROUTER_MODEL","openrouter/free")
MAX_AI_POSTS_PER_RUN=int(os.getenv("MAX_AI_POSTS_PER_RUN","5"))

CATS={
"recruitment":["recruitment","vacancy","vacancies","job","jobs","hiring","apply online"],
"result":["result","results","merit list","score card"],
"admit_card":["admit card","hall ticket","call letter"],
"answer_key":["answer key","answer keys","objection"],
"syllabus":["syllabus","exam pattern","scheme and syllabus"],
"entrance_exam":["entrance exam","entrance test","admission test","registration"],
"scholarship":["scholarship","fellowship","stipend"],
"interview":["interview","walk in interview","walk-in interview","interview schedule"],
"exam_schedule":["exam schedule","time table","timetable","examination schedule"],
"notice":["notice","notification","public notice","circular","corrigendum"]
}

def clean(v):
    s="" if v is None else str(v)
    if "%PDF-" in s: s=s[:s.find("%PDF-")]
    s=re.sub(r"<script\b.*?</script>|<style\b.*?</style>"," ",s,flags=re.I|re.S)
    s=re.sub(r"<[^>]+>"," ",s)
    s=re.sub(r"\b(endobj|endstream|xref|trailer)\b"," ",s,flags=re.I)
    return re.sub(r"\s+"," ",s).strip()[:10000]

def classify_category(j):
    explicit=clean(j.get("category") or j.get("type")).lower()
    aliases={"results":"result","admit card":"admit_card","answer key":"answer_key",
             "entrance exam":"entrance_exam","interview":"interview","recruitment":"recruitment"}
    if explicit in CATS:return explicit
    if explicit in aliases:return aliases[explicit]
    text=" ".join(clean(j.get(k)) for k in ("title","description","summary","content","text","raw_text","body")).lower()
    for cat in ("result","admit_card","answer_key","syllabus","scholarship","entrance_exam",
                "interview","exam_schedule","notice","recruitment"):
        if any(x in text for x in CATS[cat]): return cat
    return "notice"

def source(j):
    return "\n".join(f"{k}: {clean(j.get(k))}" for k in
      ("title","description","summary","content","text","raw_text","body","department","organization",
       "post_name","vacancies","total_vacancies","qualification","eligibility","salary","pay_scale",
       "age_limit","application_start","last_date","exam_date","result_date","interview_date",
       "application_fee","selection_process","apply_url","notification_url","official_url","url")
      if clean(j.get(k)))[:16000]

def fallback(j,cat):
    def f(*ks):
        for k in ks:
            if j.get(k): return clean(j[k])
        return ""
    return {"category":cat,"title":clean(j.get("title")) or "Government Update",
    "seo_title":clean(j.get("title"))[:65],"meta_description":clean(j.get("description") or j.get("summary"))[:155],
    "department":f("department"),"organization":f("organization"),"post_name":f("post_name","post"),
    "total_posts":f("total_vacancies","vacancies","total_posts"),"qualification":f("qualification","eligibility"),
    "salary":f("salary","pay_scale"),"age_limit":f("age_limit"),"application_start":f("application_start"),
    "last_date":f("last_date","deadline"),"exam_date":f("exam_date"),"result_date":f("result_date"),
    "interview_date":f("interview_date"),"fee":f("application_fee","fee"),
    "selection_process":f("selection_process","selection"),"description":clean(j.get("description") or j.get("summary")),
    "apply_url":f("apply_url","apply_link"),"notification_url":f("notification_url","notification_pdf"),
    "official_url":f("official_url","official_website"),"result_url":f("result_url"),
    "admit_card_url":f("admit_card_url"),"answer_key_url":f("answer_key_url"),
    "syllabus_url":f("syllabus_url"),"content_html":"","faqs":[]}

def enrich(j):
    cat=classify_category(j)
    key=os.getenv("OPENROUTER_API_KEY")
    if not key:return fallback(j,cat)
    prompt=f"""You are the senior editor of Education Update Hub. Return ONLY valid JSON.
Correct category is likely: {cat}.
Never convert Result, Admit Card, Syllabus, Answer Key, Entrance Exam, Interview or Exam Schedule into Recruitment.
Extract ONLY facts present in SOURCE. Missing values must be empty strings. Never invent.
Never output PDF binary text such as %PDF, endobj, stream, xref.
Do not invent URLs. Use only URLs in SOURCE.
Create an attractive natural clickable SEO title.
content_html is short clean HTML only, no buttons and no h1.
JSON keys:
category,title,seo_title,meta_description,department,organization,post_name,total_posts,qualification,salary,age_limit,application_start,last_date,exam_date,result_date,interview_date,fee,selection_process,description,apply_url,notification_url,official_url,result_url,admit_card_url,answer_key_url,syllabus_url,content_html,faqs
SOURCE:
{source(j)}"""
    r=requests.post(API,headers={"Authorization":f"Bearer {key}","Content-Type":"application/json",
       "HTTP-Referer":"https://educationupdatehub.in","X-Title":"Education Update Hub"},
       json={"model":MODEL,"messages":[{"role":"user","content":prompt}],"temperature":0.1,"max_tokens":2200},timeout=45)
    if r.status_code==429:
        raise RuntimeError("OPENROUTER_RATE_LIMIT")
    r.raise_for_status()
    txt=r.json()["choices"][0]["message"]["content"].strip()
    txt=re.sub(r"^```(?:json)?\s*|\s*```$","",txt,flags=re.I)
    obj=json.loads(txt)
    base=fallback(j,cat); base.update({k:v for k,v in obj.items() if k in base and v is not None})
    # Category is controlled by local classifier when AI tries to make it generic.
    ai_cat=str(obj.get("category") or "").lower()
    base["category"]=ai_cat if ai_cat in CATS and ai_cat!="recruitment" or cat=="recruitment" else cat
    return base
