"""OpenRouter editorial layer for Education Update Hub.

The AI is an editor, not the source of truth. It may improve title/summary,
classify the post and identify an organization/department from supplied source
text, but URLs and factual numeric/date fields are kept from the scraper unless
an exact source value is returned and validated.
"""
from __future__ import annotations
import json, logging, os, re
from typing import Any, Dict
import requests

logger = logging.getLogger("AIEditor")

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")
API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
MAX_SOURCE = 14000

ALLOWED_TYPES = {"recruitment","admit-card","result","answer-key","syllabus","entrance","interview","scholarship","notice","other"}
TYPE_TO_CATEGORY = {
    "recruitment":"Recruitment", "admit-card":"Admit Card", "result":"Result",
    "answer-key":"Answer Key", "syllabus":"Syllabus", "entrance":"Entrance Exams",
    "interview":"Recruitment", "scholarship":"Scholarship", "notice":"Recruitment",
    "other":"Recruitment",
}
BAD_VALUES = {"government","sarkari vibhag","not mentioned","not available","check official notification","as per rules","unknown","none","null",""}


def _clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def _extract_json(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    # Remove markdown fences and common prose around JSON.
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            try:
                obj = json.loads(text[start:end+1])
                return obj if isinstance(obj, dict) else {}
            except Exception:
                pass
    return {}


def _source_text(job: Dict[str, Any]) -> str:
    chunks = []
    for key in ("title","description","content","notification_text","raw_text","body","text"):
        v = _clean(job.get(key))
        if v:
            chunks.append(f"{key.upper()}: {v}")
    return "\n".join(chunks)[:MAX_SOURCE]


def _valid_department(v: str) -> bool:
    s = _clean(v)
    return bool(s) and s.casefold() not in BAD_VALUES and len(s) <= 120 and not re.search(r"https?://|www\\.", s, re.I)


def _valid_title(v: str) -> bool:
    s = _clean(v)
    if not (12 <= len(s) <= 180): return False
    if s.count("|") > 1 or s.endswith((":", "-", "–")): return False
    # Reject the spaced-glyph Hindi seen in weak free-model outputs.
    letters = re.findall(r"[A-Za-z\u0900-\u097F]", s)
    if len(letters) >= 20:
        single_chunks = re.findall(r"(?<![A-Za-z\u0900-\u097F])[A-Za-z\u0900-\u097F](?![A-Za-z\u0900-\u097F])", s)
        if len(single_chunks) > len(letters) * 0.18:
            return False
    return True


def _valid_summary(v: str) -> bool:
    s = _clean(v)
    return 60 <= len(s) <= 900 and "http://" not in s and "https://" not in s


def _preserve_links(job: Dict[str, Any], out: Dict[str, Any]) -> None:
    # AI must never invent or replace URLs. Only the deterministic scraper can
    # supply these action links.
    for key in ("apply_link","notification_pdf","official_notification_pdf","official_website","admit_card_url","result_url","answer_key_url","syllabus_url","entrance_url","interview_url"):
        if key in job:
            out[key] = job.get(key) or ""


def enrich(job: Dict[str, Any]) -> Dict[str, Any]:
    """Return a safely enriched copy. If AI fails, return the original job."""
    base = dict(job)
    if not API_KEY:
        logger.warning("AI EDIT SKIPPED | OPENROUTER_API_KEY missing | %s", job.get("title",""))
        return base

    source = _source_text(job)
    if len(source) < 30:
        logger.warning("AI EDIT SKIPPED | insufficient source | %s", job.get("title",""))
        return base

    current_type = _clean(job.get("post_type") or job.get("category")).casefold()
    prompt = f"""You are the senior editor of Education Update Hub, an Indian government/education updates website.
Use ONLY the supplied source. Do not invent facts, dates, numbers, URLs, departments, eligibility, salary or fees.
Return ONLY one compact valid JSON object. No markdown. No comments.

CLASSIFICATION RULES:
- admit-card: title/source is about admit card, hall ticket, call letter or downloading an entry ticket.
- result: result, merit list, scorecard, selected candidates, marks/results.
- answer-key: answer key/objection.
- syllabus: syllabus/exam pattern.
- entrance: entrance/admission examination or registration, not a job recruitment.
- interview: walk-in interview/interview schedule/interview result; NEVER call it recruitment.
- recruitment: applications/vacancies/appointment/engagement for posts.
- scholarship: scholarship/fellowship for students.
- notice: important notice/corrigendum without a better category.
If title clearly identifies the type, prefer the title over words appearing inside a PDF.

TITLE: Create one natural, clickable Hindi title with important proper nouns in their original form. Do NOT spell letters with spaces. Do not add a number unless present in source. Maximum 150 characters.
SUMMARY: Write 2-4 useful Hindi sentences specific to this update. Do not use generic filler such as "इस पोस्ट में पद, योग्यता, वेतन..." unless those details are actually relevant.
DEPARTMENT: Give the organization/department named in the source. If not clear, return empty string. Never return "Government".

JSON keys exactly:
category, post_type, title, summary, department, organization, exam_name, post_name, vacancy, qualification, salary, age_limit, application_fee, selection_process, exam_date, application_start_date, last_date, notification_date

Existing detected type: {current_type}

SOURCE:
{source}
"""

    payload = {
        "model": MODEL,
        "messages": [
            {"role":"system","content":"You output strict JSON only. Accuracy is more important than completeness."},
            {"role":"user","content":prompt},
        ],
        "temperature": 0.15,
        "max_tokens": 1600,
    }
    try:
        r = requests.post(
            ENDPOINT,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://educationupdatehub.in",
                "X-Title": "Education Update Hub",
            },
            json=payload,
            timeout=(10, 45),
        )
        if r.status_code == 429:
            logger.warning("AI RATE LIMIT | OpenRouter daily/free limit reached. Stopping AI calls for this run.")
            base["_ai_rate_limited"] = True
            return base
        r.raise_for_status()
        data = r.json()
        content = (((data.get("choices") or [{}])[0]).get("message") or {}).get("content", "")
        ai = _extract_json(content)
        if not ai:
            raise ValueError("AI returned invalid JSON")

        out = dict(base)
        ptype = _clean(ai.get("post_type")).casefold()
        if ptype not in ALLOWED_TYPES:
            ptype = _clean(base.get("post_type") or "other").casefold()
        # Never let AI demote a deterministic strong type based on PDF body text.
        deterministic = _clean(base.get("post_type")).casefold()
        if deterministic in ALLOWED_TYPES and deterministic != "other":
            if deterministic == "recruitment" and ptype == "interview":
                # Title-level interview detection in the source wins.
                pass
            elif deterministic in {"admit-card","result","answer-key","syllabus","entrance","interview","scholarship"}:
                ptype = deterministic
        out["post_type"] = ptype
        out["category"] = TYPE_TO_CATEGORY.get(ptype, base.get("category") or "Recruitment")

        if _valid_title(ai.get("title")):
            out["title"] = _clean(ai["title"])
        if _valid_summary(ai.get("summary")):
            out["description"] = _clean(ai["summary"])
            out["ai_summary"] = _clean(ai["summary"])
        if _valid_department(ai.get("department")):
            out["department"] = _clean(ai["department"])
            out["organization"] = _clean(ai.get("organization")) or out.get("organization", "")
        elif _valid_department(ai.get("organization")) and _clean(base.get("department")).casefold() in BAD_VALUES:
            out["department"] = _clean(ai["organization"])

        # AI factual fields are accepted only when concise and consistent with
        # the supplied source text; this prevents free models from hallucinating.
        source_low = source.casefold()
        for key in ("exam_name","post_name","vacancy","qualification","salary","age_limit","application_fee","selection_process","exam_date","application_start_date","last_date","notification_date"):
            val = _clean(ai.get(key))
            if not val or val.casefold() in BAD_VALUES or len(val) > 500:
                continue
            # Dates/numbers must have at least one exact-looking source anchor.
            if key in {"vacancy","exam_date","application_start_date","last_date","notification_date"}:
                nums = re.findall(r"\d{1,4}", val)
                if nums and not any(n in source_low for n in nums[:4]):
                    continue
            if key == "vacancy" and not re.search(r"\d", val):
                continue
            out[key] = val

        _preserve_links(base, out)
        logger.info("AI EDITED | %s | type=%s | category=%s", out.get("title",""), ptype, out.get("category",""))
        return out
    except Exception as exc:
        logger.warning("AI EDIT FAILED | %s | %s", job.get("title",""), exc)
        return base
