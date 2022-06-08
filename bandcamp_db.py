import sqlite3

from queries import CREATE_TABLE_ALBUM, CREATE_TABLE_ALBUM_METADATA,\
                    CREATE_TABLE_ARTIST, CREATE_TABLE_USER, CREATE_TABLE_USER_SUPPORTS


class BandcampDB:
    def __init__(self, db_name, create_new_db=False):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()

        if create_new_db:
            self.create_tables()

    def execute(self, query):
        """ Wrapper for executing query. """
        return self.cursor.execute(query)

    def select(self, query):
        """ Returns result of select query as JSON. """
        result = self.execute(query)
        column_names = [tup[0] for tup in result.description]
        return [dict(zip(column_names, row)) for row in result.fetchall()]

    def create_tables(self):
        """ Creates album, artist, user, and user_supports tables. """
        # Initialize album table
        self.execute(CREATE_TABLE_ALBUM)

        # Intialize album metadata table
        self.execute(CREATE_TABLE_ALBUM_METADATA)

        # Initialize artist table
        self.execute(CREATE_TABLE_ARTIST)

        # Initialize user table
        self.execute(CREATE_TABLE_USER)

        # Initialize user_supports table
        self.execute(CREATE_TABLE_USER_SUPPORTS)

    def commit_and_close(self):
        """ Commits all updates to table and closes connection. """
        self.conn.commit()
        self.conn.close()


if __name__ == "__main__":
    import os
    import random
    import string

    from tqdm import tqdm

    def random_string(n):
        return ''.join(random.choice(string.ascii_lowercase) for _ in range(n))

    f = "test.db"
    if os.path.exists(f):
        os.remove(f)

    db = BandcampDB(f, create_new_db=True)

    artist_count = 100
    album_count = 1000
    user_count = 5000

    # Dummy artist data
    for _ in tqdm(range(artist_count), desc="Generating artist data"):
        db.execute(f"INSERT INTO artist ('name', 'url') VALUES ('{random_string(10)}', 'http://{random_string(5)}.bandcamp.com')")

    # Dummy album data
    for _ in tqdm(range(album_count), desc="Generating album data"):
        db.execute(f"""
            INSERT INTO album
            ('name', 'url', 'artist_id', 'year', 'tags')
            VALUES
            ('{random_string(5)}', 'http://{random_string(5)}.bandcamp.com', {random.choice([i for i in range(1, 1 + artist_count)])}, {random.choice([i for i in range(2015, 2023)])}, '{random_string(20)}')
        """)

    # Dummy user data
    for user_id in tqdm(range(user_count), desc="Generating user data"):
        db.execute(f"""
            INSERT INTO user
            ('name', 'url')
            VALUES
            ('{random_string(5)}_{random_string(7)}', 'http://{random_string(5)}.bandcamp.com')
        """)

        # Randomly choose albums user supports
        for supports in range(random.choice([i for i in range(1, 10)])):
            db.execute(f"""
                INSERT INTO user_supports
                ('user_id', 'album_id')
                VALUES
                ({user_id}, {random.choice([i for i in range(1, album_count + 1)])})
            """)

    print(db.select("SELECT * FROM artist where id = (SELECT MAX(id) FROM artist)"))
    
    # print(db.select("SELECT * FROM album")[:5])
    
    # print(db.select("SELECT * FROM user")[:5])
    
    # print(db.select("SELECT * FROM user_supports")[:5])

    db.commit_and_close()
