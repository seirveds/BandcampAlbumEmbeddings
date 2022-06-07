import sqlite3


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

    def create_tables(self):
        """ Creates album, artist, user, and user_supports tables. """
        # Initialize album table
        self.execute("""
            CREATE TABLE album (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name varchar(128) NOT NULL,
                artist_id INTEGER NOT NULL,
                year INTEGER NOT NULL,
                tags varchar(255)
            );
        """)

        # Initialize artist table
        self.execute("""
            CREATE TABLE artist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name varchar(128) NOT NULL
            )
        """)

        # Initialize user table
        self.execute("""
            CREATE TABLE user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name varchar(128) NOT NULL
            )
        """)

        # Initialize user_supports table
        self.execute("""
            CREATE TABLE user_supports (
                user_id INTEGER NOT NULL,
                album_id INTEGER NOT NULL
            )
        """)

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

    artist_count = 1000
    album_count = 100000
    user_count = 50000

    # Dummy artist data
    for _ in tqdm(range(artist_count), desc="Generating artist data"):
        db.execute(f"INSERT INTO artist ('name') VALUES ('{random_string(10)}')")

    # Dummy album data
    for _ in tqdm(range(album_count), desc="Generating album data"):
        db.execute(f"""
            INSERT INTO album
            ('name', 'artist_id', 'year', 'tags')
            VALUES
            ('{random_string(5)}', {random.choice([i for i in range(1, 1 + artist_count)])}, {random.choice([i for i in range(2015, 2023)])}, '{random_string(20)}')
        """)

    # Dummy user data
    for user_id in tqdm(range(user_count), desc="Generating user data"):
        db.execute(f"""
            INSERT INTO user
            ('name')
            VALUES
            ('{random_string(5)}_{random_string(7)}')
        """)

        # Randomly choose albums user supports
        for supports in range(random.choice([i for i in range(1, 10)])):
            db.execute(f"""
                INSERT INTO user_supports
                ('user_id', 'album_id')
                VALUES
                ({user_id}, {random.choice([i for i in range(1, album_count + 1)])})
            """)

    # for row in db.execute("SELECT * FROM artist"):
    #     print(row)
    #
    # for row in db.execute("SELECT * FROM album"):
    #     print(row)
    #
    # for row in db.execute("SELECT * FROM user"):
    #     print(row)
    #
    # for row in db.execute("SELECT * FROM user_supports"):
    #     print(row)

    db.commit_and_close()
