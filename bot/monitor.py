import logging,os,sys,inspect
from sources_manager import SourceManager
from scraper import scrape_all_sources,enrich_job
from parser import parse_jobs
from optimizer import run_optimizer
from database import load_jobs,save_jobs
from html_generator import generate_all,filter_active_jobs,clean_output_directory
import homepage,category_generator
from sitemap_generator import update_sitemap

logging.basicConfig(level=logging.INFO,format="%(asctime)s | %(levelname)s | %(message)s")
log=logging.getLogger("EUH_FAST")
MAX_AI_POSTS=int(os.getenv("MAX_AI_POSTS_PER_RUN","5"))

def norm(x): return (x[0] or [],x[1] or []) if isinstance(x,tuple) else (x or [],[])
def scrape_compat(sources):
    p=inspect.signature(scrape_all_sources).parameters
    if "workers" in p:return scrape_all_sources(sources,workers=10)
    if "max_workers" in p:return scrape_all_sources(sources,max_workers=10)
    return scrape_all_sources(sources)
def uniq(jobs):
    out=[];seen=set()
    for j in jobs or []:
        k=str(j.get("job_id") or j.get("url") or j.get("title") or "").strip().casefold()
        if k and k not in seen:seen.add(k);out.append(j)
    return out

def main():
    try:
        log.info("Education Update Hub | CLEAN AI PUBLISHER")
        sources=SourceManager().get_html_sources()
        raw,failed=norm(scrape_compat(sources))
        log.info("Links Found=%d | Failed Sources=%d",len(raw),len(failed))
        parsed=parse_jobs(raw)
        if not parsed: log.warning("No parsed jobs. Existing site unchanged."); return
        old=load_jobs(); result=run_optimizer(old,parsed)
        new=result.get("new_jobs",[]) if isinstance(result,dict) else []
        log.info("Existing=%d | New=%d",len(old),len(new))
        if not new: log.info("No new jobs. Existing site unchanged."); return
        from ai_editor import enrich
        processed=[]
        for raw_job in new[:MAX_AI_POSTS]:
            try:
                j=dict(raw_job)
                try:j=enrich_job(j)
                except Exception:log.exception("Source enrichment failed: %s",j.get("title"))
                j=enrich(j)
                if str(j.get("apply_link") or "").strip()==str(j.get("notification_pdf") or "").strip():j["apply_link"]=""
                processed.append(j)
                log.info("AI OK | %s | type=%s | category=%s",j.get("title",""),j.get("post_type",""),j.get("category",""))
            except RuntimeError as e:
                if str(e)=="OPENROUTER_RATE_LIMIT": log.error("OpenRouter 429 -> STOP AI"); break
                log.exception("AI failed")
            except Exception: log.exception("AI failed")
        processed=uniq(processed)
        if not processed: log.warning("No successful AI posts. Existing site unchanged."); return

        # CLEAN SLATE: only successful new AI posts remain live.
        save_jobs(processed)
        clean_output_directory()
        summary=generate_all(processed,category_jobs=processed)
        log.info("Generated=%s Failed=%s",summary.get("success",0) if isinstance(summary,dict) else "?",summary.get("failed",0) if isinstance(summary,dict) else "?")
        category_generator.build_categories(processed)  # clears empty category pages too
        active=filter_active_jobs(processed)
        homepage.run(active)
        try:update_sitemap(active)
        except TypeError:update_sitemap()
        log.info("DONE | Live AI posts=%d | Old posts deleted",len(processed))
    except Exception:
        log.exception("Fatal Error");sys.exit(1)
if __name__=="__main__":main()
