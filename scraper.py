import re

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options

from queries import VISITED_URLS_QUERY
from webpages import AlbumPage, ArtistPage, UserPage


class SeleniumDriver:
    def __init__(self, path_to_driver="chromedriver.exe"):
        self.path_to_driver = path_to_driver
        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_experimental_option("excludeSwitches", ["enable-logging"])

        self.driver = webdriver.Chrome(executable_path=self.path_to_driver, options=self.options)


class Scraper:
    def __init__(self, database):
        self.driver = SeleniumDriver()
        self.database = database

        # Urls to visit
        self.stack = []

        # Load urls of visited pages from database so we can skip them if we see them again
        # Also use sets instead of lists as order doesnt matter, but speed of value in operation does
        visited_urls = [row["url"] for row in self.database.select(VISITED_URLS_QUERY)]
        self.visited = set(visited_urls)
        self.last_visited = visited_urls[-1] if visited_urls else None


    def start_scrape(self, url=None):
        """ """
        if url is None:
            # TODO doesnt work, save stack on exit and take first from there
            url = self.last_visited

        self.stack.append(url)

        while self.stack:
            url = self.stack.pop(0)
            print(f"Scraping {url}")

            if url not in self.visited:
                pagetype = self.get_page_type(url)
                try:
                    page = pagetype(url, selenium_driver=self.driver)

                    # Write page data to database, functionality differs for every page type,
                    # but function call is the same
                    page.write_to_database(self.database)

                    # Depending on page type decide what urls to add to stack
                    if isinstance(page, AlbumPage):
                        self.stack.extend(page.supporters)
                    elif isinstance(page, ArtistPage):
                        # Should only be reached if the url passed to this function is an album url
                        # Artist data is written to database through AlbumPage.write_to_database()
                        self.stack.extend(page.albums)
                    elif isinstance(page, UserPage):
                        self.stack.extend(page.collection)
                    else:
                        raise Exception("Page is not in types (AlbumPage, ArtistPage, UserPage)")

                    self.visited.add(url)
                except TimeoutException:
                    print(f"TimeoutException for {url}")
                    self.stack.append(url)
            else:
                print(f"Already visited {url}, skipping")

    def quit(self):
        """ Shut down selenium driver and database connection. """
        self.driver.driver.quit()
        self.database.commit_and_close()

    @staticmethod
    def get_page_type(url):
        """ Transforms an url to its corresponsing WebPage subclass. """
        # Format is not always artist.bandcamp.com, so we have to match
        # a very broad regex
        album_page_pattern = r"https://[\w\d\-.]+/[\w]+/[\w\d-]+$"
        artist_page_pattern = r"https://[\w\d\-.]+[/]?$"
        user_page_pattern = r"https://bandcamp.com/[\w\d-]+(\?from=fanthanks)?$"

        if re.match(album_page_pattern, url):
            return AlbumPage
        elif re.match(artist_page_pattern, url):
            return ArtistPage
        elif re.match(user_page_pattern, url):
            return UserPage
        else:
            raise Exception(f"Could not match url {url} to any regex pattern.")
