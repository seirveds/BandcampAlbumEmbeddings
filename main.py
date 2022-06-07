import os

from bandcamp_db import BandcampDB
from scraper import Scraper


DB_NAME = "BandcampDB"


if not os.path.exists(DB_NAME):
    # Dont need the object, just want to make database with correct tables
    _ = BandcampDB(db_name=DB_NAME, create_new_db=True)


scraper = Scraper(db_name=DB_NAME)

scraper.start_scrape("https://fffoxtails.bandcamp.com/")
scraper.quit()
