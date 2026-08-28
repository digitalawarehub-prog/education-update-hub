"""Strict post filter for Education Update Hub.

The scraper sees navigation links, category landing pages, policy pages and
other site chrome.  Only a *specific* education/job update is allowed into the
automation database.  Generic words such as ``Recruitment``, ``Result`` or
``Syllabus`` are never sufficient on their own.
"""
import re
from urllib.parse import urlparse

BAD_EXACT_TITLES = {
    "home", "homepage", "about", "about us", "contact", "contact us",
    "feedback", "help", "faq", "login", "logout", "register", "registration",
    "new registration", "forgot password", "reset password", "view all", "view more",
    "read more", "more", "menu", "search", "sitemap", "vacancy", "vacancies",
    "vacancy position", "vacancy/nia", "recruitment", "recruitments",
    "view all recruitment", "recruitment advertisement", "advertisement",
    "notification", "notifications", "apply online", "online application",
    "results", "result", "old result", "old results", "latest result",
    "answer key", "answer keys", "syllabus", "admit card", "hall ticket",
    "examination", "exam", "today's exam", "todays exam", "support", "student",
    "academic courses", "terms of service", "privacy policy", "cookie policy",
    "website policies", "copyright", "accessibility", "gallery", "photo gallery",
    "government orders", "orders and notification", "circular", "circulars",
    "organization", "organisation", "organization structure", "rti", "rti manuals",
    "financial results", "quarterly financial results", "press releases",
    "search in notices and notifications", "click here", "apply links",
    "section a indicative syllabus", "section-b indicative syllabus",
}

BAD_PHRASES = (
    "view all", "view more", "read more", "click here", "click on this link",
    "modify online details", "after submission", "download notification",
    "download guidelines", "download form", "login / register", "login register",
    "forgot password", "reset password", "terms of service", "privacy policy",
    "academic courses", "support_agent", "skip to main content", "select your language",
    "unserved notices", "financial results", "quarterly financial", "blacklisted firms",
    "copyright", "all rights reserved", "sitemap", "web information manager",
    "vacancy through", "vacancy advertised", "tribunal vacancy", "post new job",
    "question bank", "press release", "press-release", "admission", "admissions",
    "course", "courses", "student", "students", "fee payment", "payment of examination fee",
)

BAD_DOMAINS = (
    "economictimes.indiatimes.com", "amarujala.com", "ndtv.in", "ndtv.com",
    "timesnowhindi.com", "jagran.com", "hindustantimes.com", "news18.com",
    "aajtak.in", "zeenews.india.com", "indiatoday.in", "firstpost.com",
    "thequint.com", "newsbytesapp.com", "freepressjournal.in",
)

BAD_URL_PARTS = (
    "/login", "/logout", "/register", "/registration", "/forgot", "/reset", "/search",
    "/about", "/contact", "/feedback", "/gallery", "/photo-gallery", "/privacy", "/cookie",
    "/sitemap", "/website-policies", "/organization", "/organisation", "/chairman", "/member",
    "/finance-controller", "/examination-controller", "/public-information-officer",
    "/appellate-authority", "/web-information-manager", "/act-and-rule", "/rti", "/manual",
    "/student", "/academic", "/event", "/archive", "/old-recruitment", "/old-result",
    "/resultold", "/financial-results", "/financial-result", "/press-release", "/press-releases",
)

GOOD_URL_PARTS = (
    "/recruitment", "/notification", "/advertisement", "/vacancy", "/career", "/careers",
    "/job", "/jobs", "/advt", "/engagement", "/apprentice", "/apprenticeship", "/result",
    "/admit-card", "/admit_card", "/answer-key", "/answer_key", "/syllabus", "/selection",
    "/exam", "/examination", "/hall-ticket", "/hall_ticket", "/merit", "/counselling",
)

