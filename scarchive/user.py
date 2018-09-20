class User(object):

    def __init__(self, id, username, permalink, avatar_url):
        self.id = id
        self.permalink = permalink
        self.username = username
        self.avatar_url = avatar_url

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (self.id == other.id and
                    self.permalink == other.permalink and
                    self.username == other.username and
                    self.avatar_url == other.avatar_url)
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    @staticmethod
    def from_row(row):
        return User(*row)

    @staticmethod
    def from_json(user_json: dict):
        fields_to_save = ["id", "permalink", "username", "avatar_url"]
        user_dict = {field: user_json[field] for field in fields_to_save if field in user_json}
        return User(**user_dict)
