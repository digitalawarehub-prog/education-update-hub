import logging, sys
from sources_manager import SourceManager
from scraper import scrape_all_sources
from parser import parse_jobs
from optimizer import run_optimizer
from database import load_jobs, save_jobs
from html_generator import generate_all, filter_active_jobs
import homepage
from sitemap_generator import update_sitemap
import category_generator

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log=logging.getLogger("EUH_FAST")
MAX_AI_POSTS=5

def norm(x):
    return (x[0] or [], x[1] or []) if isinstance(x,tuple) else (x or [],[])

def key(j):
    return str(j.get("job_id") or j.get("url") or j.get("title") or "").strip()

def main():
    try:
        log.info("Education Update Hub | FAST PUBLISHER")
        manager=SourceManager()
        sources=manager.get_html_sources()
        log.info("HTML Sources: %d",len(sources))
        if not sources: return

        # IMPORTANT: do NOT call scraper.enrich_jobs() here.
        # The existing scraper's enrich_jobs() opens every detail page/PDF.
        raw,failed=norm(scrape_all_sources(sources,workers=10))
        log.info("Links Found: %d | Failed Sources: %d",len(raw),len(failed))
        if not raw: return

        parsed=parse_jobs(raw)
        log.info("Parsed Jobs: %d",len(parsed))
        if not parsed: return

        old=load_jobs()
        result=run_optimizer(old,parsed)
        new=result.get("new_jobs",[])
        log.info("Existing DB: %d | New Jobs: %d",len(old),len(new))

        if not new:
            try: homepage.run(filter_active_jobs(old))
            except Exception: log.exception("Homepage refresh failed")
            return

        selected=new[:MAX_AI_POSTS]
        log.info("AI Selected: %d | Deferred: %d",len(selected),max(0,len(new)-len(selected)))

        from ai_editor import enrich
        processed=[]
        for job in selected:
            try:
                item=dict(job)
                ai=enrich(job)
                if isinstance(ai,dict): item.update(ai)
                processed.append(item)
                log.info("AI OK: %s",item.get("title",""))
            except RuntimeError as e:
                if str(e)=="OPENROUTER_RATE_LIMIT":
                    log.error("OpenRouter 429 -> STOP AI NOW")
                    break
                log.exception("AI error")
            except Exception:
                log.exception("AI error")

        if not processed:
            log.info("No AI posts generated.")
            return

        # CLEAN MODE:
        # Do not keep the old auto-generated database records. If an old post
        # is not being repaired, it must not remain in the live website.
        # The live database is rebuilt from successfully processed posts only.
        final=[]
        seen=set()
        for j in processed:
            k=key(j)
            if k and k not in seen:
                seen.add(k)
                final.append(j)

        save_jobs(final)
        log.info("CLEAN MODE | Old posts removed | Live database: %d",len(final))

        # Remove stale generated HTML before publishing the clean set.
        try:
            from html_generator import clean_output_directory
            clean_output_directory()
            log.info("Old generated HTML removed.")
        except Exception:
            log.exception("Could not clean generated HTML")

        summary=generate_all(final,category_jobs=final)
        log.info("HTML generated: %s",summary.get("success",0) if isinstance(summary,dict) else summary)

        active=filter_active_jobs(final)
        try: category_generator.build_categories(active)
        except Exception: log.exception("Category update failed")
        try: homepage.run(active)
        except Exception: log.exception("Homepage update failed")
        try: update_sitemap(active)
        except TypeError: update_sitemap()
        log.info("DONE | Old posts removed | New live AI posts=%d | Deferred=%d",len(processed),max(0,len(new)-len(processed)))
    except Exception:
        log.exception("Fatal Error")
        sys.exit(1)

if __name__=="__main__":
    main()
