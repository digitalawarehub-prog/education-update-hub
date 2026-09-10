import logging, os, sys, inspect
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
log = logging.getLogger("EUH_FAST")

MAX_AI_POSTS = int(os.getenv("MAX_AI_POSTS_PER_RUN", "5"))

def norm(x):
    return (x[0] or [], x[1] or []) if isinstance(x, tuple) else (x or [], [])

def key(j):
    return str(j.get("job_id") or j.get("url") or j.get("title") or "").strip()

def scrape_compat(sources):
    """
    Call the scraper using whatever signature the installed scraper.py supports.
    This fixes the failure seen in the GitHub Actions log:
    scrape_all_sources() got an unexpected keyword argument 'workers'
    """
    try:
        sig = inspect.signature(scrape_all_sources)
        params = sig.parameters

        if "workers" in params:
            log.info("Scraper API: using workers=%d", 10)
            return scrape_all_sources(sources, workers=10)

        if "max_workers" in params:
            log.info("Scraper API: using max_workers=%d", 10)
            return scrape_all_sources(sources, max_workers=10)

        # Older/simple scraper API: only sources is accepted.
        log.info("Scraper API: workers argument not supported; using scrape_all_sources(sources)")
        return scrape_all_sources(sources)

    except (TypeError, ValueError):
        # Last-resort compatibility fallback.
        log.warning("Scraper signature could not be inspected; retrying with sources only.")
        return scrape_all_sources(sources)

def main():
    try:
        log.info("Education Update Hub | FAST PUBLISHER")
        manager = SourceManager()
        sources = manager.get_html_sources()
        log.info("HTML Sources: %d", len(sources))

        if not sources:
            log.warning("No HTML sources found.")
            return

        raw, failed = norm(scrape_compat(sources))
        log.info("Links Found: %d | Failed Sources: %d", len(raw), len(failed))

        if not raw:
            log.warning("No links found. Keeping current website/database unchanged.")
            return

        parsed = parse_jobs(raw)
        log.info("Parsed Jobs: %d", len(parsed))

        if not parsed:
            log.warning("No parsed jobs. Keeping current website/database unchanged.")
            return

        old = load_jobs()
        result = run_optimizer(old, parsed)
        new = result.get("new_jobs", []) if isinstance(result, dict) else []
        log.info("Existing DB: %d | New Jobs: %d", len(old), len(new))

        if not new:
            try:
                homepage.run(filter_active_jobs(old))
            except Exception:
                log.exception("Homepage refresh failed")
            return

        selected = new[:MAX_AI_POSTS]
        log.info(
            "AI Selected: %d | Deferred: %d",
            len(selected),
            max(0, len(new) - len(selected)),
        )

        from ai_editor import enrich

        processed = []
        for job in selected:
            try:
                item = dict(job)
                ai = enrich(job)
                if isinstance(ai, dict):
                    item.update(ai)
                processed.append(item)
                log.info("AI OK: %s", item.get("title", ""))

            except RuntimeError as e:
                if str(e) == "OPENROUTER_RATE_LIMIT":
                    log.error("OpenRouter 429 -> STOP AI NOW")
                    break
                log.exception("AI error")

            except Exception:
                log.exception("AI error")

        if not processed:
            log.warning("No AI posts generated. Existing website/database left unchanged.")
            return

        # CLEAN MODE:
        # Old auto-generated posts are removed from the live database.
        final = []
        seen = set()

        for job in processed:
            k = key(job)
            if k and k not in seen:
                seen.add(k)
                final.append(job)

        save_jobs(final)
        log.info("CLEAN MODE | Old posts removed | Live database: %d", len(final))

        try:
            from html_generator import clean_output_directory
            clean_output_directory()
            log.info("Old generated HTML removed.")
        except Exception:
            log.exception("Could not clean generated HTML")

        summary = generate_all(final, category_jobs=final)
        log.info(
            "HTML generated: %s",
            summary.get("success", 0) if isinstance(summary, dict) else summary,
        )

        active = filter_active_jobs(final)

        try:
            category_generator.build_categories(active)
        except Exception:
            log.exception("Category update failed")

        try:
            homepage.run(active)
        except Exception:
            log.exception("Homepage update failed")

        try:
            update_sitemap(active)
        except TypeError:
            update_sitemap()

        log.info(
            "DONE | Old posts removed | New live AI posts=%d | Deferred=%d",
            len(processed),
            max(0, len(new) - len(processed)),
        )

    except Exception:
        log.exception("Fatal Error")
        sys.exit(1)

if __name__ == "__main__":
    main()
