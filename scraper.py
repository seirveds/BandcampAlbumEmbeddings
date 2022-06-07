
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from tqdm import tqdm

from bandcamp_db import BandcampDB
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
        # Pages to visit
        self.artist_stack = []
        self.album_stack = []
        self.user_stack = []

        # Load urls of visited pages from database so we can skip them if we see them again
        # Also use sets instead of lists as order doesnt matter, but speed of value in operation does
        self.visited_artists = set([row["url"] for row in self.database.select("SELECT url FROM artist")])
        self.visited_albums = set([row["url"] for row in self.database.select("SELECT url FROM album")])
        self.visited_users = set([row["url"] for row in self.database.select("SELECT url FROM user")])

    def start_scrape(self, artist_url=None):
        """ """
        # if artist_url is None:
        #     # Start from most recently visited artist page
        #     artist_url = self.database.select("SELECT * FROM artist where id = (SELECT MAX(id) FROM artist)")

        self.artist_stack.append(artist_url)
        for url in self.artist_stack:
            artist_page = ArtistPage(url)
            user = UserPage("https://bandcamp.com/jmblack?from=fanthanks", selenium_driver=self.driver)
            user.write_to_database(self.database)

            # self.album_stack.extend(artist_page.albums)
            # for album_url in tqdm(self.album_stack, desc=f"Parsing album data for {url}"):
            #     album_page = AlbumPage(album_url, selenium_driver=self.driver)

            #     self.user_stack.extend(album_page.supporters)
            artist_page.write_to_database(self.database)

        print(len(self.user_stack))

    def quit(self):
        """ Shut down selenium driver and database connection. """
        self.driver.driver.quit()
        self.database.commit_and_close()
