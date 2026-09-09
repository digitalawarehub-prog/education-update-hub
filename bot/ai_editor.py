"""OpenRouter Free editorial layer for Education Update Hub."""
from __future__ import annotations
import json, os, re, urllib.request, urllib.error, hashlib

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")

SYSTEM = r"""
You are the senior editor of Education Update Hub, a Hindi government-exam/jobs information portal.
Return ONLY valid JSON. Never invent facts, dates, vacancy counts, fees, salaries, qualifications or URLs.
Use only the supplied source record. If a fact is absent, return an empty string.
Classify the item by its ACTUAL purpose, not merely words in the title:
- recruitment: a fresh hiring/application opportunity
- admit_card: admit card/hall ticket/call letter/download notice
- result: result, merit list, scorecard, selection list, marks
- answer_key: answer key/response sheet/objection
- syllabus: syllabus/exam pattern/curriculum
- entrance_exam: entrance/admission test, not recruitment
- interview: walk-in/interview notice, keep separate from normal recruitment
- notice: general official notice/update that is not one of the above
A notification PDF is NOT automatically an application URL. A source URL is not an apply URL unless it is explicitly an application page/link.
Do not use generic values like Government, Govt, As per rules, Not mentioned, Official Notification देखें.
Create an attractive, factual Hindi title suitable for Google Discover/search. Do not use fake urgency.
Keep official names accurate. Prefer Hindi explanation with official English names where useful.
"""

FIELDS = ["post_type","title","seo_title","summary_hi","department","organization","post_name","vacancy","qualification","salary","age_limit","application_start","last_date","fee","exam_date","apply_url","admit_card_url","result_url","answer_key_url","syllabus_url","notification_url","official_url","confidence"]

def _json_from_text(text):
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```$", "", text)
    try: return json.loads(text)
    except Exception: pass
    m=re.search(r"\{.*\}", text, re.S)
    if not m: raise ValueError("OpenRouter did not return JSON")
    return json.loads(m.group(0))

def _source_urls(job):
    vals=[]
    for k,v in job.items():
        if isinstance(v,str) and v.startswith(("http://","https://")):
            vals.append(v.strip())
    return sorted(set(vals))

def enrich(job):
    key=os.getenv("OPENROUTER_API_KEY")
    if not key: raise RuntimeError("OPENROUTER_API_KEY is not configured")
    source=dict(job)
    # Do not send huge HTML/noisy blobs; keep all useful scalar fields.
    clean={k:v for k,v in source.items() if isinstance(v,(str,int,float,bool)) and v not in ("",None)}
    prompt=(SYSTEM+"\nSOURCE RECORD:\n"+json.dumps(clean,ensure_ascii=False,indent=2) +
            "\nSOURCE URLS (these are the only URLs you may return):\n"+json.dumps(_source_urls(job),ensure_ascii=False))
    body={"model":MODEL,"messages":[{"role":"system","content":SYSTEM},{"role":"user","content":prompt+"\nReturn JSON with exactly these keys: "+", ".join(FIELDS)}],"temperature":0.2,"max_tokens":2200}
    req=urllib.request.Request(ENDPOINT,data=json.dumps(body).encode("utf-8"),headers={"Authorization":"Bearer "+key,"Content-Type":"application/json","HTTP-Referer":"https://educationupdatehub.in","X-Title":"Education Update Hub"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=45) as r:
            data=json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail=e.read().decode("utf-8","ignore")
        raise RuntimeError(f"OpenRouter HTTP {e.code}: {detail[:800]}")
    choices=data.get("choices") or []
    if not choices: raise RuntimeError("OpenRouter returned no choices")
    content=choices[0].get("message",{}).get("content","")
    out=_json_from_text(content)
    for k in FIELDS:
        out.setdefault(k,"")
    # Hard safety gate for URLs: AI can only reuse an exact source URL.
    allowed=set(_source_urls(job))
    for k in ["apply_url","admit_card_url","result_url","answer_key_url","syllabus_url","notification_url","official_url"]:
        if out.get(k) not in allowed: out[k]=""
    # If the source record already has a canonical link, preserve it rather than inventing.
    return out
