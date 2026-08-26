"""Stable source scraping engine for Education Update Hub.

This module deliberately contains no HTML/homepage/database generation logic.
It only fetches source adapters and returns valid raw jobs.  Publishing is
handled by monitor.py so one failing source cannot corrupt the site build.
"""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable

from adapters import get_adapter
from utils.logger import logger

MAX_WORKERS = int(os.getenv("EHU_SOURCE_WORKERS", "6"))


def validate_adapter_jobs(jobs):
    out=[]
    for job in jobs or []:
        if not isinstance(job, dict):
            continue
        title=str(job.get("title") or "").strip()
        url=str(job.get("url") or "").strip()
        if not title or not url:
            continue
        if "{{" in title or "translate" in title.casefold():
            continue
        item=dict(job)
        item["title"]=title
        item["url"]=url
        out.append(item)
    return out


def scrape_source(source):
    name=str((source or {}).get("name") or "Unknown")
    try:
        adapter=get_adapter(source)
        logger.info("SOURCE START | %s | adapter=%s", name, (source or {}).get("adapter","generic"))
        jobs=validate_adapter_jobs(adapter.scrape(source))
        logger.info("SOURCE DONE | %s | jobs=%d", name, len(jobs))
        return jobs
    except Exception as exc:
        logger.warning("SOURCE FAILED | %s | %s", name, exc.__class__.__name__)
        logger.exception("Source failure detail: %s", name)
        return []


def scrape_all_sources(sources, workers=None):
    sources=list(sources or [])
    workers=max(1, int(workers or MAX_WORKERS))
    all_jobs=[]
    failed=[]
    logger.info("SOURCE BATCH | total=%d workers=%d", len(sources), workers)
    with ThreadPoolExecutor(max_workers=min(workers,len(sources) or 1), thread_name_prefix="ehu") as executor:
        future_map={executor.submit(scrape_source,s):s for s in sources}
        for future in as_completed(future_map):
            source=future_map[future]
            try:
                jobs=future.result()
            except Exception as exc:
                jobs=[]
                failed.append(source)
                logger.warning("SOURCE FUTURE FAILED | %s | %s", source.get("name"), exc.__class__.__name__)
            if jobs:
                all_jobs.extend(jobs)
            elif source not in failed:
                # A cleanly unreachable/blocked source is recorded for reporting only.
                failed.append(source)
    # De-duplicate source output without changing job content.
    seen=set(); unique=[]
    for job in all_jobs:
        key=(str(job.get("title") or "").casefold(), str(job.get("url") or "").casefold())
        if key in seen: continue
        seen.add(key); unique.append(job)
    logger.info("SCRAPE SUMMARY | sources=%d jobs=%d failed=%d", len(sources), len(unique), len(failed))
    return unique, failed


def run_scraping(sources):
    return scrape_all_sources(sources)


def load_sources():
    path=BOT / "sources.json"
    if not path.exists():
        logger.error("sources.json not found: %s", path)
        return []
    import json
    try:
        data=json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        logger.exception("Invalid sources.json")
        return []
    return [dict(x) for x in data if isinstance(x,dict) and x.get("enabled",True)]
