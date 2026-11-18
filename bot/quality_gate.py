"""Publication quality gate: keep thin/notification-only AI records out of indexable pages.
Manual editorial posts are preserved by callers; this gate is for automated records.
"""
import re
from urllib.parse import urlparse

BLOCKED = (
    "public notice", "physical screening test", "written examination", "written test", "time table", "schedule of", "selection list", "selected candidates", "qualified candidates", "shortlisted candidates",
    "answer key", "answer-key", "admit card", "admit-card", "hall ticket", "call letter",
    "result of", "merit list", "waiting list", "score card", "scorecard",
    "exam schedule", "examination schedule", "exam date", "interview schedule",
    "corrigendum", "extension of last date", "date extended", "last date extended",
    "press release", "press-release", "appointment of", "re-appointed", "reappointed",
    "vice chancellor", "vice-chancellor", "second term", "deputation",
    "चयन सूची", "चयनित उम्मीदवार", "उत्तर कुंजी", "प्रवेश पत्र", "परिणाम",
    "तिथि बढ़ी", "अंतिम तिथि बढ़ी", "समयपरिवर्तन", "समय परिवर्तन", "लिखित परीक्षा", "शारीरिक दक्षता परीक्षा", "कुलपति", "पुनः नियुक्त", "शुल्क वापसी"
)
RECRUITMENT = (
    "recruitment", "vacancy", "vacancies", "applications are invited",
    "application invited", "apply online", "online application", "engagement of",
    "walk-in", "walk in", "apprentice", "apprenticeship", "भर्ती", "रिक्ति",
    "आवेदन आमंत्रित", "ऑनलाइन आवेदन", "सीधी भर्ती"
)
PLACEHOLDERS = {
    "", "not mentioned", "not available", "not specified", "check official notification",
    "check notification", "as per rules", "उपलब्ध नहीं", "आधिकारिक अधिसूचना देखें",
    "n/a", "na", "none", "null", "-", "--"
}

def _clean(value):
    return re.sub(r"\\s+", " ", str(value or "")).strip()

def _real(value):
    return _clean(value).casefold() not in PLACEHOLDERS

def _salary_ok(value):
    s = _clean(value).casefold()
    if not s:
        return True
    if any(x in s for x in ("application fee", "exam fee", "processing fee", "page no", "page number")):
        return False
    if not any(x in s for x in ("pay level", "pay scale", "basic pay", "salary", "remuneration",
                                "consolidated pay", "per month", "per annum", "stipend",
                                "emolument", "pay matrix", "level-")):
        return False
    return not re.search(r"[\\^~`]{2,}|(?:ment done|freq:|qv\\^|f41q)", s)

def is_publishable(job):
    if not isinstance(job, dict):
        return False
    title = _clean(job.get("title"))
    url = _clean(job.get("url"))
    if len(title) < 20 or not url or urlparse(url).scheme not in {"http", "https"}:
        return False
    low = title.casefold()
    if any(term in low for term in BLOCKED):
        return False

    category = _clean(job.get("category") or job.get("post_type")).casefold()
    is_recruitment = "recruit" in category or "भर्ती" in category or any(x in low for x in RECRUITMENT)
    if not is_recruitment:
        # Only retain a substantial scholarship explainer among automated
        # non-recruitment items. Results, schedules, admit cards and short
        # notices are better kept out of indexable public pages.
        if job.get("ai_generated") or job.get("ai_model"):
            is_scholarship = "scholarship" in category or "छात्रवृत्ति" in category or "छात्रवृत्ति" in low
            body = " ".join(_clean(job.get(k)) for k in ("summary", "intro", "description", "content", "how_to"))
            return is_scholarship and len(body) >= 500 and _real(job.get("official_website"))
        return True

    if not any(x in low for x in RECRUITMENT):
        return False
    if not _salary_ok(job.get("salary")):
        return False

    # An AI recruitment page needs a readable explanation and verifiable facts.
    if job.get("ai_generated") or job.get("ai_model"):
        summary = _clean(job.get("summary"))
        intro = _clean(job.get("intro"))
        body = " ".join(_clean(job.get(k)) for k in ("summary", "intro", "description", "content", "how_to", "important_notes"))
        detail_keys = ("vacancy", "qualification", "age_limit", "application_fee",
                       "selection_process", "last_date", "application_start_date", "salary")
        details = sum(1 for k in detail_keys if _real(job.get(k)))
        verified_link = _real(job.get("notification_pdf")) or _real(job.get("apply_link")) or _real(job.get("official_website"))
        if len(summary) < 120 or len(intro) < 100 or len(body) < 380:
            return False
        if details < 2 or not verified_link:
            return False
    return True
