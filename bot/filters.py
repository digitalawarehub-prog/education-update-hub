"""Strict validation and classification for Education Update Hub automation.
Only genuine update/recruitment/result/admit-card/etc. pages are allowed.
"""
import re
from urllib.parse import urlparse

BAD_EXACT_TITLES = {
    "home", "homepage", "about", "about us", "contact", "contact us",
    "feedback", "help", "faq", "login", "logout", "register", "registration",
    "new registration", "forgot password", "reset password", "view all", "view more",
    "read more", "click here", "more", "menu", "search", "sitemap", "vacancy",
    "vacancies", "vacancy/nia", "vacancy position", "recruitment/admission links",
    "download notification", "download hindi notification", "download english notification",
    "download guidelines", "download guidelines for candidates for filing up online application",
    "skip to main content", "select your language", "website policies", "privacy policy",
    "terms and conditions", "copyright", "accessibility", "photo gallery", "gallery",
    "government orders", "national portal of india", "web information manager",
    "public information officer", "appellate authority", "finance controller",
    "examination controller", "organization", "organisation", "organization structure",
    "composition of the commission", "different section", "rti", "rti manuals",
    "step-1: new registration", "step 1: new registration",
}

BAD_PHRASES = (
    "forgot password", "reset password", "new registration", "step-1", "step 1",
    "download hindi notification", "download english notification", "download notification",
    "download guidelines", "view all", "view more", "read more", "recruitment/admission links",
    "vacancy position", "vacancy/nia", "skip to main content", "select your language",
    "login register", "login / register", "home -", "home >", "forget password",
)

BAD_URL_PARTS = (
    "/login", "/logout", "/register", "/registration", "/forgot", "/reset", "/search",
    "/about", "/contact", "/feedback", "/gallery", "/photo-gallery", "/privacy", "/cookie",
    "/sitemap", "/website-policies", "/organization", "/organisation", "/chairman", "/member",
    "/finance-controller", "/examination-controller", "/public-information-officer",
    "/appellate-authority", "/web-information-manager", "/act-and-rule", "/rti", "/manual",
    "/student", "/academic", "/event", "/archive", "/old-recruitment",
)

GOOD_URL_PARTS = (
    "/recruitment", "/notification", "/advertisement", "/vacancy", "/career", "/careers",
    "/job", "/jobs", "/advt", "/engagement", "/apprentice", "/apprenticeship", "/result",
    "/admit-card", "/admit_card", "/answer-key", "/answer_key", "/syllabus", "/selection",
    "/exam", "/examination", "/hall-ticket", "/merit", "/counselling",
)

RECRUITMENT_TERMS = (
    "recruitment", "vacancy", "vacancies", "advertisement", "advt", "direct recruitment",
    "engagement", "hiring", "appointment", "walk-in", "walk in", "apprentice", "apprenticeship",
    "application invited", "applications are invited", "apply online", "online application", "career",
    "job", "jobs", "भर्ती", "विज्ञापन", "विज्ञप्ति", "रिक्ति", "रिक्तियां", "आवेदन आमंत्रित",
    "ऑनलाइन आवेदन", "नियुक्ति", "अप्रेंटिस", "साक्षात्कार", "सीधी भर्ती",
)
RESULT_TERMS = ("result", "results", "merit list", "score card", "recommendation", "परिणाम", "मेरिट", "संस्तुति")
ADMIT_TERMS = ("admit card", "hall ticket", "call letter", "प्रवेश पत्र")
ANSWER_TERMS = ("answer key", "answer keys", "उत्तर कुंजी", "उत्तरकुंजी")
SYLLABUS_TERMS = ("syllabus", "पाठ्यक्रम")
SCHOLARSHIP_TERMS = ("scholarship", "छात्रवृत्ति")
EXAM_TERMS = ("exam schedule", "exam programme", "exam program", "exam calendar", "time table", "timetable", "date sheet", "परीक्षा कार्यक्रम", "परीक्षा समय सारणी")
ROLE_TERMS = (
    "assistant", "teacher", "officer", "engineer", "technician", "constable", "inspector", "clerk",
    "stenographer", "patwari", "lekhpal", "fellow", "research", "professional", "scientist", "staff",
    "faculty", "professor", "lecturer", "driver", "junior", "senior", "कर्मचारी", "अधिकारी", "शिक्षक",
    "प्रोफेसर", "व्याख्याता", "अनुसंधान",
)


def clean(text):
    text = str(text or "").strip().lower()
    return re.sub(r"\s+", " ", text)


def is_bad_url(url):
    u = clean(url)
    if not u or u.startswith(("javascript:", "mailto:", "tel:", "#")):
        return True
    for part in BAD_URL_PARTS:
        if part in u:
            return True
    return False


def classify_post(title, url="", description="", source=""):
    """Return the exact post category or None. Never classify generic pages as jobs."""
    t = clean(title)
    u = clean(url)
    d = clean(description)
    if not t or len(t) < 8 or is_bad_url(u):
        return None
    if t in BAD_EXACT_TITLES or any(p in t for p in BAD_PHRASES):
        return None
    if any(p in u for p in BAD_URL_PARTS):
        return None

    # Specific categories have priority over recruitment wording.
    if any(x in t for x in ADMIT_TERMS): return "Admit Card"
    if any(x in t for x in ANSWER_TERMS): return "Answer Key"
    if any(x in t for x in RESULT_TERMS): return "Result"
    if any(x in t for x in SYLLABUS_TERMS): return "Syllabus"
    if any(x in t for x in SCHOLARSHIP_TERMS): return "Scholarship"
    if any(x in t for x in EXAM_TERMS): return "Exam"

    has_recruitment = any(x in t for x in RECRUITMENT_TERMS)
    has_role = any(x in t for x in ROLE_TERMS)
    good_url = any(x in u for x in GOOD_URL_PARTS)

    # A generic word such as notification/exam/application is not enough.
    if has_recruitment:
        return "Recruitment"
    if has_role and good_url:
        return "Recruitment"

    # Content can rescue a link whose title is a specific role, but only if
    # the page URL itself is clearly a job/notification resource.
    if good_url and any(x in d for x in RECRUITMENT_TERMS):
        return "Recruitment"

    return None


def allow_job(title, url="", description="", source=""):
    return classify_post(title, url, description, source) is not None


def is_bad_title(title):
    return classify_post(title, "https://invalid.local/") is None


def is_good_title(title):
    # Title-only check: require an actual recruitment/update signal.
    t = clean(title)
    if t in BAD_EXACT_TITLES or any(p in t for p in BAD_PHRASES):
        return False
    return any(x in t for x in (RECRUITMENT_TERMS + RESULT_TERMS + ADMIT_TERMS + ANSWER_TERMS + SYLLABUS_TERMS + SCHOLARSHIP_TERMS + EXAM_TERMS))
