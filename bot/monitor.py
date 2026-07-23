from config import SOURCES
from scraper import scrape_source

all_jobs = []

for source in SOURCES:
    print(f"Checking {source['name']}...")
    jobs = scrape_source(source)
    all_jobs.extend(jobs)

print(f"\nTotal Links Found: {len(all_jobs)}")

for job in all_jobs[:20]:
    print(job["title"])
