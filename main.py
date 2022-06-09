import os

from bandcamp_db import BandcampDB
from scraper import Scraper


DB_NAME = "BandcampDB.db"


if not os.path.exists(DB_NAME):
    # Dont need the object, just want to make database with correct tables
    print(f"Making new database '{DB_NAME}'")
    _ = BandcampDB(db_name=DB_NAME, create_new_db=True)

database = BandcampDB(db_name=DB_NAME)
scraper = Scraper(database=database)

# Fails on https://bandcamp.com/Nicolegaffneyo?from=fanthanks
scraper.start_scrape("https://bandcamp.com/Nicolegaffneyo?from=fanthanks")
print(len(database.select("SELECT * FROM artist")))
print(len(database.select("SELECT * FROM user")))
print(len(database.select("SELECT * FROM album")))
print(len(database.select("SELECT * FROM album_metadata")))
scraper.quit()
