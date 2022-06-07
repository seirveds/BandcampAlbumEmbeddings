import os

from bandcamp_db import BandcampDB
from scraper import Scraper


DB_NAME = "BandcampDB.db"


if not os.path.exists(DB_NAME):
    # Dont need the object, just want to make database with correct tables
    _ = BandcampDB(db_name=DB_NAME, create_new_db=True)

database = BandcampDB(db_name=DB_NAME)
scraper = Scraper(database=database)

scraper.start_scrape("https://fffoxtails.bandcamp.com/album/fawn")
print(database.select("SELECT * FROM artist"))
print(database.select("SELECT * FROM user"))
print(database.select("SELECT * FROM album"))
scraper.quit()
