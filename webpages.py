from math import ceil
import re
import requests

from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from tqdm import tqdm

from queries import ALBUM_ID_QUERY, ARTIST_ID_QUERY, USER_ID_QUERY,\
                    INSERT_ALBUM_METADATA_QUERY, INSERT_ALBUM_QUERY, INSERT_ARTIST_QUERY,\
                    INSERT_USER_QUERY, INSERT_USER_SUPPORTS_QUERY
from utils import ElementCountChanged


class WebPage:
    # TODO check super.__init__ calls in subclasses to see if this can be cleaner
    def __init__(self, url, selenium_driver=None):
        # Remove leading slashes to make joining relative page urls easier
        if url.endswith("/"):
            url = url[:-1]

        self.url = url
        self.selenium_driver = selenium_driver
        self.html = self.get_html()
        self.soup = BeautifulSoup(self.html, "lxml")

    def get_html(self):
        """ Use simple get request to retrieve page html and store this as instance variable. """
        response = requests.get(self.url)
        if response.status_code == 200:
            return response.text
        else:
            raise ConnectionError(f"Request returned faulty response: {response.status_code}: {response.content}")


class AlbumPage(WebPage):
    def __init__(self, url, selenium_driver=None):
        super().__init__(url, selenium_driver)
        self.supporters = self.get_supporters()

        # Placeholders for metadata
        self.album_name = None
        self.artist_url = None  # Not written to db, but needed to get artist_id
        self.artist_name = None  # Not written to db, but needed to get artist_id
        self.year = None
        self.tags = None

        # Fill placeholder variables
        self.set_metadata()

    def get_supporters(self):
        # Load content shown by pressing button using selenium
        if self.soup.find("a", class_="more-writing") is not None or self.soup.find("a", class_="more-thumbs") is not None:
            if self.selenium_driver is None:
                raise Exception("Need to use selenium to load content, but no selenium driver was passed.")

            self.selenium_driver.driver.get(self.url)

            self.press_more_buttons("//a[@class='more-writing']")
            self.press_more_buttons("//a[@class='more-thumbs']")

            # Update html and soup attribute with html containing content loaded using selenium
            self.html = self.selenium_driver.driver.page_source.encode("utf-8")
            self.soup = BeautifulSoup(self.html, "lxml")

        supporter_div = self.soup.find("div", class_="deets populated")
        if supporter_div is not None:
            supporter_profiles = [a["href"] for a in supporter_div.find_all("a", class_="pic")]
            return supporter_profiles
        else:
            return []

    def press_more_buttons(self, xpath_selector):
        """ Keeps pressing the specified 'more...' button on the webpage until it doesn't show up anymore. """
        while True:
            try:
                # We dont know how many times we need to click the button, so we just keep trying until
                # we cant find the button on the page anymore
                a_tag = self.selenium_driver.driver.find_element(By.XPATH, xpath_selector)

                a_tag.click()
                
                # Wait until element is clickable again, with max wait time of 5 seconds. If element could not clicked in
                # 5 seconds WebDriverWait raises a TimeoutException, and the while loop will be broken.
                WebDriverWait(self.selenium_driver.driver, 5).until(EC.element_to_be_clickable((By.XPATH, xpath_selector)))
            except (NoSuchElementException, ElementNotInteractableException, TimeoutException):
                break

    def set_metadata(self):
        """ Use beautifulsoup to scrape metadata from html. """
        self.album_name = self.soup.find("h2", class_="trackTitle").text.strip()

        # Needed for getting artist id
        self.artist_url = self.soup.find("div", id="name-section").find("a")["href"]
        self.artist_name = self.soup.find("p", id="band-name-location").find("span", class_="title").text.strip()

        # Year is written in plaintext in a div, we use regex to extract the year from the text
        year_div = self.soup.find("div", class_="tralbumData tralbum-credits").text
        self.year = re.search(r"released[\s\w\d]+,\s([\d]{4})", year_div).group(1)

        tags_div = self.soup.find("div", class_="tralbumData tralbum-tags tralbum-tags-nu")
        tags = sorted([a.text for a in tags_div.find_all("a", class_="tag")])
        # Want a single column for tags, so we use a comma separated string
        self.tags = ', '.join(tags)

    def write_to_database(self, database):
        """ Write album data to database. If album artist does not appear in artist table we write the artist as well.
        This is done because we need an artist id to link the album to the artist. """
        # Check if artist is already in artist table
        artist_id = database.select(ARTIST_ID_QUERY.format(artist_url=self.artist_url))
        # If artist not in table we add it here so we have an artist id we can link to the album
        if not artist_id:
            database.execute(INSERT_ARTIST_QUERY.format(
                artist_name=self.artist_name,
                artist_url=self.artist_url
            ))
            # Retrieve artist id we've just written to database
            artist_id = database.select(ARTIST_ID_QUERY.format(artist_url=self.artist_url))[0]["id"]
        else:
            # Retrieve artist id from json
            artist_id = artist_id[0]["id"]

        # Insert url into album table (if not in table already) to get an album id
        database.execute(INSERT_ALBUM_QUERY.format(
            album_url=self.url
        ))

        # Get id of row written above, we need this to fill metadata table
        album_id = database.select(ALBUM_ID_QUERY.format(
            album_url=self.url
        ))[0]["id"]

        # Use above retrieved album id to write metadata to table
        database.execute(INSERT_ALBUM_METADATA_QUERY.format(
            album_id=album_id,
            album_name=self.album_name,
            artist_id=artist_id,
            year=self.year,
            tags=self.tags
        ))


