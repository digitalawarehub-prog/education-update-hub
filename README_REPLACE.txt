EHU SARKARI-RESULT STYLE STABLE V30

Replace exactly these files:
1. bot/html_generator.py
2. bot/category_generator.py
3. bot/homepage.py
4. bot/url_utils.py
5. bot/monitor.py
6. bot/filters.py
7. bot/adapters/base.py
8. .github/workflows/auto-publisher.yml

DO NOT replace/delete:
- database/jobs.json
- generated/posts/
- existing root category HTML files manually
- images/

Fixes included:
- Shortlisted/marks/selection-list notices are classified as Result/Update, not Recruitment.
- Recruitment pages show distinct Apply Online / Official Notification / Official Website buttons only when those URLs exist.
- Result, Admit Card, Answer Key and Syllabus pages use their own action labels.
- English notification remains English; Hindi remains Hindi; regional language remains unchanged. No source-content translation.
- Removes literal \\n/\\r/\\t artifacts from generated details.
- Recruitment tables show only real extracted values; missing data is not fabricated.
- Category pages use compact title-first rows and one View Details button.
- Stale html_file values cannot create 404 links.
- Category sorting no longer invents today's date.
- Result/shortlisted/marks notices route to Result category even when their source category says Teaching/Recruitment.
- Latest Updates remains title-only on the homepage.

After replacing, run the workflow once. The generator rebuilds posts/categories from the persistent database; do not delete database/jobs.json.
