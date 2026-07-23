import os
import re

TEMPLATE_FILE = "templates/job_template.html"
OUTPUT_FOLDER = "generated"


def slugify(text):

    text = text.lower()

    text = re.sub(r'[^a-z0-9]+', '-', text)

    text = text.strip("-")

    return text


def load_template():

    with open(
        TEMPLATE_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return f.read()


def generate_html(job):

    template = load_template()

    html = template

    html = html.replace(
        "{{TITLE}}",
        job["title"]
    )

    html = html.replace(
        "{{SOURCE}}",
        job["source"]
    )

    html = html.replace(
        "{{CATEGORY}}",
        job["category"]
    )

    html = html.replace(
        "{{URL}}",
        job["url"]
    )

    filename = slugify(
        job["title"]
    ) + ".html"

    os.makedirs(
        OUTPUT_FOLDER,
        exist_ok=True
    )

    filepath = os.path.join(
        OUTPUT_FOLDER,
        filename
    )

    with open(
        filepath,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(html)

    return filepath


def generate_all(jobs):

    generated = []

    for job in jobs:

        file = generate_html(job)

        generated.append(file)

    return generated
