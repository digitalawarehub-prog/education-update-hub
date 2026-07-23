from parser import parse_jobs
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
parsed_jobs = parse_jobs(all_jobs)

print(f"Total Parsed Jobs: {len(parsed_jobs)}")

for job in parsed_jobs[:20]:
    print(job)
