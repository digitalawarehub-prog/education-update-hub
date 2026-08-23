# Education Update Hub – Final Automation Fix

Replace the existing `bot/` folder with this folder.

## Main changes
- Loads the complete official source library from `bot/sources.json` instead of silently using only the 7-source fallback config.
- SBI uses the dedicated SBI Careers adapter.
- IBPS is treated as a primary banking/recruitment source, including its Recent Updates and Other Ongoing Recruitments.
- Core sources run every 30 minutes; the wider official source library is staggered to avoid hammering hundreds of sites on every run.
- Exact notification/PDF identity matching is required before recruitment details are extracted.
- A matching PDF is authoritative; page/navigation text cannot override it.
- Old contaminated detail values are cleared during a fresh accepted extraction.
- Better extraction for vacancy totals, Hindi qualification sections, salary/pay ranges, selection process and application deadlines.
- Expired recruitment posts are retained in the database but removed from all live job categories and homepage feeds.
- Expired recruitment posts are automatically written to `database/archive.json` and published on `archive.html`.
- Recruitment records with no verifiable application deadline are not shown as active jobs; they remain `needs_review` rather than being guessed as active.
- Results/admit cards/answer keys/syllabus are not treated as recruitment just because their source text mentions exams/results.
- Search index and homepage use the same active dataset.
- Missing structured fields are shown as `आधिकारिक अधिसूचना देखें` rather than fabricated values.

## Install
1. Delete the old repository `bot/` folder.
2. Upload this `bot/` folder.
3. Do not delete `database/jobs.json`.
4. Run GitHub Actions manually once.
5. The first run intentionally scans the full source library; later runs stagger extended sources automatically.
