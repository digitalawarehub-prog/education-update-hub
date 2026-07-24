import json
import os

DATABASE = "database/jobs.json"


def load_database():

    os.makedirs("database", exist_ok=True)

    if not os.path.exists(DATABASE):

        with open(DATABASE, "w", encoding="utf-8") as f:
            json.dump([], f)

        return []

    try:

        with open(DATABASE, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception:

        return []


def save_database(data):

    with open(DATABASE, "w", encoding="utf-8") as f:

        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False
        )


def filter_new_jobs(jobs):

    database = load_database()

    existing_urls = {

        item["url"]

        for item in database

        if "url" in item

    }

    new_jobs = []

    for job in jobs:

        url = job.get("url")

        if not url:

            continue

        if url in existing_urls:

            continue

        existing_urls.add(url)

        database.append(job)

        new_jobs.append(job)

    save_database(database)

    print(f"New Jobs Added : {len(new_jobs)}")

    return new_jobs
