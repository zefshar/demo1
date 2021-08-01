import base64
import hashlib
import hmac
import json
from asyncio import get_event_loop
from os import environ
from unittest import TestCase

from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA

from aiohttp import ClientSession
from aiohttp.formdata import FormData
from amouse import AuthMouse


class TestAuthMouse(TestCase):
    """Simple test

    Before execution please make sure, that .buildew file
    From the root project folder has correct values:
    client_id=...
    client_secret=...
    api_key=...
    """

    def setUp(self) -> None:
        with open('.buildew', 'r') as reader:
            for key, value in [key_value_string.split('=') for key_value_string in reader.read().split('\n') if '=' in key_value_string]:
                environ[key.strip(' ')] = value.strip(' ')

    def test_get_token(self):

        async def test_get_token_async():
            return await AuthMouse(
                client_id=environ['client_id'],
                client_secret=environ['client_secret'],
                scope=['https://www.googleapis.com/auth/drive.metadata.readonly'],
                user_agent='TestAuthMouse',
                oauth_displayname='TestAuthMouse',
                api_key=environ['api_key']
            ).client(ClientSession()).get('https://www.googleapis.com/drive/v3/files?q=%221vbuT3Ye50ihdOHe3UVaOeiQhT4t5KN8n%22%20in%20parents')

        loop = get_event_loop()
        result = loop.run_until_complete(test_get_token_async())
        loop.close()

        self.assertEqual(result.status, 200)

    def test_get_token_by_service_account(self):

        async def test_get_token_async():
            client_session = ClientSession()

            header = {'typ': 'JWT', 'alg': 'HS256'}
            header = base64.b64encode(json.dumps(header).encode()).decode()
            payload = {
                'iss': environ['service_account'],
                'scope': 'https://www.googleapis.com/auth/drive.metadata.readonly',
                'aud': "https://oauth2.googleapis.com/token",
                'exp': 1328554385,
                'iat': 1328550785
            }
            payload = base64.b64encode(json.dumps(header).encode()).decode()
            message = header + '.' + payload

            secret = 'suibianxie'
            h_obj = hmac.new(secret.encode(), message.encode(), hashlib.sha256)
            signature = h_obj.hexdigest()

            form_data = FormData()
            form_data.add_field(
                'grant_type', 'urn:ietf:params:oauth:grant-type:jwt-bearer')
            form_data.add_field('assertion', message+'.'+signature)

            key = RSA.import_key(open('private_key.der').read())
            h = SHA256.new(message)
            signature = pkcs1_15.new(key).sign(h)

            response = await client_session.post('https://oauth2.googleapis.com/token',
                                                 data=form_data)
            response_json = await response.json()

            if not(response.status == 200):
                raise Exception(f'Token request returns error: {response_json}')

            access_token = response_json['access_token']
            return ClientSession().get(f'https://www.googleapis.com/drive/v3/files?q=%221vbuT3Ye50ihdOHe3UVaOeiQhT4t5KN8n%22%20in%20parents&access_token={access_token}')

        loop = get_event_loop()
        result = loop.run_until_complete(test_get_token_async())
        loop.close()

        self.assertEqual(result.status, 200)
