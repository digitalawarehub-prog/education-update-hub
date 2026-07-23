import re

KEYWORDS = {
    "Latest Jobs": [
        "recruitment", "vacancy", "notification", "apply online",
        "job", "posts", "appointment", "advertisement"
    ],
    "Admit Card": [
        "admit card", "hall ticket", "call letter"
    ],
    "Result": [
        "result", "final result", "merit list", "selection list"
    ],
    "Answer Key": [
        "answer key", "provisional answer key", "final answer key"
    ],
    "Scholarship": [
        "scholarship", "fellowship", "stipend"
    ],
    "Admission": [
        "admission", "registration", "application form"
    ],
    "Syllabus": [
        "syllabus", "exam pattern", "curriculum"
    ]
}


def detect_category(title):
    text = title.lower()

    for category, words in KEYWORDS.items():
        for word in words:
            if word.lower() in text:
                return category

    return "Latest Updates"


def clean_title(title):
    title = re.sub(r"\s+", " ", title)
    return title.strip()


def parse_jobs(job_list):
    parsed = []

    for job in job_list:

        title = clean_title(job["title"])

        parsed.append({
            "source": job["source"],
            "title": title,
            "url": job["url"],
            "category": detect_category(title)
        })

    return parsed
