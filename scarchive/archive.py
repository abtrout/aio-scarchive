import itertools
import sqlite3

from contextlib import closing

from .track import Track
from .user import User


class Archive(object):

    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.__init_tables()
        self.page_size = 25

    # Add a user to the archive.
    def add_user(self, user):
        with closing(self.conn.cursor()) as c:
            q = "INSERT INTO users (id, username, permalink, avatar_url) VALUES (?, ?, ?, ?)"
            c.execute(q, (user.id, user.username, user.permalink, user.avatar_url))
            self.conn.commit()
            return user.id

    # Add a track to the archive.
    def add_track(self, track):
        with closing(self.conn.cursor()) as c:
            q = "INSERT INTO tracks (id, permalink, user_id, username, title, uri, artwork_url, is_downloadable, is_streamable) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
            c.execute(q, (
                track.id, track.permalink, track.user_id, track.username, track.title, track.uri, track.artwork_url,
                track.is_downloadable, track.is_streamable))
            self.conn.commit()
            return track.id

    # Search for user in archive by user_id.
    def find_user(self, user_id):
        with closing(self.conn.cursor()) as c:
            q = "SELECT id, username, permalink, avatar_url FROM users WHERE id = ?"
            row = c.execute(q, (user_id,)).fetchone()
            return User.from_row(row) if row else None

    # Search for track in archive by track_id.
    def find_track(self, track_id):
        with closing(self.conn.cursor()) as c:
            q = "SELECT id, permalink, user_id, username, title, uri, artwork_url, is_downloadable, is_streamable FROM tracks WHERE id = ?"
            row = c.execute(q, (track_id,)).fetchone()
            return Track.from_row(row) if row else None

    # List all users in archive.
    def list_all_users(self):
        for user in self.__crawl_pages(self.list_users_page):
            yield user

    # List users in archive, one page at a time.
    def list_users_page(self, page=0):
        with closing(self.conn.cursor()) as c:
            q = "SELECT id, username, permalink, avatar_url FROM users ORDER BY id LIMIT ? OFFSET ?"
            params = (self.page_size, self.page_size * page)
            for row in c.execute(q, params).fetchall():
                yield User.from_row(row)

    # List all tracks in archive.
    def list_all_tracks(self):
        for track in self.__crawl_pages(self.list_tracks_page):
            yield track

    # List tracks in archive, one page at a time.
    def list_tracks_page(self, page=0):
        with closing(self.conn.cursor()) as c:
            q = "SELECT id, permalink, user_id, username, title, uri, artwork_url, is_downloadable, is_streamable FROM tracks ORDER BY id LIMIT ? OFFSET ?"
            params = (self.page_size, self.page_size * page)
            for row in c.execute(q, params).fetchall():
                yield Track.from_row(row)

    # List tracks in archive by user_id, one page at a time.
    def list_user_tracks_page(self, user_id, page=0):
        with closing(self.conn.cursor()) as c:
            q = "SELECT id, permalink, user_id, username, title, uri, artwork_url, is_downloadable, is_streamable FROM tracks WHERE user_id = ? ORDER BY id LIMIT ? OFFSET ?"
            params = (user_id, self.page_size, self.page_size * page)
            for row in c.execute(q, params).fetchall():
                yield Track.from_row(row)

    def __crawl_pages(self, page_gen):
        for page in itertools.count():
            count = 0
            for item in page_gen(page):
                yield item
                count += 1
            if count == 0:
                break

    def close(self):
        self.conn.commit()
        self.conn.close()

    # TODO: include create_tables.sql as pkg_resource and replace this again.
    def __init_tables(self):
        with closing(self.conn.cursor()) as c:
            c.execute("""
            create table if not exists users (
              id integer PRIMARY KEY,
              username text,
              permalink text,
              avatar_url text
            );""")
            c.execute("""
            create table if not exists tracks (
              id integer PRIMARY KEY,
              permalink text,
              user_id integer,
              username text,
              title text,
              uri text,
              artwork_url text,
              is_downloadable boolean,
              is_streamable boolean,
              FOREIGN KEY(user_id) REFERENCES users(id)
            );""")
