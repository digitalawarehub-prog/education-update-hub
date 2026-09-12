import logging, os, sys, inspect, json, re
from datetime import datetime, date
from pathlib import Path
from sources_manager import SourceManager
from scraper import scrape_all_sources
from parser import parse_jobs
from optimizer import run_optimizer
from database import load_jobs, save_jobs
from html_generator import generate_all, clean_output_directory
import homepage, category_generator
from sitemap_generator import update_sitemap

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log=logging.getLogger("EUH_FINAL")

TARGET=max(1, int(os.getenv("MAX_AI_POSTS_PER_RUN","5")))
ROOT=Path(__file__).resolve().parent.parent
ARCH=ROOT/"database"/"archive.json"

def norm(x):
    return (x[0] or [], x[1] or []) if isinstance(x,tuple) else (x or [], [])

def scrape_compat(sources):
    p=inspect.signature(scrape_all_sources).parameters
    if "workers" in p: return scrape_all_sources(sources, workers=10)
    if "max_workers" in p: return scrape_all_sources(sources, max_workers=10)
    return scrape_all_sources(sources)

def key(j):
    return str(j.get("job_id") or j.get("url") or j.get("title") or "").strip().casefold()

def unique(items):
    out=[]; seen=set()
    for j in items or []:
        if not isinstance(j,dict): continue
        k=key(j)
        if k and k not in seen:
            seen.add(k); out.append(j)
    return out

MONTHS={"jan":1,"january":1,"feb":2,"february":2,"mar":3,"march":3,"apr":4,"april":4,
        "may":5,"jun":6,"june":6,"jul":7,"july":7,"aug":8,"august":8,"sep":9,"sept":9,
        "september":9,"oct":10,"october":10,"nov":11,"november":11,"dec":12,"december":12}

def pdate(v):
    s=str(v or "").strip()
    for fmt in ("%d-%m-%Y","%d/%m/%Y","%d.%m.%Y","%Y-%m-%d","%d %B %Y","%d %b %Y"):
        try: return datetime.strptime(s,fmt).date()
        except Exception: pass
    m=re.search(r"\b(\d{1,2})\s+([A-Za-z]+)\s+(20\d{2})\b",s)
    if m and m.group(2).lower() in MONTHS:
        try:return date(int(m.group(3)),MONTHS[m.group(2).lower()],int(m.group(1)))
        except Exception: pass
    return None

def deadline(j):
    for k in ("last_date","deadline","application_last_date","last_date_to_apply","closing_date","application_deadline"):
        d=pdate(j.get(k))
        if d:return d
    text=" ".join(str(j.get(k,"") or "") for k in ("title","description","content","notification_text"))
    for pat in (r"(?:last date|closing date|application deadline)[^\d]{0,20}(\d{1,2}[-/.]\d{1,2}[-/.]20\d{2})",
                r"(?:last date|closing date|application deadline)[^\d]{0,20}(\d{1,2}\s+[A-Za-z]+\s+20\d{2})"):
        m=re.search(pat,text,re.I)
        if m:
            d=pdate(m.group(1))
            if d:return d
    return None

def is_expired(j):
    d=deadline(j)
    return bool(d and d < date.today())

def load_arch():
    try:return json.loads(ARCH.read_text(encoding="utf-8")) if ARCH.exists() else []
    except Exception:return []

def save_arch(items):
    ARCH.parent.mkdir(parents=True,exist_ok=True)
    ARCH.write_text(json.dumps(unique(items),ensure_ascii=False,indent=2),encoding="utf-8")

def recruitment_candidate(j):
    title=str(j.get("title","") or "").strip()
    text=(title+" "+str(j.get("description","") or "")+" "+str(j.get("content","") or "")).casefold()
    bad=("qualified candidates","selected candidates","provisional merit","merit list","result","results",
         "answer key","admit card","hall ticket","exam schedule","examination schedule","interview schedule",
         "corrigendum","withdrawn","cancelled","cancellation","extension of date","score card","shortlisted")
    if any(x in text for x in bad): return False
    good=("recruitment","vacancy","vacancies","applications are invited","apply online","online application",
          "application invited","engagement of","appointment of","walk-in","job opportunity","posts of",
          "post of","filling up","invited from eligible")
    return any(x in text for x in good)

