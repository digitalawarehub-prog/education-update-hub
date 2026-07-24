import re

KEYWORDS = {
    "Latest Jobs": [
        "recruitment", "vacancy", "notification",
        "apply online", "job", "jobs", "posts",
        "appointment", "advertisement"
    ],
    "Admit Card": [
        "admit card", "hall ticket", "call letter"
    ],
    "Result": [
        "result", "final result", "merit list",
        "selection list"
    ],
    "Answer Key": [
        "answer key",
        "provisional answer key",
        "final answer key"
    ],
    "Scholarship": [
        "scholarship",
        "fellowship",
        "stipend"
    ],
    "Admission": [
        "admission",
        "registration",
        "application form"
    ],
    "Syllabus": [
        "syllabus",
        "exam pattern",
        "curriculum"
    ]
}


BAD_TITLES = [

    "accessibility",

    "act and rule",

    "click here",

    "home",

    "contact",

    "privacy",

    "feedback",

    "gallery",

    "photo",

    "video",

    "tender",

    "auction",

    "login",

    "logout",

    "copyright",

    "terms",

    "cookie",

    "faq",

    "help",

    "site map",

    "sitemap"

]


def detect_category(title):

    text = title.lower()

    for category, words in KEYWORDS.items():

        for word in words:

            if word in text:

                return category

    return "Latest Jobs"


def clean_title(title):

    if not title:

        return ""

    title = str(title)

    title = re.sub(r"\s+", " ", title)

    title = re.sub(r"\|.*$", "", title)

    title = re.sub(r"-\s*Home.*$", "", title)

    title = re.sub(r"^\d+\s*", "", title)

    title = re.sub(r"\.html$", "", title, flags=re.I)

    return title.strip()


def parse_jobs(job_list):

    parsed = []

    seen = set()

    for job in job_list:

        title = clean_title(
            job.get("title", "")
        )

        if len(title) < 15:

            continue

        title_lower = title.lower()

        if any(
            word in title_lower
            for word in BAD_TITLES
        ):

            continue

        url = job.get("url", "")

        if url in seen:

            continue

        seen.add(url)

        parsed.append({

            "source": job.get(
                "source",
                "Unknown"
            ),

            "title": title,

            "url": url,

            "category": detect_category(
                title
            )

        })

    return parsed