class ArtistPage(WebPage):
    def __init__(self, url, selenium_driver=None):
        super().__init__(url, selenium_driver)
        self.albums = self.get_albums()
        self.artist_name = self.get_artist_name()

    def get_albums(self):
        """ Returns list of AlbumPage objects, one for every project of an artist. Projects are
        referred to as albums but also include tracks. """
        # Get album urls from li elements in ol tag
        album_ol = self.soup.find("ol", id="music-grid")
        li_elements = album_ol.find_all("li", class_="music-grid-item")
        # Append page url to relative urls that are retrieved from href attribute
        album_urls = [self.url + li.find("a")["href"] for li in li_elements]

        return album_urls

    def get_artist_name(self):
        """ Retrieve artists name from specified tag. """
        return self.soup.find("p", id="band-name-location").find("span", class_="title").text.strip()

    def write_to_database(self, database):
        """ Store self in database. """
        database.execute(f"""
            INSERT OR IGNORE INTO artist (name, url)
            VALUES ('{self.artist_name}', '{self.url}')
        """)


class UserPage(WebPage):
    def __init__(self, url, selenium_driver=None):
        super().__init__(url, selenium_driver)
        # Clean referral part in url
        if self.url.endswith("?from=fanthanks"):
            self.url = self.url.replace("?from=fanthanks", "")

        self.selenium_driver = selenium_driver
        self.collection = self.get_collection()
        self.username = self.get_username()

    def get_collection(self):
        """ """
        import time
        # Use selenium to press button if it is found on page
        if self.soup.find("button", class_="show-more") is not None:
            # TODO check why below line is very slow
            self.selenium_driver.driver.get(self.url)

            # Click show more button, this doesn't show all content, it is loaded dynamically as we scroll down the page, so
            # we simulate this after pressing the button
            button = self.selenium_driver.driver.find_element(By.XPATH, "//button[@class='show-more']")
            button.click()

            # XPATH matching the album li elements
            li_locator = "//li[contains(@id, 'collection-item-container')]"

            # Each scroll loads 20 new albums, use the total collection size to calculate how often we need to scroll
            # to the bottom of the page to load new content
            collection_size = int(self.selenium_driver.driver.find_element(By.XPATH, "//span[@class='count']").text)
            for _ in tqdm(range(ceil((collection_size - 20) / 20)), desc=f"Loading collection for user {self.url}"):
                # Count amount of albums loaded, we wait until this amount has changed before scrolling down to the bottom
                li_count = len(self.selenium_driver.driver.find_elements(By.XPATH, li_locator))
                # TODO handle timeouts
                WebDriverWait(self.selenium_driver.driver, 5).until(ElementCountChanged((By.XPATH, li_locator), li_count))
                self.selenium_driver.driver.find_element(By.XPATH, '//body').send_keys(Keys.CONTROL+Keys.END)

            assert(len(self.selenium_driver.driver.find_elements(By.XPATH, li_locator)) == collection_size), "Not all albums able to be loaded"

            # Update html and soup attribute with html containing content loaded using selenium
            self.html = self.selenium_driver.driver.page_source.encode("utf-8")
            self.soup = BeautifulSoup(self.html, "lxml")

        # Find ol tag containg all albums and retrieve album urls from a tag hrefs
        album_ol = self.soup.find("ol", class_="collection-grid")
        albums = [a["href"] for a in album_ol.find_all("a", class_="item-link", target="_blank")]

        return albums

    def get_username(self):
        return self.soup.find("div", class_="name").find("span").text.strip()

    def write_to_database(self, database):
        """ Stores user data in database. Also makes entry for all supported albums in album table. This does not
        fill the album metadata table, we do this when writing album to table. This is done to prevent expensive operation
        of scraping the album page. """
        # Write user data to database
        database.execute(INSERT_USER_QUERY.format(
            username=self.username,
            user_url=self.url
        ))

        # Retrieve user id used for linking album ids to user
        user_id = database.select(USER_ID_QUERY.format(
            user_url=self.url
        ))[0]["id"]

        # Make entries for all supported albums, we need these to get album ids we store in user_supports table
        for album_url in self.collection:
            # TODO could be done in batch query instead of one by one if this proves to be a bottleneck
            # Fill album entry
            database.execute(INSERT_ALBUM_QUERY.format(
                album_url=album_url
            ))

            # Retrieve album id
            album_id = database.select(ALBUM_ID_QUERY.format(
                album_url=album_url
            ))[0]["id"]

            # Enter user/album id combination in user_supports table
            database.execute(INSERT_USER_SUPPORTS_QUERY.format(
                user_id=user_id,
                album_id=album_id
            ))


if __name__ == "__main__":
    from scraper import SeleniumDriver
    from bandcamp_db import BandcampDB
    database = BandcampDB("BandcampDB.db")
    driver = SeleniumDriver()
    album = AlbumPage("https://fffoxtails.bandcamp.com/album/fawn", selenium_driver=driver)
    album.write_to_database(database=database)
    # user = UserPage("https://bandcamp.com/jmblack", selenium_driver=driver)
