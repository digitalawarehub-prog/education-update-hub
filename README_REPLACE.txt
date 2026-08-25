Education Update Hub - Stable Final Replacement v27

REPLACE THESE FILES:
  bot/monitor.py
  bot/html_generator.py
  bot/homepage.py
  bot/category_generator.py
  bot/url_utils.py
  bot/optimizer.py
  bot/filters.py
  bot/parser.py
  bot/homepage_updater.py
  bot/adapters/base.py

DO NOT replace sources.json, config.py, scraper.py, database.py or the website HTML files.
Those remain the current repository versions.

WHY THIS VERSION:
1. Full database (not only New Jobs) is used for HTML/category/homepage reconciliation.
2. Canonical slug/URL generation is shared by post, category and homepage links.
3. Generated post existence is validated before links are published.
4. Latest Updates / Latest Posts are title-only; no image/card/Read More is inserted there.
5. Category archive pages retain valid historical posts; Latest Jobs remains current/deadline based.
6. Generic navigation items such as Click Here For Details are rejected.
7. PDF details are accepted only after PDF-vs-title identity validation.
8. Recruitment fields are not copied into Result/Admit Card/Answer Key posts.
9. Legacy missing/garbled recruitment details are repaired before regeneration.
10. Duplicate logging from legacy module handlers is suppressed.

IMPORTANT:
- Extract the zip in the repository root and overwrite ONLY the files listed above.
- Run: python bot/tests_ehu_final.py
- Then run the GitHub Action manually once.
- The first stable run intentionally reconciles the complete database so old 404 links are repaired.
