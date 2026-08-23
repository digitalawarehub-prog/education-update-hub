"""Expired recruitment archive for Education Update Hub."""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from html import escape
ROOT=Path(__file__).resolve().parent.parent
DB=ROOT/"database"/"archive.json"
PAGE=ROOT/"archive.html"
def _parse_date(v):
    s=str(v or "").strip()
    for fmt in ("%d-%m-%Y","%d/%m/%Y","%d.%m.%Y","%Y-%m-%d","%d %B %Y","%d %b %Y"):
        try: return datetime.strptime(s,fmt).date()
        except Exception: pass
    return None
def is_expired(job):
    d=_parse_date(job.get("last_date")); return bool(d and d < datetime.now().date())
def archive_expired_jobs(jobs):
    DB.parent.mkdir(parents=True,exist_ok=True)
    try: existing=json.loads(DB.read_text(encoding="utf-8")) if DB.exists() else []
    except Exception: existing=[]
    merged={str(j.get("job_id") or j.get("url") or j.get("title")):dict(j) for j in existing if isinstance(j,dict)}
    for j in jobs or []:
        if not isinstance(j,dict) or not is_expired(j): continue
        key=str(j.get("job_id") or j.get("url") or j.get("title")); merged[key]=dict(j)
    DB.write_text(json.dumps(list(merged.values()),ensure_ascii=False,indent=2),encoding="utf-8")
def rebuild_archive_page():
    try: jobs=json.loads(DB.read_text(encoding="utf-8")) if DB.exists() else []
    except Exception: jobs=[]
    rows=[]
    for j in jobs:
        title=escape(str(j.get("title","")).strip())
        if not title: continue
        href=str(j.get("html_file") or "").strip()
        if not href:
            slug=str(j.get("slug") or "").strip()
            if slug: href=f"generated/posts/{slug}.html"
        link=f'<a href="/{escape(href.lstrip("/"))}">{title}</a>' if href else title
        rows.append(f'<li><strong>{link}</strong><br><span>Last Date: {escape(str(j.get("last_date") or "उपलब्ध नहीं"))}</span></li>')
    rows_html="".join(rows) or "<li>No archived recruitment posts.</li>"
    html="""<!doctype html><html lang="en-IN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Recruitment Archive | Education Update Hub</title><meta name="description" content="Expired government recruitment notifications archived by Education Update Hub."><style>body{font-family:Arial,sans-serif;background:#f5f7fb;margin:0;color:#172033}main{max-width:1000px;margin:30px auto;padding:24px;background:#fff;border-radius:16px}h1{color:#0b4ea2}li{padding:16px 0;border-bottom:1px solid #e6eaf0}a{color:#0757b8;text-decoration:none}span{color:#666}</style></head><body><main><h1>Recruitment Archive</h1><p>Expired application notices are kept here for reference. Only active jobs appear in job categories and on the homepage.</p><ul>"""+rows_html+"""</ul></main></body></html>"""
    PAGE.write_text(html,encoding="utf-8")
