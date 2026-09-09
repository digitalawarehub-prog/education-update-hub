import logging,sys,os
from sources_manager import SourceManager
from scraper import scrape_all_sources
from parser import parse_jobs
from duplicate_checker import filter_new_jobs
from html_generator import generate_all
logging.basicConfig(level=logging.INFO,format="%(asctime)s | %(levelname)s | %(message)s")
logger=logging.getLogger("EUH-Monitor")
def main():
 try:
  logger.info("="*60); logger.info("Education Update Hub AI Auto Publisher"); logger.info("AI posts/run: %s",os.getenv("MAX_AI_POSTS_PER_RUN","5"))
  m=SourceManager(); sources=m.get_html_sources(); logger.info("HTML Sources: %d",len(sources))
  if not sources:return
  links=scrape_all_sources(sources,workers=10); logger.info("Links Found: %d",len(links))
  if not links:return
  parsed=parse_jobs(links); logger.info("Parsed Jobs: %d",len(parsed))
  if not parsed:return
  new=filter_new_jobs(parsed); logger.info("New Jobs: %d",len(new))
  if not new:return
  s=generate_all(new); logger.info("Generated: %d | Failed: %d | Selected: %d",s["success"],s["failed"],s["total"])
 except Exception: logger.exception("Fatal error"); sys.exit(1)
if __name__=="__main__":main()