RECRUITMENT_TERMS = (
    "recruitment", "recruitments", "vacancy", "vacancies", "advertisement", "advt",
    "direct recruitment", "engagement", "hiring", "appointment", "walk-in", "walk in",
    "apprentice", "apprenticeship", "application invited", "applications are invited",
    "apply online", "online application", "career", "careers", "job", "jobs",
    "भर्ती", "विज्ञापन", "विज्ञप्ति", "रिक्ति", "रिक्तियां", "आवेदन आमंत्रित",
    "ऑनलाइन आवेदन", "नियुक्ति", "अप्रेंटिस", "साक्षात्कार", "सीधी भर्ती", "पद हेतु आवेदन",
)
RESULT_TERMS = ("result", "results", "merit list", "score card", "scorecard", "individual score", "final scorecard", "recommendation", "selected candidate", "selected candidates", "selection list", "list of qualified candidates", "marks obtained", "परिणाम", "मेरिट", "संस्तुति")
ADMIT_TERMS = ("admit card", "e-admit card", "admit-card", "hall ticket", "hall-ticket", "call letter", "call letters", "call-letter", "प्रवेश पत्र")
ANSWER_TERMS = ("answer key", "answer keys", "उत्तर कुंजी", "उत्तरकुंजी")
SYLLABUS_TERMS = ("syllabus", "indicative syllabus", "पाठ्यक्रम")
SCHOLARSHIP_TERMS = ("scholarship", "छात्रवृत्ति")
SCHEME_TERMS = ("government scheme", "government schemes", "yojana", "yojana", "योजना", "सरकारी योजना", "प्रधानमंत्री योजना", "मुख्यमंत्री योजना")
SCHEME_SUPPORT_TERMS = ("benefit", "benefits", "eligibility", "subsidy", "financial assistance", "scheme details", "लाभ", "पात्रता", "अनुदान", "सहायता")
EXAM_TERMS = ("exam schedule", "exam programme", "exam program", "exam calendar", "time table", "timetable", "date sheet", "परीक्षा कार्यक्रम", "परीक्षा समय सारणी", "परीक्षा कार्यक्रम")
ROLE_TERMS = (
    "assistant", "teacher", "officer", "engineer", "technician", "constable", "inspector", "clerk",
    "stenographer", "patwari", "lekhpal", "fellow", "research", "professional", "scientist", "staff",
    "faculty", "professor", "lecturer", "driver", "junior", "senior", "manager", "analyst", "surgeon",
    "doctor", "nurse", "pharmacist", "attendant", "peon", "counsellor", "chairperson", "member",
    "teacher", "शिक्षक", "अधिकारी", "प्रोफेसर", "व्याख्याता", "अनुसंधान", "पद", "कर्मचारी", "निदेशक",
)


def clean(text):
    text = str(text or "").strip().lower()
    return re.sub(r"\s+", " ", text)


def _contains_term(text, terms):
    return any(t in text for t in terms)


def _looks_garbled(text):
    if not text:
        return True
    # Common UTF-8-as-Latin1 mojibake seen in scraped Hindi pages.
    bad = len(re.findall(r"(?:à¤|Ã|Â|â€|ðŸ)", text))
    return bad >= 2 and bad / max(1, len(text)) > 0.015


def is_bad_url(url):
    u = clean(url)
    if not u or u.startswith(("javascript:", "mailto:", "tel:", "#")):
        return True
    if any(domain in u for domain in BAD_DOMAINS):
        return True
    parsed = urlparse(u)
    if parsed.scheme not in {"http", "https"}:
        return True
    for part in BAD_URL_PARTS:
        if part in u:
            return True
    return False


def _specific_update_title(t):
    """Require enough information to identify a real update, not a menu link."""
    if _looks_garbled(t):
        return False
    if re.search(r"\b(?:post|posts|vacanc(?:y|ies)|advt?\.?\s*no\.?|notification\s*no\.?|no\.\s*\d{1,5})\b", t, re.I):
        return True
    if any(term in t for term in ROLE_TERMS):
        return True
    if re.search(r"\b20\d{2}\b", t):
        return True
    if any(p in t for p in ("applications are invited", "application invited", "for the post", "for the posts", "recruitment of", "advertisement for", "advertisement no", "online application for", "selection of")):
        return True
    # Do not accept a long sentence merely because it has many words.
    # Scraped navigation blocks are often long but are not posts.
    return False


def _specific_result(t):
    if t in {"result", "results", "old result", "old results", "latest result"}:
        return False
    if "resulted in order" in t or "resulting in" in t:
        return False
    if any(p in t for p in ("financial result", "quarterly financial", "nano fertiliser", "trial results")):
        return False
    return bool(
        re.search(r"\b20\d{2}\b", t, re.I)
        or any(p in t for p in ("result of", "results of", "re-examination results", "selected candidate", "selection list", "scorecard", "score card", "marks obtained", "merit list"))
    )


def _specific_exam(t):
    if t in {"exam", "examination", "today's exam", "todays exam"}:
        return False
    if any(p in t for p in EXAM_TERMS):
        return True
    # Generic pages such as "Examination" or "Question Bank" are not posts.
    # A named examination with a year is allowed.
    return bool(re.search(r"\b(?:exam|examination)\b", t, re.I) and re.search(r"\b20\d{2}\b", t))


