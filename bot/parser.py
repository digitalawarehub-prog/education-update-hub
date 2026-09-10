"""Final parser/validator for scraped adapter records."""
import re
from urllib.parse import urljoin
from filters import allow_job, classify_post


def clean_title(title):
    text = str(title or "").strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*\|\s*", " ", text)
    return text.strip(" -|:;")


def clean_url(base, href=None):
    if href is None:
        # Backward-compatible call clean_url(url)
        href = base
        base = ""
    href = str(href or "").strip()
    if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
        return None
    return urljoin(str(base or ""), href).split("#", 1)[0].rstrip("/")


def parse_jobs(jobs):
    parsed, seen = [], set()
    for raw in jobs or []:
        if not isinstance(raw, dict):
            continue
        job = dict(raw)
        title = clean_title(job.get("title", ""))
        url = clean_url("", job.get("url", ""))
        if not title or not url:
            continue
        category = classify_post(title, url, job.get("description", ""), job.get("source", ""))
        if not category:
            continue
        key = (title.casefold(), url.casefold())
        if key in seen:
            continue
        seen.add(key)
        job["title"] = title
        job["url"] = url
        job["category"] = category
        job["post_type"] = category
        job["is_valid_post"] = True
        parsed.append(job)
    return parsed


def finalize_jobs(jobs):
    return parse_jobs(jobs)


def parse(soup, base_url):
    results = []
    if soup is None:
        return results
    for a in soup.find_all("a", href=True):
        title = clean_title(a.get_text(" ", strip=True))
        url = clean_url(base_url, a.get("href"))
        if not url or not title or not allow_job(title, url):
            continue
        results.append({"title": title, "url": url})
    return parse_jobs(results)
