import os

INDEX_FILE = "index.html"

START_MARKER = "<!-- AUTO_POSTS_START -->"
END_MARKER = "<!-- AUTO_POSTS_END -->"


def create_post_card(job):

    filename = (
        job["title"]
        .lower()
        .replace(" ", "-")
        .replace("/", "-")
    ) + ".html"

    card = f"""
<div class="latest-card">
    <span class="category">{job['category']}</span>

    <h3>
        <a href="generated/{filename}">
            {job['title']}
        </a>
    </h3>

    <p>
        Source : {job['source']}
    </p>
</div>
"""

    return card


def update_homepage(jobs):

    if not os.path.exists(INDEX_FILE):
        print("index.html not found")
        return

    with open(
        INDEX_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        html = f.read()

    start = html.find(START_MARKER)
    end = html.find(END_MARKER)

    if start == -1 or end == -1:
        print("Markers not found")
        return

    cards = ""

    for job in jobs:
        cards += create_post_card(job)

    new_html = (
        html[:start + len(START_MARKER)]
        + "\n"
        + cards
        + "\n"
        + html[end:]
    )

    with open(
        INDEX_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(new_html)

    print("Homepage Updated Successfully")
