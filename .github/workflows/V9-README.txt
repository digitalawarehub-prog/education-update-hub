Education Update Hub V9 – Deep Recruitment Crawler

Replace these exact files in the repository:
.github/workflows/auto-publisher.yml
bot/sources_manager.py
bot/sources.json
bot/adapters/__init__.py
bot/adapters/base.py
bot/adapters/sbi.py
bot/detail_crawler.py
bot/monitor.py

Do NOT delete bot/database/jobs.json.
The runtime now reads bot/sources.json as the canonical source library.
SBI is registered as the SBI adapter.
Recruitment detail enrichment follows listing -> detail/document -> PDF, with identity validation and PDF failure caching.
