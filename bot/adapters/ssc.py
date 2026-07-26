from parser import get_soup, extract_links


class SSCAdapter:

    name = "SSC"

    def scrape(self, source):

        soup = get_soup(source["url"])

        if not soup:
            return []

        jobs = extract_links(
            soup,
            source["url"]
        )

        return jobs
