from parser import get_soup, extract_links


class PSCAdapter:

    name = "PSC"

    def scrape(self, source):

        soup = get_soup(source["url"])

        if not soup:
            return []

        return extract_links(
            soup,
            source["url"]
        )
