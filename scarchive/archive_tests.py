import json
import unittest

from contextlib import closing

from .archive import Archive
from .track import Track
from .user import User


class ArchiveTests(unittest.TestCase):

    def setUp(self):
        self.testArchive = lambda: Archive(db_file=":memory:")

        # Basic CRUD tests for the users table.

    def test_users_crud(self):
        user_json = json.loads(
            """{"website": "https://j-hok.bandcamp.com/", "myspace_name": null, "last_name": "", "reposts_count": 0, "public_favorites_count": 0, "followings_count": 828, "full_name": "", "id": 54206388, "city": "", "first_name": "", "track_count": 26, "playlist_count": 1, "discogs_name": null, "followers_count": 1232, "online": false, "username": "Global Goon", "description": "https://j-hok.bandcamp.com/", "permalink": "9ynth", "last_modified": "2016/10/02 06:34:04 +0000", "plan": "Free", "permalink_url": "http://soundcloud.com/9ynth", "likes_count": 0, "kind": "user", "country": null, "uri": "https://api.soundcloud.com/users/54206388", "avatar_url": "https://i1.sndcdn.com/avatars-000219038442-bnu5b1-large.jpg", "comments_count": 3, "website_title": ""}""")
        test_user = User.from_json(user_json)

        with closing(self.testArchive()) as archive:
            self.assertEqual(archive.find_user(test_user.id), None)
            self.assertEqual(archive.add_user(test_user), test_user.id)
            self.assertEqual(archive.find_user(test_user.id), test_user)
            self.assertEqual(list(archive.list_users_page()), [test_user])

    # Basic CRUD tests for the tracks table.
    def test_tracks_crud(self):
        track_json = json.loads(
            """{"reposts_count": 1, "attachments_uri": "https://api.soundcloud.com/tracks/315542893/attachments", "video_url": null, "track_type": null, "release_month": 4, "original_format": "mp3", "label_name": null, "duration": 28606, "id": 315542893, "streamable": true, "user_id": 271252585, "title": "Tha (eazykill worse edit)", "favoritings_count": 15, "commentable": true, "label_id": null, "download_url": "https://api.soundcloud.com/tracks/315542893/download", "state": "finished", "downloadable": false, "policy": "ALLOW", "waveform_url": "https://w1.sndcdn.com/0RlgAibYorVa_m.png", "sharing": "public", "description": "Happy April Fool's Day from the Stupid Color Squad!", "release_day": 1, "purchase_url": null, "permalink": "tha-eazykill-worse-edit", "comment_count": 19, "purchase_title": null, "stream_url": "https://api.soundcloud.com/tracks/315542893/stream", "last_modified": "2017/04/01 12:41:37 +0000", "user": {"username": "stupid color squad", "permalink": "stupidcolorsquad", "avatar_url": "https://i1.sndcdn.com/avatars-000280366830-p4gyyf-large.jpg", "kind": "user", "uri": "https://api.soundcloud.com/users/271252585", "last_modified": "2016/11/28 14:17:18 +0000", "permalink_url": "http://soundcloud.com/stupidcolorsquad", "id": 271252585}, "genre": "", "isrc": null, "download_count": 0, "permalink_url": "https://soundcloud.com/stupidcolorsquad/tha-eazykill-worse-edit", "playback_count": 257, "kind": "track", "release_year": 2017, "license": "all-rights-reserved", "monetization_model": "NOT_APPLICABLE", "artwork_url": "https://i1.sndcdn.com/artworks-000215732996-pa9y35-large.jpg", "created_at": "2017/04/01 12:35:03 +0000", "bpm": null, "uri": "https://api.soundcloud.com/tracks/315542893", "original_content_size": 1177039, "key_signature": null, "release": null, "tag_list": "Worse", "embeddable_by": "all"}""")
        test_track = Track.from_json(track_json)

        with closing(self.testArchive()) as archive:
            self.assertEqual(archive.find_track(test_track.id), None)
            self.assertEqual(archive.add_track(test_track), test_track.id)
            self.assertEqual(archive.find_track(test_track.id), test_track)
            self.assertEqual(list(archive.list_tracks_page()), [test_track])

    # Test pagination logic for user query results.
    def test_users_paging(self):
        with closing(self.testArchive()) as archive:
            # Insert 1.5 pages worth of tracks.
            num_users = int(archive.page_size * 1.5)
            for x in range(num_users):
                archive.add_user(self.__make_test_user(x))
            # Page through them, making sure the page counts make sense.
            self.__test_pages(archive.list_users_page, [archive.page_size, num_users - archive.page_size])

    # Test pagination logic for track query results.
    def test_tracks_paging(self):
        with closing(self.testArchive()) as archive:
            # Insert 1.5 pages worth of tracks.
            num_tracks = int(archive.page_size * 1.5)
            for x in range(num_tracks):
                archive.add_track(self.__make_test_track(x))
            # Page through them, making sure the page counts make sense.
            self.__test_pages(archive.list_tracks_page, [archive.page_size, num_tracks - archive.page_size])

    def __test_pages(self, page_gen, page_counts):
        for page_number, page_count in enumerate(page_counts):
            page = list(page_gen(page_number))
            self.assertEqual(len(page), page_count)

    @staticmethod
    def __make_test_user(x):
        return User(
            id=x,
            permalink=x,
            username="fake user {}".format(x),
            avatar_url="https://soundcloud.com/{}/avatar.jpg".format(x))

    @staticmethod
    def __make_test_track(x):
        return Track(
            id=x,
            permalink="https://soundcloud.com/{}/{}".format(x, x),
            user_id=x,
            username="fake user {}".format(x),
            title="fake track {}".format(x),
            uri=None,
            artwork_url="https://soundcloud.com/{}/{}/artwork.jpg".format(x, x),
            is_downloadable=False,
            is_streamable=True)


if __name__ == "__main__":
    unittest.main()
