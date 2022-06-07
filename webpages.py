from math import ceil
from bs4 import BeautifulSoup
import requests

from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from utils import ElementCountChanged


class WebPage:
    def __init__(self, url):
        # Remove leading slashes to make joining relative page urls easier
        if url.endswith("/"):
            url = url[:-1]

        self.url = url
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
        super().__init__(url)
        self.selenium_driver = selenium_driver
        self.supporters = self.get_supporters()
        # TODO meer album metadata tags, pub data, artist

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
                # We dont know how many times we need to click the button, so we just keep trying untill
                # we cant find the button on the page anymore
                a_tag = self.selenium_driver.driver.find_element(By.XPATH, xpath_selector)

                a_tag.click()
                
                # Wait until element is clickable again, with max wait time of 3 seconds. If element could not clicked in
                # 3 seconds WebDriverWait raises a TimeoutException, and the while loop will be broken.
                WebDriverWait(self.selenium_driver.driver, 3).until(EC.element_to_be_clickable((By.XPATH, xpath_selector)))
            except (NoSuchElementException, ElementNotInteractableException, TimeoutException):
                break


class UserPage(WebPage):
    def __init__(self, url, selenium_driver=None):
        super().__init__(url)
        self.selenium_driver = selenium_driver
        self.collection = self.get_collection()


    def get_collection(self):
        """ """
        # Use selenium to press button if it is found on page
        if self.soup.find("button", class_="show-more") is not None:
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
            for _ in range(ceil((collection_size - 20) / 20)):
                # Count amount of albums loaded, we wait until this amount has changed before scrolling down to the bottom
                li_count = len(self.selenium_driver.driver.find_elements(By.XPATH, li_locator))
                WebDriverWait(self.selenium_driver.driver, 3).until(ElementCountChanged((By.XPATH, li_locator), li_count))
                self.selenium_driver.driver.find_element(By.XPATH, '//body').send_keys(Keys.CONTROL+Keys.END)

            assert(len(self.selenium_driver.driver.find_elements(By.XPATH, li_locator)) == collection_size), "Not all albums able to be loaded"

            # Update html and soup attribute with html containing content loaded using selenium
            self.html = self.selenium_driver.driver.page_source.encode("utf-8")
            self.soup = BeautifulSoup(self.html, "lxml")

        # Find ol tag containg all albums and retrieve album urls from a tag hrefs
        album_ol = self.soup.find("ol", class_="collection-grid")
        albums = [a["href"] for a in album_ol.find_all("a", class_="item-link", target="_blank")]

        return albums


class ArtistPage(WebPage):
    def __init__(self, url):
        super().__init__(url)
        self.albums = self.get_albums()

    def get_albums(self):
        """ Returns list of AlbumPage objects, one for every project of an artist. Projects are
        referred to as albums but also include tracks. """
        # Get album urls from li elements in ol tag
        album_ol = self.soup.find("ol", id="music-grid")
        li_elements = album_ol.find_all("li", class_="music-grid-item")
        # Append page url to relative urls that are retrieved from href attribute
        album_urls = [self.url + li.find("a")["href"] for li in li_elements]

        return album_urls
