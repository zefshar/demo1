from typing import List
from authmouse.sugar import Sugar

class AuthMouse():

    def __init__(self,
        client_id: str = None,
        client_secret: str = None,
        scope: List[str] = None,
        user_agent: str = None,
        oauth_displayname: str = None,
        api_key: str = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.user_agent = user_agent
        self.oauth_displayname = oauth_displayname
        self.api_key = api_key

    def client(self, client):
        return Sugar(self, client)
