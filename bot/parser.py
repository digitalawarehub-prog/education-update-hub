import re

KEYWORDS = {
    "Latest Jobs": [
        "recruitment", "vacancy", "notification",
        "apply online", "job", "posts",
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


def detect_category(title):
    text = title.lower()

    for category, words in KEYWORDS.items():
        for word in words:
            if word in text:
                return category

    return "Latest Updates"


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

    for job in job_list:

        title = clean_title(job.get("title", ""))

        # बहुत छोटे या बेकार Title छोड़ दें
        if len(title) < 10:
            continue

        parsed.append({

            "source": job.get("source", "Unknown"),

            "title": title,

            "url": job.get("url", ""),

            "category": detect_category(title)

        })

    return parsed
