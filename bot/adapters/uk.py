from parser import get_soup, extract_links


class UKAdapter:

    name = "UKPSC"

    def scrape(self, source):

        soup = get_soup(source["url"])

        if not soup:
            return []

        return extract_links(
            soup,
            source["url"]
        )
