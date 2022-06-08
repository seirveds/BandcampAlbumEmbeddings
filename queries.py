ARTIST_ID_QUERY = "SELECT id FROM artist WHERE url = '{artist_url}'"

ALBUM_ID_QUERY = "SELECT id FROM album WHERE url = '{album_url}'"

USER_ID_QUERY = "SELECT id FROM user WHERE url = '{user_url}'"

CREATE_TABLE_ALBUM = """
CREATE TABLE album (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url varchar(128) NOT NULL UNIQUE
);
"""

CREATE_TABLE_ALBUM_METADATA = """
CREATE TABLE album_metadata (
    id INTEGER PRIMARY KEY,
    artist_id INTEGER NOT NULL,
    name varchar(128) NOT NULL,
    year INTEGER NOT NULL,
    tags varchar(255)
)
"""

CREATE_TABLE_ARTIST = """
CREATE TABLE artist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name varchar(128) NOT NULL,
    url varchar(128) NOT NULL UNIQUE
);
"""

CREATE_TABLE_USER = """
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name varchar(128) NOT NULL,
    url varchar(128) NOT NULL UNIQUE
);
"""

CREATE_TABLE_USER_SUPPORTS = """
CREATE TABLE user_supports (
    user_id INTEGER NOT NULL,
    album_id INTEGER NOT NULL,
    UNIQUE(user_id, album_id)
);
"""

INSERT_ALBUM_QUERY = """
INSERT OR IGNORE INTO album (url)
VALUES ('{album_url}')
"""

INSERT_ALBUM_METADATA_QUERY = """
INSERT OR IGNORE INTO album_metadata (id, artist_id, name, year, tags)
VALUES ('{album_id}', {artist_id}, '{album_name}', {year}, '{tags}')
"""

INSERT_ARTIST_QUERY = """
INSERT OR IGNORE INTO artist (name, url)
VALUES ('{artist_name}', '{artist_url}')
"""

INSERT_USER_QUERY = """
INSERT OR IGNORE INTO user (name, url)
VALUES ('{username}', '{user_url}')
"""

INSERT_USER_SUPPORTS_QUERY = """
INSERT OR IGNORE INTO user_supports (user_id, album_id)
VALUES ({user_id}, {album_id})
"""

VISITED_URLS_QUERY = """
SELECT url FROM artist
UNION
SELECT url FROM album
UNION
SELECT url FROM user
"""
