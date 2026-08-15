import re

# -----------------------------------
# Invalid URLs
# -----------------------------------

BAD_URLS = [
    "javascript:",
    "#",
    "mailto:",
    "tel:",
]

# -----------------------------------
# Invalid / Navigation Titles
# -----------------------------------

BAD_TITLES = {
    "home",
    "homepage",
    "about",
    "about us",
    "contact",
    "contact us",
    "feedback",
    "help",
    "faq",
    "login",
    "logout",
    "search",
    "support",
    "student",
    "event",
    "academic",
    "view all",
    "view more",
    "more",
    "results",
    "view results",
    "register",
    "registration",
    "new registration",
    "step-1: new registration",
    "forgot password",
    "reset password",
    "download hindi notification",
    "download english notification",
    "download notification",
    "download guidelines for candidates for filing up online application",
    "recruitment/admission links",
    "vacancy position",
    "vacancy/nia",
    "skip to main content",
    "website policies",
    "privacy policy",
    "copyright",
    "terms",
    "terms and conditions",
    "organisation",
    "organization",
    "organization structure",
    "composition of the commission",
    "chairman",
    "hon'ble chairman",
    "honble chairman",
    "members",
    "hon'ble members",
    "finance controller",
    "controller",
    "different section",
    "public information officer",
    "appellate authority",
    "rti",
    "rti manuals",
    "photo gallery",
    "gallery",
    "government orders",
    "cm dashboard",
    "cm office",
    "digital uttarakhand",
    "national portal of india",
    "web information manager",
    "nic",
    "ministry of electronics & information technology",
}

# -----------------------------------
# Navigation / Non-job phrases
# -----------------------------------

IGNORE_PHRASES = [
    "forgot password",
    "new registration",
    "step-1",
    "step 1",
    "download hindi notification",
    "download english notification",
    "download notification",
    "download guidelines",
    "view all",
    "view more",
    "recruitment/admission links",
    "vacancy position",
    "vacancy/nia",
    "skip to main content",
    "select your language",
    "login register",
    "login / register",
    "home -",
    "home >",
]

# -----------------------------------
# Recruitment / Result Keywords
# -----------------------------------

GOOD_KEYWORDS = [
    "recruitment",
    "notification",
    "advertisement",
    "vacancy",
    "vacancies",
    "apply online",
    "application invited",
    "applications are invited",
    "engagement",
    "appointment",
    "walk-in",
    "walk in",
    "interview",
    "apprentice",
    "apprenticeship",
    "hiring",
    "job",
    "jobs",
    "result",
    "answer key",
    "admit card",
    "syllabus",
    "exam",
    "selection",
    "recommendation",
    "revised",
    "corrigendum",
    "merit",
    "shortlisted",
    "shortlist",
    "document verification",
    "counselling",
    "driver",
    "assistant",
    "teacher",
    "officer",
    "engineer",
    "technician",
    "junior",
    "senior",
    "constable",
    "inspector",
    "agriculture",
    "clerk",
    "stenographer",
    "patwari",
    "lekhpal",
    "agricultural",
    "livestock",
    "fellow",
    "research",
    "professional",
    "scientist",
    "staff",
    "faculty",
    "professor",
    "lecturer",
    "pdf",
]

# -----------------------------------
# Strong non-job URL indicators
# -----------------------------------

BAD_URL_WORDS = [
    "/login",
    "/logout",
    "/register",
    "/registration",
    "/forgot",
    "/reset-password",
    "/search",
    "/home",
    "/about",
    "/contact",
    "/gallery",
    "/feedback",
    "/help",
    "/student",
    "/event",
    "/academic",
]

BAD_DOWNLOAD_TITLE_PREFIXES = (
    "download hindi notification",
    "download english notification",
    "download notification",
    "download guidelines",
)

# -----------------------------------
# Helpers
# -----------------------------------

def clean(text):
    if not text:
        return ""

    text = str(text).strip().lower()
    text = re.sub(r"\s+", " ", text)

    return text


def is_bad_url(url):
    url = clean(url)

    if not url:
        return True

    for bad in BAD_URLS:
        if url.startswith(bad):
            return True

    for bad in BAD_URL_WORDS:
        if bad in url:
            return True

    return False


def is_bad_title(title):
    title = clean(title)

    if len(title) < 3:
        return True

    if title in BAD_TITLES:
        return True

    for phrase in IGNORE_PHRASES:
        if phrase in title:
            return True

    for prefix in BAD_DOWNLOAD_TITLE_PREFIXES:
        if title.startswith(prefix):
            return True

    return False


def is_good_title(title):
    title = clean(title)

    for word in GOOD_KEYWORDS:
        if word in title:
            return True

    # Preserve genuine Indian-language notices.
    if any(ord(c) > 127 for c in title):
        return True

    return False


def allow_job(title, url):
    title = clean(title)
    url = clean(url)

    if is_bad_url(url):
        return False

    if is_bad_title(title):
        return False

    if not is_good_title(title):
        return False

    return True
