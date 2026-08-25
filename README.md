# Education Update Hub — Runtime Safe Fix

## Files to replace

1. `bot/scraper.py`
2. `.github/workflows/auto-publisher.yml`

## What this fixes

- Limits one run to a rotating batch of 80 enabled sources instead of scraping the complete source list every time.
- Keeps priority adapters (IBPS, SSC, UPSC, PSC, UK and Railway) in every run when possible.
- Removes duplicate source URLs before scraping, which prevents repeated calls to the same RRB/domain URL.
- Reduces concurrent workers from 10 to 6.
- Reduces HTTP timeout/retry defaults to 20 seconds / 1 retry.
- Persists rotation state in `database/source_rotation.json`.
- Keeps OCR installed because the existing parser may need it, but prevents OCR-heavy source volume from blocking the whole run by limiting the source batch.
- Adds a 25-minute workflow guard and safer Git synchronization/push retries.

## Environment overrides

`EHU_SOURCE_BATCH_SIZE`, `EHU_SOURCE_WORKERS`, `EHU_REQUEST_TIMEOUT`, and `EHU_MAX_RETRIES` can be changed later without editing Python code.

## Important

This patch intentionally does not change the existing HTML generator, homepage updater, sitemap generator, database schema, source definitions, or language/category logic.
