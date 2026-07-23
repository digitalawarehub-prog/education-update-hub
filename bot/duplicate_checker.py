import json
import os

DATABASE = "database/jobs.json"


def load_database():

    if not os.path.exists(DATABASE):
        return []

    with open(DATABASE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_database(data):

    with open(DATABASE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


def is_duplicate(job):

    database = load_database()

    for item in database:

        if item["url"] == job["url"]:
            return True

    return False


def add_job(job):

    database = load_database()

    database.append(job)

    save_database(database)


def filter_new_jobs(jobs):

    new_jobs = []

    for job in jobs:

        if not is_duplicate(job):

            add_job(job)

            new_jobs.append(job)

    return new_jobs
