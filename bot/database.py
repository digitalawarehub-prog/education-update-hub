import json
from pathlib import Path

DB_FILE = Path("database/jobs.json")


def load_jobs():

    if not DB_FILE.exists():
        return []

    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_jobs(jobs):

    DB_FILE.parent.mkdir(exist_ok=True)

    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(
            jobs,
            f,
            ensure_ascii=False,
            indent=2
        )
