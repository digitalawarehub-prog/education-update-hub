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
# Invalid Titles
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

    "accessibility",
    "accessibility tools",
    "hide images",
    "skip to main content",

    "website policies",
    "privacy policy",
    "copyright",
    "terms",

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
GOOD_KEYWORDS = [

    "recruitment",
    "notification",
    "advertisement",
    "vacancy",
    "apply",

    "result",
    "answer key",
    "admit card",

    "syllabus",

    "exam",

    "calendar",

    "document",

    "selection",

    "recommendation",

    "revised",

    "corrigendum",

    "merit",

    "list",

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

    "pdf"

]
def clean(text):

    if not text:
        return ""

    text = text.strip().lower()

    text = re.sub(r"\s+", " ", text)

    return text


def is_bad_url(url):

    url = clean(url)

    for bad in BAD_URLS:

        if url.startswith(bad):
            return True

    return False


def is_bad_title(title):

    title = clean(title)

    if len(title) < 3:
        return True

    for bad in BAD_TITLES:

        if bad in title:
            return True

    return False


def is_good_title(title):

    title = clean(title)

    for word in GOOD_KEYWORDS:

        if word in title:
            return True

    return False


def allow_job(title, url):

    if is_bad_url(url):
        return False

    if is_bad_title(title):
        return False

    if not is_good_title(title):

        if not any(ord(c) > 127 for c in title):
            return False

    return True
