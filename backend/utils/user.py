
class User:
    is_active = True
    is_authenticated = True

    def __init__(self, user):
        self.id = str(user['_id'])
        self.email = user['email']

    def get_id(self):
        return self.id
