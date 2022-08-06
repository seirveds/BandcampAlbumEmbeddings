from datetime import datetime
import re

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options

from queries import INSERT_LOGS_QUERY, TO_VISIT_URLS_QUERY, UPDATE_LOGS_TABLE, VISITED_URLS_QUERY
from utils import CollectionTooLargeException
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


    def start_scrape(self, url=None):
        """ """
        # Fill stack with unvisited urls from log table
        if url is None:
            self.stack = [row["url"] for row in self.database.select(TO_VISIT_URLS_QUERY)]
        # Add passed url to empty stack and start from there
        else:
            self.stack.append(url)

        while self.stack:
            url = self.stack.pop(0)
            print(f"[{datetime.now()}] Scraping {url}")

            if url not in self.visited:
                pagetype = self.get_page_type(url)
                try:
                    page = pagetype(url, selenium_driver=self.driver)

                    # Write page data to database, functionality differs for every page type,
                    # but function call is the same
                    page.write_to_database(self.database)

                    # Depending on page type decide what urls to add to stack
                    if isinstance(page, AlbumPage):
                        add_to_stack = page.supporters
                    elif isinstance(page, ArtistPage):
                        # Should only be reached if the url passed to this function is an album url
                        # Artist data is written to database through AlbumPage.write_to_database()
                        add_to_stack = page.albums
                    elif isinstance(page, UserPage):
                        add_to_stack = page.collection
                    else:
                        raise Exception("Page is not in types (AlbumPage, ArtistPage, UserPage)")

                    # Add scraped urls to stack
                    self.stack.extend(add_to_stack)

                    # Save scraped urls AND current url in logs table
                    self.database.execute(
                        INSERT_LOGS_QUERY.format(
                            urls=self.format_urls_for_insert_log_query([url] + add_to_stack)
                        )
                    )

                    # Set scraped indicator for current url to True
                    self.database.execute(
                        UPDATE_LOGS_TABLE.format(url=url)
                    )

                    # Commit changes to prevent data loss on crash
                    self.database.commit()
                    
                    self.visited.add(url)
                except TimeoutException:
                    print(f"TimeoutException for {url}")
                    self.stack.append(url)
                except CollectionTooLargeException:
                    print(f"Skipped {url}; collection too large")
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

    @staticmethod
    def format_urls_for_insert_log_query(urls):
        """
        Formats list of urls to format needed for insert query, e.g.:
        ['a', 'b', 'c'] > "('a'), ('b'), ('c')"
        """
        return ',\n'.join([f"('{url}')" for url in urls])
