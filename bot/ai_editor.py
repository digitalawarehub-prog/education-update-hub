
"""AI editorial layer for Education Update Hub.

This file is intentionally independent of the scraper. It accepts a job dict,
uses only supplied source facts, and returns structured fields that the existing
HTML generator understands.
"""

from __future__ import annotations
import hashlib
import json
import os
import re
from pathlib import Path

from openai import OpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
CACHE = Path(os.getenv("AI_POST_CACHE", "ai_post_cache.json"))

CATEGORIES = (
    "recruitment", "admit_card", "result", "answer_key",
    "syllabus", "entrance_exam", "notice"
)

SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "post_type": {"type": "string", "enum": list(CATEGORIES)},
        "title": {"type": "string"},
        "seo_title": {"type": "string"},
        "summary_hi": {"type": "string"},
        "department": {"type": "string"},
        "organization": {"type": "string"},
        "post_name": {"type": "string"},
        "vacancy": {"type": "string"},
        "qualification": {"type": "string"},
        "salary": {"type": "string"},
        "age_limit": {"type": "string"},
        "application_start": {"type": "string"},
        "last_date": {"type": "string"},
        "fee": {"type": "string"},
        "exam_date": {"type": "string"},
        "apply_url": {"type": "string"},
        "admit_card_url": {"type": "string"},
        "result_url": {"type": "string"},
        "answer_key_url": {"type": "string"},
        "syllabus_url": {"type": "string"},
        "notification_url": {"type": "string"},
        "official_url": {"type": "string"},
        "faq": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "properties": {"question": {"type": "string"}, "answer": {"type": "string"}},
            "required": ["question", "answer"]
        }},
        "missing_critical": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
    },
    "required": [
        "post_type","title","seo_title","summary_hi","department","organization",
        "post_name","vacancy","qualification","salary","age_limit",
        "application_start","last_date","fee","exam_date","apply_url",
        "admit_card_url","result_url","answer_key_url","syllabus_url",
        "notification_url","official_url","faq","missing_critical","confidence"
    ],
}

BASE_RULES = """
You are the editorial AI for Education Update Hub.

SOURCE-ONLY RULES:
- Use ONLY facts present in the supplied source record.
- Missing facts must be empty, never guessed.
- Never invent a URL. URLs may only be copied from supplied source fields.
- Never convert a notification PDF into Apply Online.
- Never convert an Admit Card URL into Apply Online.
- Never invent vacancy, salary, qualification, date, fee, department or exam date.
- If a value is absent, omit it from the article/table.
- Write clear natural Hindi with official English names where appropriate.
- Do not use fake urgency or misleading clickbait.
- Dates in visible output should be DD-MM-YYYY where a full numeric date exists.
"""

CATEGORY_RULES = {
"recruitment": """
Classify only actual hiring/recruitment advertisements as recruitment.
Title should emphasize organization + post + confirmed vacancy/date.
Recruitment button must use a real application URL if one is supplied.
""",
"admit_card": """
Focus on hall ticket/admit card availability, exam, download date and instructions.
Never use notification_pdf as admit_card_url.
""",
"result": """
Focus on result/scorecard declaration, result date, exam and checking process.
A result PDF is valid.
""",
"answer_key": """
Focus on answer key, provisional/final key and objection dates if supplied.
""",
"syllabus": """
Focus on syllabus, subjects, exam pattern, marks and duration if supplied.
A syllabus PDF is valid.
""",
"entrance_exam": """
Focus on entrance/admission examination, eligibility, application and exam dates.
Keep entrance exam separate from recruitment.
""",
"notice": """
Summarize the official notice/update. Do not force recruitment fields into it.
""",
}

def _clean(v):
    return re.sub(r"\s+", " ", str(v or "")).strip()

def _url(v):
    v = _clean(v)
    return v if v.startswith(("http://","https://")) else ""

def _blob(job):
    keys = [
        "title","description","summary","content","notification_text",
        "notification_content","url","apply_link","application_link",
        "official_website","notification_pdf","download_link",
        "admit_card_link","result_link","answer_key_link","syllabus_link",
        "department","organization","vacancy","qualification","salary",
        "age_limit","application_start","last_date","fee","exam_date","category"
    ]
    data = {k: job[k] for k in keys if k in job and job[k] not in ("",None,[],{})}
    return json.dumps(data, ensure_ascii=False, indent=2)[:60000]

def _load_cache():
    try:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _save_cache(c):
    CACHE.write_text(json.dumps(c, ensure_ascii=False, indent=2), encoding="utf-8")

def enrich(job):
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    key = hashlib.sha256(_blob(job).encode("utf-8")).hexdigest()
    cache = _load_cache()
    if key in cache:
        ai = cache[key]
    else:
        # First-pass classification can use the scraper's category as a hint,
        # but AI has authority to correct it from the source text.
        hint = _clean(job.get("category"))
        prompt = (
            BASE_RULES + "\nCATEGORY-SPECIFIC RULES:\n"
            + "\n".join(f"{k}: {v}" for k,v in CATEGORY_RULES.items())
            + f"\nScraper category hint: {hint}\n\nSOURCE RECORD:\n{_blob(job)}"
        )
        response = client.responses.create(
            model=MODEL,
            instructions=prompt,
            input="Return the structured editorial record.",
            text={"format":{"type":"json_schema","name":"euh_ai_post",
                            "strict":True,"schema":SCHEMA}}
        )
        ai = json.loads(response.output_text)
        cache[key] = ai
        _save_cache(cache)

    # Hard URL safety gate.
    supplied = set()
    for k in (
        "apply_link","application_link","official_website","notification_pdf",
        "download_link","admit_card_link","result_link","answer_key_link",
        "syllabus_link"
    ):
        u = _url(job.get(k))
        if u: supplied.add(u)

    for k in (
        "apply_url","admit_card_url","result_url","answer_key_url",
        "syllabus_url","notification_url","official_url"
    ):
        if _url(ai.get(k)) not in supplied:
            ai[k] = ""

    return ai
