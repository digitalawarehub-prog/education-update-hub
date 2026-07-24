from sources_manager import SourceManager
from scraper import scrape_all_sources
from parser import parse_jobs
from duplicate_checker import filter_new_jobs
from html_generator import generate_all
from homepage_updater import update_homepage
from sitemap_generator import update_sitemap

# ===========================
# Source Manager
# ===========================

manager = SourceManager()

print("=" * 50)
print("Education Update Hub Auto Publisher")
print("=" * 50)

print(f"Total Sources : {manager.count()}")

sources = manager.get_html_sources()

print(f"HTML Sources : {len(sources)}")

# ===========================
# Scrape Websites
# ===========================

print("\nChecking Websites...\n")

all_jobs = scrape_all_sources(
    sources,
    workers=10
)

print(f"\nTotal Links Found : {len(all_jobs)}")

# ===========================
# Parse Jobs
# ===========================

parsed_jobs = parse_jobs(all_jobs)

print(f"Total Parsed Jobs : {len(parsed_jobs)}")

# ===========================
# Remove Duplicate Jobs
# ===========================

new_jobs = filter_new_jobs(parsed_jobs)

print(f"New Jobs : {len(new_jobs)}")

for job in new_jobs:
    print("✔", job["title"])

# ===========================
# Generate HTML Files
# ===========================

generated = generate_all(new_jobs)

print(f"\nGenerated Files : {len(generated)}")

for file in generated:
    print(file)

# ===========================
# Update Homepage
# ===========================

update_homepage(new_jobs)

# ===========================
# Update Sitemap
# ===========================

update_sitemap(new_jobs)

print("\n✅ Finished Successfully.")
