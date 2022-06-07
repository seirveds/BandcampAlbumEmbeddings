
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
    def __init__(self, db_name="BandcampDB"):
        self.driver = SeleniumDriver()
        self.database = BandcampDB(db_name=db_name, create_new_db=False)

        self.artist_stack = []
        self.album_stack = []
        self.user_stack = []

        self.artists

    def start_scrape(self, artist_url):
        """ """
        self.artist_stack.append(artist_url)
        for url in self.artist_stack:
            artist_page = ArtistPage(url)

            self.album_stack.extend(artist_page.albums)
            for album_url in tqdm(self.album_stack, desc=f"Parsing album data for {url}"):
                album_page = AlbumPage(album_url, selenium_driver=self.driver)

                self.user_stack.extend(album_page.supporters)

        print(len(self.user_stack))

    def quit(self):
        """ Shut down selenium driver and database connection. """
        self.driver.driver.quit()
        self.database.commit_and_close()
