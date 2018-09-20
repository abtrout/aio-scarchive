from .user import User


class Track(object):

    def __init__(self, id, permalink, user_id, username, title, uri, artwork_url, is_downloadable, is_streamable):
        self.id = id
        self.permalink = permalink
        self.user_id = user_id
        self.username = username
        self.title = title
        self.uri = uri
        self.artwork_url = artwork_url
        self.is_downloadable = is_downloadable
        self.is_streamable = is_streamable

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (self.id == other.id and
                    self.permalink == other.permalink and
                    self.user_id == other.user_id and
                    self.username == other.username and
                    self.title == other.title and
                    self.uri == other.uri and
                    self.artwork_url == other.artwork_url and
                    self.is_downloadable == other.is_downloadable and
                    self.is_streamable == other.is_streamable)
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    @staticmethod
    def from_row(row):
        return Track(*row)

    @staticmethod
    def from_json(track_json):
        track_user = User.from_json(track_json["user"])
        fields_to_save = ["id", "permalink_url", "title", "artwork_url", "streamable", "downloadable"]
        track_dict = {field: track_json[field] for field in fields_to_save if field in track_json}
        return Track(
            id=track_dict["id"],
            permalink=track_dict.get("permalink_url"),
            user_id=track_user.id,
            username=track_user.username,
            title=track_dict.get("title"),
            uri=None,
            artwork_url=track_dict.get("artwork_url"),
            is_downloadable=track_dict.get("downloadable"),
            is_streamable=track_dict.get("streamable"))
