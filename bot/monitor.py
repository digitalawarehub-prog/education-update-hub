from duplicate_checker import filter_new_jobs
parsed_jobs = parse_jobs(all_jobs)

new_jobs = filter_new_jobs(parsed_jobs)

print(f"New Jobs : {len(new_jobs)}")

for job in new_jobs:

    print(job["title"])
from source_manager import SourceManager
from scraper import scrape_all_sources
from parser import parse_jobs

# Source Manager
manager = SourceManager()

print("=" * 50)
print("Education Update Hub Auto Publisher")
print("=" * 50)

print(f"Total Sources : {manager.count()}")

# HTML Sources
sources = manager.get_html_sources()

print(f"HTML Sources  : {len(sources)}")

# Parallel Scraping
print("\nChecking Websites...\n")

all_jobs = scrape_all_sources(
    sources,
    workers=10
)

print(f"\nTotal Links Found : {len(all_jobs)}")

# Parse Jobs
parsed_jobs = parse_jobs(all_jobs)

print(f"Total Parsed Jobs : {len(parsed_jobs)}")

print("\nTop 20 Results\n")

for job in parsed_jobs[:20]:
    print("-" * 40)
    print("Source   :", job["source"])
    print("Category :", job["category"])
    print("Title    :", job["title"])
    print("URL      :", job["url"])

print("\nFinished Successfully.")
