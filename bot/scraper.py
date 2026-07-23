import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def scrape_source(source):
    try:
        response = requests.get(
            source["url"],
            headers=HEADERS,
            timeout=20
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        results = []

        # सभी लिंक निकालें
        for link in soup.find_all("a", href=True):
            title = link.get_text(" ", strip=True)

            # बहुत छोटे या खाली टेक्स्ट छोड़ दें
            if len(title) < 10:
                continue

            href = link["href"]

            # Relative URL को Absolute बनाएं
            if href.startswith("/"):
                href = source["url"].rstrip("/") + href

            results.append({
                "source": source["name"],
                "title": title,
                "url": href
            })

        return results

    except Exception as e:
        print(f"{source['name']} Error: {e}")
        return []
