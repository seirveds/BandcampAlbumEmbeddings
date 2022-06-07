ARTIST_ID_QUERY = "SELECT id FROM artist WHERE url = '{artist_url}'"

INSERT_ARTIST_QUERY = """
INSERT OR IGNORE INTO artist (name, url)
VALUES ('{artist_name}', '{artist_url}')
"""

INSERT_ALBUM_QUERY = """
INSERT OR IGNORE INTO artist (url, name, artist_id, year, tag)
VALUES ('{album_url}', '{album_name}', {artist_id}, {year}, '{tags}')
"""

INSERT_USER_QUERY = """

"""
