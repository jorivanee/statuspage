
class User:
    is_active = True
    is_authenticated = True

    def __init__(self, user):
        self.id = str(user['_id'])
        self.email = user['email']
        self.password = user['password']
        self.dark_theme = user['dark_theme'] if "dark_theme" in user else False

    def get_id(self):
        return self.id
