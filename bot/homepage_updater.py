import os
import re

INDEX_FILE = "index.html"

START_MARKER = "<!-- AUTO_POSTS_START -->"
END_MARKER = "<!-- AUTO_POSTS_END -->"


def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = text.strip("-")
    return text


def create_post(job):

    filename = slugify(job["title"]) + ".html"

    return f'<li><a href="generated/{filename}">{job["title"]}</a></li>'


def update_homepage(jobs):

    if not os.path.exists(INDEX_FILE):
        print("index.html not found")
        return

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    start = html.find(START_MARKER)
    end = html.find(END_MARKER)

    if start == -1 or end == -1:
        print("AUTO markers not found")
        return

    posts = ""

    for job in jobs:
        posts += create_post(job) + "\n"

    new_html = (
        html[:start + len(START_MARKER)]
        + "\n"
        + posts
        + html[end:]
    )

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(new_html)

    print("Homepage Updated Successfully")
