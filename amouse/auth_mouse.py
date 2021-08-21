from base64 import b64encode
from datetime import datetime, timedelta
from json import dumps, loads
from os import environ
from typing import List

from aiohttp import ClientSession, web
from aiohttp.formdata import FormData
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15

from amouse.sugar import Sugar


class AuthMouse():
    """Wrapper for the client

     - That adds addition functionality for get token.
       It executes in background during basic request.
    """

    def __init__(self,
                 # client_id: str = None,
                 # client_secret: str = None,
                 scope: str = None,
                 # user_agent: str = None,
                 # oauth_displayname: str = None,
                 # api_key: str = None,
                 service_account: str = None,
                 private_key: str = None,
                 access_token: str = None):
        # self.client_id = client_id
        # self.client_secret = client_secret
        self.scope = scope
        # self.user_agent = user_agent
        # self.oauth_displayname = oauth_displayname
        # self.api_key = api_key
        self.service_account = service_account
        self.private_key = private_key
        self.access_token = access_token if access_token else environ.get('auth_mouse_access_token')

    async def get_access_token_async(self, client):
        if self.access_token:
            return self.access_token
        header = {'typ': 'JWT', 'alg': 'RS256'}
        header = b64encode(dumps(header).encode()).decode()
        current_date_time_in_utc = datetime.now()
        payload = {
            'iss': self.service_account,
            'scope': self.scope,
            'aud': 'https://oauth2.googleapis.com/token',
            'exp': int((current_date_time_in_utc + timedelta(hours=1)).timestamp()),
            'iat': int(current_date_time_in_utc.timestamp())
        }
        payload = b64encode(dumps(payload).encode()).decode()
        message = header + '.' + payload

        key = RSA.import_key(self.private_key)
        h_obj = SHA256.new(message.encode())
        signature = pkcs1_15.new(key).sign(h_obj)
        signature = b64encode(signature).decode()

        form_data = FormData()
        form_data.add_field(
            'grant_type', 'urn:ietf:params:oauth:grant-type:jwt-bearer')
        form_data.add_field('assertion', message+'.'+signature)

        response = await client.post('https://oauth2.googleapis.com/token',
                                     data=form_data)
        response_json = await response.json()

        if not(response.status == 200):
            raise Exception(
                f'Token request returns error: {response_json}')

        access_token = response_json['access_token']
        self.access_token = access_token
        environ['auth_mouse_access_token'] = access_token
        return access_token

    def _authorized_get_request(self, client, method):
        async def _get_request_async(*args):
            modified_args = (args[0] + '&access_token=' + await self.get_access_token_async(client), ) + args[1:]
            response = await method(*modified_args)
            if response.status != 400 or response.status != 401:
                return response
            # Refresh token
            self.access_token = None
            environ['auth_mouse_access_token'] = None
            modified_args = (args[0] + '&access_token=' + await self.get_access_token_async(client), ) + args[1:]
            return await method(*modified_args)

        return _get_request_async

    def client(self, client):
        return Sugar(self, client)
