from parser import get_soup, extract_links


class UPSCAdapter:

    name = "UPSC"

    def scrape(self, source):

        soup = get_soup(source["url"])

        if not soup:
            return []

        jobs = extract_links(
            soup,
            source["url"]
        )

        return jobs
