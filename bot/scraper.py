import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# Session with Retry
session = requests.Session()

retry = Retry(
    total=2,
    backoff_factor=1,
    status_forcelist=[500,502,503,504]
)

adapter = HTTPAdapter(max_retries=retry)

session.mount("http://", adapter)
session.mount("https://", adapter)


def scrape_source(source):

    jobs = []

    try:

        response = session.get(
            source["url"],
            headers=HEADERS,
            timeout=(5,10)
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        links = soup.find_all("a", href=True)

        for link in links:

            title = link.get_text(
                " ",
                strip=True
            )

            if len(title) < 10:
                continue

            href = link["href"]

            if href.startswith("/"):
                href = source["url"].rstrip("/") + href

            jobs.append({

                "source": source["name"],

                "title": title,

                "url": href

            })

    except Exception as e:

        print(f"{source['name']} -> {e}")

    return jobs


def scrape_all_sources(
        sources,
        workers=10
):

    all_jobs = []

    with ThreadPoolExecutor(
            max_workers=workers
    ) as executor:

        futures = {

            executor.submit(
                scrape_source,
                source
            ): source

            for source in sources

        }

        for future in as_completed(futures):

            try:

                jobs = future.result()

                all_jobs.extend(jobs)

                print(
                    f"Collected {len(jobs)} links"
                )

            except Exception as e:

                print(e)

    return all_jobs
