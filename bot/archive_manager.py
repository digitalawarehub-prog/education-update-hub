"""Active-job/Archive lifecycle manager.

Recruitment records stay in the canonical database for history, but once the
application deadline has passed they are removed from every live job feed and
moved to a dedicated archive page. Non-recruitment updates such as results and
admit cards are not archived merely because they have no application deadline.
"""
from pathlib import Path
from datetime import datetime, date
import html
import json
import re

ROOT = Path(__file__).resolve().parent.parent
DB_ARCHIVE = ROOT / "database" / "archive.json"
ARCHIVE_HTML = ROOT / "archive.html"
BASE_URL = "https://educationupdatehub.in"

RECRUITMENT_TYPES = {"recruitment", "job", "jobs", "latest jobs", "latest job"}

MONTHS = {m:i for i,m in enumerate(("jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"),1)}

def parse_date(value):
    s = re.sub(r"\s+", " ", str(value or "").strip())
    if not s: return None
    for fmt in ("%d-%m-%Y","%d/%m/%Y","%d.%m.%Y","%Y-%m-%d","%d %B %Y","%d %b %Y"):
        try: return datetime.strptime(s.replace("/","-") if fmt=="%d-%m-%Y" else s, fmt).date()
        except Exception: pass
    m = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", s)
    if m and m.group(2)[:3].lower() in MONTHS:
        try: return date(int(m.group(3)), MONTHS[m.group(2)[:3].lower()], int(m.group(1)))
        except Exception: pass
    return None

def deadline(job):
    for k in ("last_date","deadline","application_last_date","last_date_to_apply","application_deadline","closing_date"):
        d=parse_date(job.get(k))
        if d: return d
    text=" ".join(str(job.get(k,"") or "") for k in ("title","description","content","notification_text"))
    pats=(
        r"(?:last\s*date(?:\s*to\s*apply)?|application\s*(?:last\s*)?date|deadline|closing\s*date)\s*[:\-–]?\s*(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})",
        r"(?:अंतिम\s*तिथि|अंतिम\s*तारीख|आवेदन\s*की\s*अंतिम\s*तिथि)\s*[:\-–]?\s*(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})",
    )
    for p in pats:
        m=re.search(p,text,re.I)
        if m:
            d=parse_date(m.group(1))
            if d:return d
    return None

def is_recruitment(job):
    return str(job.get("post_type") or job.get("category") or "").strip().casefold() in RECRUITMENT_TYPES

def classify(job):
    if not is_recruitment(job):
        return "active" if str(job.get("status","active")).casefold() != "archived" else "archived"
    d=deadline(job)
    if d and d < date.today(): return "archived"
    if d and d >= date.today(): return "active"
    # Missing deadline is not safe enough for a live Latest Jobs feed.
    return "needs_review"

def reconcile(jobs):
    archive=[]; active=[]; review=[]
    now=datetime.now().isoformat()
    for job in jobs or []:
        status=classify(job)
        job["status"]=status
        d=deadline(job)
        if d: job["application_deadline_iso"]=d.isoformat()
        if status=="archived":
            job.setdefault("archived_at", now)
            archive.append(job)
        elif status=="needs_review":
            review.append(job)
        else:
            active.append(job)
    DB_ARCHIVE.parent.mkdir(parents=True,exist_ok=True)
    DB_ARCHIVE.write_text(json.dumps(archive,ensure_ascii=False,indent=2),encoding="utf8")
    return active, archive, review

def generate_archive_page(archive):
    cards=[]
    for j in sorted(archive,key=lambda x: parse_date(x.get("application_deadline_iso")) or date.min,reverse=True):
        title=html.escape(str(j.get("title", "Government Job") or "Government Job"))
        slug=str(j.get("slug") or "")
        href=f"/generated/posts/{slug}.html" if slug else "#"
        last=html.escape(str(j.get("last_date") or j.get("application_deadline_iso","")[:10] or "Closed"))
        cards.append(f'''<article class="archive-card"><h2><a href="{html.escape(href)}">{title}</a></h2><p>आवेदन की अंतिम तिथि: <strong>{last}</strong></p><a class="read-more" href="{html.escape(href)}">Details →</a></article>''')
    body="\n".join(cards) or '<div class="empty"><h2>अभी कोई archived job नहीं है।</h2></div>'
    ARCHIVE_HTML.write_text(f'''<!doctype html><html lang="hi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Archived Government Jobs | Education Update Hub</title><meta name="description" content="Education Update Hub archived government jobs and recruitment notifications."><style>body{{font-family:Arial,sans-serif;background:#f4f7fb;margin:0;color:#1d2a3a}}main{{max-width:1000px;margin:30px auto;padding:20px}}h1{{color:#123f78}}.archive-card{{background:#fff;padding:18px;margin:14px 0;border-radius:12px;box-shadow:0 2px 12px #0001}}a{{color:#125dcc;text-decoration:none}}.read-more{{display:inline-block;margin-top:8px;padding:9px 14px;background:#1269e8;color:#fff;border-radius:7px}}.empty{{background:#fff;padding:30px;border-radius:12px}}</style></head><body><main><h1>Archived Government Jobs</h1><p>इन भर्तियों की आवेदन अंतिम तिथि समाप्त हो चुकी है। Active Jobs के लिए Latest Jobs देखें।</p>{body}</main></body></html>''',encoding="utf8")

def update(jobs):
    active, archive, review = reconcile(jobs)
    generate_archive_page(archive)
    return active, archive, review
