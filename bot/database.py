import json
import os
from pathlib import Path

DB_FILE = Path("database/jobs.json")


def load_jobs():
    if not DB_FILE.exists():
        return []

    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_jobs(jobs):
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)

    cleaned = []

    for job in jobs:
        item = dict(job)

        # बड़े fields database में save नहीं होंगे
        item.pop("content", None)
        item.pop("html", None)

        if "description" in item and isinstance(item["description"], str):
            item["description"] = item["description"][:500]

        cleaned.append(item)

    tmp = DB_FILE.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(DB_FILE)
