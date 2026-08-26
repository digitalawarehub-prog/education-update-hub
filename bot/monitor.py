"""Authoritative Auto Publisher pipeline."""
from __future__ import annotations
import logging,sys,os
from sources_manager import SourceManager
from scraper import scrape_all_sources
from parser import parse_jobs
from optimizer import run_optimizer
from database import load_jobs,save_jobs
from html_generator import generate_all
import homepage
from sitemap_generator import update_sitemap
from search_index import run as generate_search_index
from url_utils import post_exists

logging.basicConfig(level=logging.INFO,format="%(asctime)s | %(levelname)s | %(message)s")
logger=logging.getLogger("EHU-Monitor")


def main():
    try:
        logger.info("="*70); logger.info("Education Update Hub — Stable Auto Publisher"); logger.info("="*70)
        manager=SourceManager(); all_sources=manager.get_html_sources(); batch=manager.get_run_sources(int(os.getenv("EHU_SOURCE_BATCH_SIZE","40")))
        logger.info("SOURCE REGISTRY | enabled=%d html=%d this_run=%d",manager.count(),len(all_sources),len(batch))
        if not batch:
            logger.warning("No sources selected; preserving current site."); return 0

        scraped,failed=scrape_all_sources(batch,workers=int(os.getenv("EHU_SOURCE_WORKERS","6")))
        logger.info("SCRAPE SUMMARY | links=%d failed=%d",len(scraped),len(failed))
        parsed=parse_jobs(scraped)
        logger.info("PARSE SUMMARY | valid=%d rejected=%d",len(parsed),len(scraped)-len(parsed))

        old=load_jobs()
        result=run_optimizer(old,parsed)
        merged=result.get("jobs",[])
        fresh=result.get("new_jobs",[])
        # Never replace a healthy database with an empty/partial scrape.
        if not merged and old:
            logger.warning("ZERO-JOB SAFETY | scrape produced no usable jobs; preserving database=%d",len(old)); return 0

        # Rebuild the entire public archive from the complete database. This is
        # what prevents categories and homepage from showing only this run's jobs.
        save_jobs(merged)
        summary=generate_all(merged)
        logger.info("HTML SUMMARY | public=%d generated=%d failed=%d",summary.get("total",0),summary.get("success",0),summary.get("failed",0))
        valid=[j for j in merged if post_exists(j)]
        if not valid:
            raise RuntimeError("No generated posts exist after full archive rebuild")
        # Keep the full database even if an individual HTML file fails. A
        # transient generation error must never delete a valid historical job.
        save_jobs(merged)
        homepage.run(valid)
        generate_search_index()
        update_sitemap(valid)
        logger.info("="*70); logger.info("PUBLISH COMPLETE | database=%d fresh=%d posts=%d missing_posts=%d categories=rebuilt homepage=rebuilt",len(merged),len(fresh),len(list((__import__('pathlib').Path('generated/posts')).glob('*.html'))),len(merged)-len(valid)); logger.info("="*70)
        return 0
    except Exception:
        logger.exception("FATAL PUBLISHER ERROR")
        return 1

if __name__=="__main__": sys.exit(main())