def candidate_key(j):
    u=str(j.get("url","") or "").strip().casefold()
    t=re.sub(r"[^a-z0-9]+"," ",str(j.get("title","") or "").casefold()).strip()
    return u or t

def main():
    log.info("Education Update Hub | FINAL 5-POST PUBLISHER")
    sources=SourceManager().get_html_sources()
    raw,failed=norm(scrape_compat(sources))
    parsed=parse_jobs(raw)
    log.info("Links=%d FailedSources=%d Parsed=%d",len(raw),len(failed),len(parsed))

    old=unique(load_jobs())
    archive=unique(load_arch())
    old_keys={candidate_key(j) for j in old+archive}
    # First archive expired live records. Never delete them.
    live=[]
    archived_this=0
    for j in old:
        if is_expired(j):
            j=dict(j); j["status"]="Application Closed"; j["is_expired"]=True
            archive.append(j); archived_this+=1
        else:
            live.append(j)
    archive=unique(archive)

    # Optimizer provides normalized fresh records, but selection is restricted to
    # genuine application/vacancy notices and never result/schedule/list items.
    result=run_optimizer(live,parsed)
    fresh=unique(result.get("new_jobs",[]) if isinstance(result,dict) else [])
    fresh=[j for j in fresh if recruitment_candidate(j) and not is_expired(j)]
    selected=[]; seen=set()
    for j in fresh:
        k=candidate_key(j)
        if not k or k in old_keys or k in seen: continue
        seen.add(k); selected.append(j)
        if len(selected)>=max(TARGET*4,20): break
    log.info("NEW POST SELECTION | ExistingLive=%d | Archived=%d | Candidates=%d | Target=%d",
             len(live),len(archive),len(selected),TARGET)

    from ai_editor import enrich
    made=[]
    for raw_job in selected:
        if len(made)>=TARGET: break
        try:
            j=enrich(dict(raw_job))
            if not j.get("ai_generated"): raise RuntimeError("AI_NOT_CONFIRMED")
            # AI must still represent a genuine recruitment notice.
            if not recruitment_candidate(j): raise RuntimeError("AI_NOT_RECRUITMENT")
            if is_expired(j): raise RuntimeError("AI_POST_ALREADY_EXPIRED")
            j["status"]="Active"; j["is_expired"]=False
            j["site_published_at"]=datetime.now().strftime("%Y-%m-%d")
            made.append(j)
            log.info("AI OK | %d/%d | %s | %s",len(made),TARGET,j.get("title"),j.get("category"))
        except RuntimeError as e:
            log.warning("AI skipped | %s | %s",raw_job.get("title"),e)
        except Exception:
            log.exception("AI failed: %s",raw_job.get("title"))

    if len(made)<TARGET:
        log.error("AI_TARGET_NOT_REACHED | Made=%d Target=%d | No fake/local fallback published",len(made),TARGET)

    # Preserve ALL existing live records plus newly generated posts.
    live=unique(live+made)
    # Re-check expiry after AI generation.
    final_live=[]; newly_archived=0
    for j in live:
        if is_expired(j):
            j=dict(j); j["status"]="Application Closed"; j["is_expired"]=True
            archive.append(j); newly_archived+=1
        else:
            j["status"]="Active"; j["is_expired"]=False
            final_live.append(j)
    archive=unique(archive)
    save_arch(archive)
    save_jobs(final_live)

    clean_output_directory()
    all_public=unique(final_live+archive)
    generate_all(all_public,category_jobs=final_live)
    category_generator.build_categories(final_live)
    homepage.run(final_live)
    from archive_generator import build_archive
    build_archive(archive)
    try:update_sitemap(all_public)
    except TypeError:update_sitemap()

    log.info("DONE | Live=%d Archived=%d NewAI=%d ArchivedThisRun=%d Target=%d",
             len(final_live),len(archive),len(made),archived_this+newly_archived,TARGET)

if __name__=="__main__":
    try: main()
    except Exception:
        log.exception("Fatal Error")
        sys.exit(1)
