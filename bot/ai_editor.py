"""Education Update Hub AI editor using OpenRouter Free."""
from __future__ import annotations
import hashlib, json, os, re
from pathlib import Path
from openai import OpenAI

MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")
CACHE = Path(os.getenv("AI_POST_CACHE", "ai_post_cache.json"))
CATEGORIES = ["recruitment","admit_card","result","answer_key","syllabus","entrance_exam","interview","notice"]
SCHEMA={"type":"object","additionalProperties":False,"properties":{
"post_type":{"type":"string","enum":CATEGORIES},"title":{"type":"string"},"seo_title":{"type":"string"},"summary_hi":{"type":"string"},
"department":{"type":"string"},"organization":{"type":"string"},"post_name":{"type":"string"},"vacancy":{"type":"string"},"qualification":{"type":"string"},"salary":{"type":"string"},"age_limit":{"type":"string"},"application_start":{"type":"string"},"last_date":{"type":"string"},"fee":{"type":"string"},"exam_date":{"type":"string"},
"apply_url":{"type":"string"},"admit_card_url":{"type":"string"},"result_url":{"type":"string"},"answer_key_url":{"type":"string"},"syllabus_url":{"type":"string"},"notification_url":{"type":"string"},"official_url":{"type":"string"},
"faq":{"type":"array","items":{"type":"object","additionalProperties":False,"properties":{"question":{"type":"string"},"answer":{"type":"string"}},"required":["question","answer"]}},
"missing_critical":{"type":"array","items":{"type":"string"}},"confidence":{"type":"string","enum":["high","medium","low"]}},
"required":["post_type","title","seo_title","summary_hi","department","organization","post_name","vacancy","qualification","salary","age_limit","application_start","last_date","fee","exam_date","apply_url","admit_card_url","result_url","answer_key_url","syllabus_url","notification_url","official_url","faq","missing_critical","confidence"]}
RULES='''You are the senior Hindi editor for Education Update Hub.\nUse ONLY the supplied source record. Never invent facts, dates, numbers, organisations or URLs.\nA URL may only be copied exactly from a supplied URL field; never construct a URL.\nMissing facts must be empty; never use Government, Not Mentioned, Check Notification as factual values.\nCreate an attractive, SEO-friendly, clickable Hindi title without false urgency or clickbait.\nClassify from the actual source: recruitment=new hiring/application; admit_card=hall ticket; result=result/scorecard/merit; answer_key=answer key/objection; syllabus=syllabus/exam pattern; entrance_exam=entrance/admission exam; interview=walk-in/interview; notice=other official update.\nA walk-in interview MUST NOT become recruitment. Recruitment apply_url must be a supplied application URL only. Notification PDF must never become Apply Online. Admit-card/result/answer-key/syllabus links must remain in their own fields.\n'''

def _clean(v): return re.sub(r"\s+"," ",str(v or "")).strip()
def _url(v):
    v=_clean(v); return v if v.startswith(("http://","https://")) else ""
def _source(job):
    keys=("title","description","summary","content","text","raw_text","body","url","apply_link","application_link","notification_pdf","notification_link","download_link","official_website","admit_card_url","result_url","answer_key_url","syllabus_url","entrance_exam_link","interview_link","department","organization","category","post_type","vacancy","qualification","salary","age_limit","application_start","last_date","fee","exam_date")
    return json.dumps({k:job[k] for k in keys if job.get(k) not in (None,"")},ensure_ascii=False)[:60000]
def _load():
    try:return json.loads(CACHE.read_text(encoding="utf-8"))
    except Exception:return {}
def _save(x): CACHE.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding="utf-8")

def enrich(job):
    key_api=os.getenv("OPENROUTER_API_KEY")
    if not key_api: raise RuntimeError("OPENROUTER_API_KEY is not configured")
    client=OpenAI(api_key=key_api,base_url="https://openrouter.ai/api/v1",default_headers={"HTTP-Referer":"https://educationupdatehub.in","X-Title":"Education Update Hub"})
    raw=_source(job); key=hashlib.sha256(raw.encode()).hexdigest(); cache=_load()
    if key in cache: ai=cache[key]
    else:
        resp=client.chat.completions.create(model=MODEL,messages=[{"role":"system","content":RULES},{"role":"user","content":"SOURCE RECORD:\n"+raw}],temperature=0.2,response_format={"type":"json_schema","json_schema":{"name":"euh_editorial_record","strict":True,"schema":SCHEMA}})
        ai=json.loads(resp.choices[0].message.content or "{}"); cache[key]=ai; _save(cache)
    allowed={_url(job.get(k)) for k in ("url","apply_link","application_link","notification_pdf","notification_link","download_link","official_website","admit_card_url","result_url","answer_key_url","syllabus_url","entrance_exam_link","interview_link")}; allowed.discard("")
    for k in ("apply_url","admit_card_url","result_url","answer_key_url","syllabus_url","notification_url","official_url"):
        if _url(ai.get(k)) not in allowed: ai[k]=""
    return ai
