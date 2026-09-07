"""AI editorial layer for Education Update Hub.
Uses only facts/URLs already present in the scraped record.
"""
from __future__ import annotations
import hashlib, json, os, re
from pathlib import Path
from openai import OpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
CACHE = Path(os.getenv("AI_POST_CACHE", "ai_post_cache.json"))

CATEGORIES = ["recruitment", "admit_card", "result", "answer_key", "syllabus", "entrance_exam", "interview", "notice"]

SCHEMA = {
 "type":"object", "additionalProperties":False,
 "properties": {
  "post_type":{"type":"string","enum":CATEGORIES},
  "title":{"type":"string"}, "seo_title":{"type":"string"}, "summary_hi":{"type":"string"},
  "department":{"type":"string"}, "organization":{"type":"string"}, "post_name":{"type":"string"},
  "vacancy":{"type":"string"}, "qualification":{"type":"string"}, "salary":{"type":"string"},
  "age_limit":{"type":"string"}, "application_start":{"type":"string"}, "last_date":{"type":"string"},
  "fee":{"type":"string"}, "exam_date":{"type":"string"},
  "apply_url":{"type":"string"}, "admit_card_url":{"type":"string"}, "result_url":{"type":"string"},
  "answer_key_url":{"type":"string"}, "syllabus_url":{"type":"string"}, "notification_url":{"type":"string"},
  "official_url":{"type":"string"},
  "faq":{"type":"array","items":{"type":"object","additionalProperties":False,"properties":{"question":{"type":"string"},"answer":{"type":"string"}},"required":["question","answer"]}},
  "missing_critical":{"type":"array","items":{"type":"string"}},
  "confidence":{"type":"string","enum":["high","medium","low"]}
 },
 "required":["post_type","title","seo_title","summary_hi","department","organization","post_name","vacancy","qualification","salary","age_limit","application_start","last_date","fee","exam_date","apply_url","admit_card_url","result_url","answer_key_url","syllabus_url","notification_url","official_url","faq","missing_critical","confidence"]
}

RULES = """
You are the editorial AI for Education Update Hub.
Use ONLY the supplied source record. Never invent facts, dates, numbers, organisations or URLs.
A URL may only be copied from a supplied URL field; never construct a new URL.
If a fact is missing, return an empty string. Do not use placeholders such as Government, Not Mentioned, Check Notification as factual values.
Visible dates should be DD-MM-YYYY when a full date is known.
Create an attractive but accurate Hindi title; no fake urgency or clickbait.
Classify the page from the actual title/text:
- recruitment = a new hiring/application advertisement
- admit_card = hall ticket/admit card download
- result = result/scorecard/merit list
- answer_key = answer key/objection
- syllabus = syllabus/exam pattern
- entrance_exam = entrance/admission exam
- interview = walk-in interview/interview schedule/interview selection update
- notice = other official update/notice
A walk-in interview MUST NOT be classified as recruitment merely because it contains the word apply.
For recruitment, apply_url must be the supplied application URL only; never use notification_url as apply_url.
For admit_card, result, answer_key and syllabus, keep their URLs in their own fields and do not copy notification_url into them unless that exact URL is also explicitly supplied as the corresponding action URL.
"""

def _clean(v): return re.sub(r"\s+", " ", str(v or "")).strip()
def _url(v):
    v=_clean(v); return v if v.startswith(("http://","https://")) else ""
def _source(job):
    keys=("title","description","summary","content","text","raw_text","body","url","apply_link","notification_pdf","download_link","official_website","admit_card_url","result_url","answer_key_url","syllabus_url","department","organization","category")
    return json.dumps({k:job[k] for k in keys if job.get(k) not in (None,"")},ensure_ascii=False)[:60000]

def _cache_load():
    try:return json.loads(CACHE.read_text(encoding="utf-8"))
    except Exception:return {}
def _cache_save(c):
    CACHE.write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding="utf-8")

def enrich(job):
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not available to the Python process")
    client=OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    raw=_source(job); key=hashlib.sha256(raw.encode()).hexdigest()
    cache=_cache_load()
    if key in cache: ai=cache[key]
    else:
        resp=client.responses.create(
            model=MODEL,
            instructions=RULES,
            input="SOURCE RECORD:\n"+raw,
            text={"format":{"type":"json_schema","name":"euh_editorial_record","strict":True,"schema":SCHEMA}}
        )
        ai=json.loads(resp.output_text)
        cache[key]=ai; _cache_save(cache)
    # Hard URL allow-list: AI can never create or mutate a URL.
    allowed={_url(job.get(k)) for k in ("url","apply_link","notification_pdf","download_link","official_website","admit_card_url","result_url","answer_key_url","syllabus_url")}
    allowed.discard("")
    for k in ("apply_url","admit_card_url","result_url","answer_key_url","syllabus_url","notification_url","official_url"):
        if _url(ai.get(k)) not in allowed: ai[k]=""
    return ai
