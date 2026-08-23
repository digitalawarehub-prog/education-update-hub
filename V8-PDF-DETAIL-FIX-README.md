# Education Update Hub – V8 PDF/Detail Extraction Fix

## Replace
1. Replace the existing `bot/` folder with the `bot/` folder in this package.
2. Replace `.github/workflows/auto-publisher.yml` with the included workflow.
3. Keep `database/jobs.json` and the existing website HTML files.
4. `bot/sources.json` is the canonical source file used by the automation. The root `sources.json` can remain; it is not the runtime source library.

## What this version fixes
- Follows the recruitment detail page before extracting notification data.
- Checks multiple PDF candidates instead of trusting the first PDF link.
- Rejects unrelated/sample/old PDFs using advertisement number, organisation, role and recruitment-cycle identity checks.
- Prevents one recruitment's PDF from contaminating another recruitment's table.
- Clears stale notification PDF values when the document fails identity validation.
- Adds PDF extraction caching so the same PDF is not downloaded repeatedly during legacy repair.
- Limits legacy detail repair to 35 records per run and prioritises active/unknown-deadline records, preventing GitHub Actions timeouts.
- Improves qualification and selection-process extraction so navigation/website text is not accepted as a recruitment field.
- Treats very short/invalid salary values such as `Rs`, `Rs1`, `₹50` as invalid and rechecks them.
- Allows direct recruitment PDFs from official source pages to become recruitment records instead of silently skipping them.
- Uses the current SBI Careers openings URL and official SBI Junior Associates PDF fallback, with identity validation before use.
- Adds workflow timeout protection.

## Important
Do not delete `database/jobs.json` before the first run. The new repair stage uses the existing database to progressively correct old posts.

After uploading the files, run **Actions → auto-publisher → Run workflow** once manually.
