import logging, os, sys, json, hashlib
from pathlib import Path
from sources_manager import SourceManager
from scraper import scrape_all_sources
from parser import parse_jobs
from duplicate_checker import filter_new_jobs
from ai_editor import enrich, classify_category, MAX_AI_POSTS_PER_RUN
from html_generator import write_post, build_files

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log=logging.getLogger("EUH")

STATE=Path(__file__).resolve().parent.parent/"generated"/"processed_ai.json"
STATE.parent.mkdir(parents=True,exist_ok=True)

def key(job):
    raw="|".join(str(job.get(k,"")).strip().lower() for k in
                 ("url","source_url","link","title","job_id"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def load_state():
    try: return set(json.loads(STATE.read_text(encoding="utf-8")))
    except Exception: return set()

def save_state(s):
    STATE.write_text(json.dumps(sorted(s),ensure_ascii=False,indent=2),encoding="utf-8")

def main():
    log.info("="*70)
    log.info("EUH AI Auto Publisher | NEW POSTS ONLY")
    log.info("AI limit per run: %s", MAX_AI_POSTS_PER_RUN)

    manager=SourceManager()
    sources=manager.get_html_sources()
    log.info("Sources: %d",len(sources))
    if not sources: return

    found=scrape_all_sources(sources,workers=10)
    log.info("Links Found: %d",len(found))
    parsed=parse_jobs(found)
    log.info("Parsed Jobs: %d",len(parsed))
    if not parsed: return

    # Existing duplicate filter first.
    try: candidates=filter_new_jobs(parsed)
    except Exception:
        log.exception("duplicate_checker failed; using local state")
        candidates=parsed

    state=load_state()
    new=[]
    for j in candidates:
        k=key(j)
        if k not in state:
            new.append(j)

    # Never send hundreds of records to AI.
    selected=new[:MAX_AI_POSTS_PER_RUN]
    skipped=max(0,len(new)-len(selected))
    log.info("New candidates: %d | Selected for AI: %d | Deferred: %d",
             len(new),len(selected),skipped)

    generated=[]
    for j in selected:
        try:
            ai=enrich(j)  # raises immediately on OpenRouter 429
            merged=dict(j); merged.update(ai)
            write_post(merged)
            generated.append(merged)
            state.add(key(j))
            log.info("AI OK | %s | category=%s",merged.get("title",""),merged.get("category"))
        except RuntimeError as e:
            if str(e)=="OPENROUTER_RATE_LIMIT":
                log.error("OpenRouter 429: STOPPING AI FOR THIS RUN")
                break
            log.exception("AI runtime error")
        except Exception:
            log.exception("Post generation failed")

    save_state(state)

    # Homepage/category pages are generated only from the posts produced in this run.
    # Existing pages are not mass-regenerated from hundreds of old records.
    if generated:
        build_files(generated)

    log.info("AI Success=%d | Failed=%d | Deferred=%d",
             len(generated), max(0,len(selected)-len(generated)), skipped)
    log.info("Completed")

if __name__=="__main__":
    try: main()
    except Exception:
        log.exception("Fatal error")
        sys.exit(1)
