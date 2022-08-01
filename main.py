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

# scraper.start_scrape("https://fffoxtails.bandcamp.com/")
scraper.start_scrape()

print(f"Total artists: {len(database.select('SELECT * FROM artist')):,}")
print(f"Total users: {len(database.select('SELECT * FROM user')):,}")
print(f"Total albums: {len(database.select('SELECT * FROM album')):,}")
print(f"Total user-artist links: {len(database.select('SELECT * FROM user_supports')):,}")
scraper.quit()
