import os
import re

INDEX_FILE = "index.html"

START_MARKER = "<!-- AUTO_POSTS_START -->"
END_MARKER = "<!-- AUTO_POSTS_END -->"

MAX_POSTS = 30


def slugify(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def create_post(job):

    filename = slugify(job["title"]) + ".html"

    return f'<li><a href="generated/{filename}">{job["title"]}</a></li>'


def update_homepage(jobs):

    if not jobs:
        print("No new jobs. Homepage skipped.")
        return

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

    old_section = html[start + len(START_MARKER):end]

    old_posts = re.findall(
        r"<li><a.*?</li>",
        old_section,
        flags=re.DOTALL
    )

    new_posts = [create_post(job) for job in jobs]

    merged = new_posts + old_posts

    # Duplicate हटाएँ
    seen = set()
    final = []

    for post in merged:

        if post not in seen:
            seen.add(post)
            final.append(post)

    final = final[:MAX_POSTS]

    new_html = (
        html[:start + len(START_MARKER)]
        + "\n"
        + "\n".join(final)
        + "\n"
        + html[end:]
    )

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(new_html)

    print(f"Homepage Updated ({len(final)} posts)")