def classify_post(title, url="", description="", source=""):
    """Return one of the supported post categories or None."""
    t = clean(title)
    u = clean(url)
    d = clean(description)
    if not t or len(t) < 8 or is_bad_url(u):
        return None
    if t in BAD_EXACT_TITLES:
        return None
    if any(p in t for p in BAD_PHRASES):
        return None
    if _looks_garbled(t):
        return None

    # Specific categories have priority.
    if _contains_term(t, ADMIT_TERMS) and _specific_update_title(t):
        return "Admit Card"
    if _contains_term(t, ANSWER_TERMS) and _specific_update_title(t):
        return "Answer Key"
    if _contains_term(t, RESULT_TERMS) and _specific_result(t):
        return "Result"
    if _contains_term(t, SYLLABUS_TERMS) and _specific_update_title(t):
        return "Syllabus"
    if _contains_term(t, SCHOLARSHIP_TERMS) and _specific_update_title(t):
        return "Scholarship"

    # Government-scheme posts are a separate content type.  A recruitment
    # notice must never become a scheme merely because its description/PDF
    # contains the word "scheme".  Prefer an explicit scheme/yojana title.
    has_scheme = _contains_term(t, SCHEME_TERMS)
    has_recruitment = _contains_term(t, RECRUITMENT_TERMS)
    has_role = _contains_term(t, ROLE_TERMS)
    # A word like "scheme" is common in recruitment rules/selection schemes.
    # Only classify as Government Scheme when the title itself is clearly a
    # public-benefit/yojana item and contains no job/application language.
    scheme_title = (
        any(x in t for x in ("government scheme", "government schemes", "yojana", "योजना",
                             "सरकारी योजना", "प्रधानमंत्री योजना", "मुख्यमंत्री योजना"))
        or (_contains_term(t, SCHEME_SUPPORT_TERMS) and any(x in t for x in ("scheme", "yojana", "योजना")))
    )
    scheme_job_context = any(x in t for x in (
        "scheme for selection", "scheme for appointment", "selection scheme",
        "recruitment scheme", "scheme of recruitment", "appointment scheme",
        "research assistant", "assistant professor", "assistant", "officer", "teacher",
        "engineer", "technician", "clerk", "scientist", "faculty", "professor",
        "applications are invited", "apply online", "vacancy", "vacancies", "recruitment",
        "अभ्यर्थी", "पद हेतु आवेदन"
    ))
    if has_scheme and scheme_title and not has_recruitment and not has_role and not scheme_job_context:
        return "Government Scheme"

    # Recruitment must describe an actual post/application/engagement.
    # Generic landing pages such as "Recruitment", "Vacancy" or "Advertisement
    # No. 03/2026" are intentionally rejected.
    has_recruitment = _contains_term(t, RECRUITMENT_TERMS)
    has_role = _contains_term(t, ROLE_TERMS)
    concrete_recruitment = (
        has_role
        or re.search(r"\b(?:post|posts|vacanc(?:y|ies))\b", t, re.I)
        or any(p in t for p in (
            "recruitment of", "advertisement for", "for the post", "for the posts",
            "applications are invited", "application are invited", "application invited",
            "online applications are invited", "walk-in interview", "walk in interview",
            "engagement of", "appointment of", "selection of"
        ))
    )
    non_job_context = any(p in t for p in (
        "recruitment rules", "recruitment calendar", "recruitment cell", "recruitment archive",
        "press release", "press-release", "notification of api score", "api score",
        "recruitment results", "recruitment notices", "recruitment/admission", "online application link",
        "application link", "national ict awards", "award", "student", "students", "course",
        "fee", "fees", "score", "marks", "mock test", "question bank", "question paper",
        "previous year", "rules of", "terms and conditions"
    ))
    if has_recruitment and concrete_recruitment and not non_job_context:
        return "Recruitment"

    # Only rescue a role title when the URL clearly points to a recruitment
    # resource and the page description also contains strong recruitment evidence.
    good_url = any(x in u for x in GOOD_URL_PARTS)
    if has_role and good_url and (_contains_term(d, RECRUITMENT_TERMS) or any(p in t for p in ("applications are invited", "recruitment of", "advertisement for", "for the post"))):
        return "Recruitment"

    if _specific_exam(t):
        return "Exam"

    return None


def allow_job(title, url="", description="", source=""):
    return classify_post(title, url, description, source) is not None


def is_bad_title(title):
    return classify_post(title, "https://invalid.local/", "") is None


def is_good_title(title):
    return classify_post(title, "https://example.gov.in/recruitment", "") is not None



def is_publishable(job):
    """Pipeline-level publication gate; never raises."""
    if not isinstance(job, dict):
        return False
    title = str(job.get("title") or "").strip()
    url = str(job.get("url") or job.get("source_url") or "").strip()
    description = str(job.get("description") or job.get("summary") or "").strip()
    category = str(job.get("category") or "").strip().lower()
    if not title or len(title) < 8 or category in {"", "unknown"}:
        return False
    if title.lower() in BAD_EXACT_TITLES or any(p in clean(title) for p in BAD_PHRASES):
        return False
    if _looks_garbled(title):
        return False
    # Respect an already classified category, but reject obvious generic landing pages.
    if category in {"recruitment", "banking jobs", "railway jobs", "upsc jobs", "ssc jobs", "uttarakhand jobs", "central government jobs"}:
        t = clean(title)
        generic = {"recruitment", "recruitments", "vacancy", "vacancies", "advertisement", "notification", "career", "careers", "recruitment exams", "clerical cadre", "specialist officers"}
        if t in generic:
            return False
        if _contains_term(t, RECRUITMENT_TERMS) or _contains_term(t, ROLE_TERMS) or re.search(r"\b20\d{2}\b", t):
            return True
    classified = classify_post(title, url or "https://example.gov.in/recruitment", description, str(job.get("source") or ""))
    return classified is not None
