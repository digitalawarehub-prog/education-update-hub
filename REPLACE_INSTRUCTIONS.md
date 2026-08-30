# Education Update Hub – Final Replacement Pack V7

Copy the files to these exact repository paths:

- bot/homepage.py
- bot/homepage_updater.py
- bot/category_generator.py
- bot/html_generator.py
- bot/parser.py
- bot/scraper.py
- bot/optimizer.py
- bot/monitor.py
- style.css
- .github/workflows/auto-publisher.yml

Do NOT delete database/jobs.json.

Fixes included:
- Canonical generated-post links + existence checks to stop homepage/category 404s.
- Type-specific buttons for Result, Syllabus, Admit Card, Answer Key, Exam and other post types, including PDF-source posts.
- Category-page buttons are type-specific instead of all having the same label.
- Removes trailing “हेतु क्लिक करें / के लिए क्लिक करें / Click Here” from titles.
- Cleans concatenated “Download Result … Download Result …” titles.
- Cleans legacy database titles automatically on the next Auto Publisher run.
- Keeps Government Scheme category isolated from Recruitment.
- Uses the rotating 80-source batch; the supplied log showed the previous run was cancelled while scraping all 284 sources, before generation completed.
- Workflow timeouts/retries are tightened to reduce long runs from unavailable sources.
