from parser import get_soup, extract_links


class GenericAdapter:

    name = "Generic"

    def scrape(self, source, session=None):

        soup = get_soup(source["url"])

        if not soup:
            return []

        return extract_links(
            soup,
            source["url"]
        )
