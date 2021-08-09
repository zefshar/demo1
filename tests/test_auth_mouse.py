import base64
import hashlib
import hmac
import json
from asyncio import get_event_loop
from datetime import datetime, timedelta
from os import environ
from unittest import TestCase

from aiohttp import ClientSession
from aiohttp.formdata import FormData
from amouse import AuthMouse
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from demo1.api.demo1_configuration import Demo1Configuration


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
        demo1_configuration = Demo1Configuration()
        demo1_configuration.set_google_private_key_json(environ['google_private_key_json'])
        demo1_configuration.set_google_service_account(environ['google_service_account'])
        demo1_configuration.refresh_environ()

    def test_get_token_direct_flow(self):

        async def test_get_token_async():
            with open(environ['google_private_key_path'], 'r') as reader:
                private_key = json.loads(reader.read())['private_key']

            async with ClientSession() as client_session:
                response = await AuthMouse(
                    service_account=environ['google_service_account'],
                    private_key=private_key,
                    scope='https://www.googleapis.com/auth/drive.metadata.readonly'
                ).client(client_session).get('https://www.googleapis.com/drive/v3/files?q=%221vbuT3Ye50ihdOHe3UVaOeiQhT4t5KN8n%22%20in%20parents')
                return {'status': response.status, 'json': await response.json()}

        loop = get_event_loop()
        result = loop.run_until_complete(test_get_token_async())
        loop.close()

        self.assertEqual(result['status'], 200)

    def test_get_token_indirect_flow(self):

        async def test_get_token_async():
            with open(environ['google_private_key_path'], 'r') as reader:
                private_key = json.loads(reader.read())['private_key']

            a_mouse = AuthMouse(
                service_account=environ['google_service_account'],
                private_key=private_key,
                scope='https://www.googleapis.com/auth/drive.metadata.readonly'
            )

            result = await a_mouse.client(ClientSession()).get('https://www.googleapis.com/drive/v3/files?q=%221vbuT3Ye50ihdOHe3UVaOeiQhT4t5KN8n%22%20in%20parents')
            access_token = a_mouse.access_token

            async with ClientSession() as client_session:
                async with client_session.get(f'https://www.googleapis.com/drive/v3/files?q=%221vbuT3Ye50ihdOHe3UVaOeiQhT4t5KN8n%22%20in%20parents&access_token={access_token}') as response:
                    return {'status': response.status, 'json': await response.json()}

        loop = get_event_loop()
        result = loop.run_until_complete(test_get_token_async())
        loop.close()

        self.assertEqual(result['status'], 200)

    def test_get_token_by_service_account(self):

        async def test_get_token_async():
            header = {'typ': 'JWT', 'alg': 'RS256'}
            header = base64.b64encode(json.dumps(header).encode()).decode()
            current_date_time_in_utc = datetime.now()
            payload = {
                'iss': environ['google_service_account'],
                'scope': 'https://www.googleapis.com/auth/drive.metadata.readonly',
                'aud': "https://oauth2.googleapis.com/token",
                'exp': int((current_date_time_in_utc + timedelta(hours=1)).timestamp()),
                'iat': int(current_date_time_in_utc.timestamp())
            }
            payload = base64.b64encode(json.dumps(payload).encode()).decode()
            message = header + '.' + payload

            with open(environ['google_private_key_path'], 'r') as reader:
                private_key = json.loads(reader.read())['private_key']
            key = RSA.import_key(private_key)
            h_obj = SHA256.new(message.encode())
            signature = pkcs1_15.new(key).sign(h_obj)
            signature = base64.b64encode(signature).decode()

            form_data = FormData()
            form_data.add_field(
                'grant_type', 'urn:ietf:params:oauth:grant-type:jwt-bearer')
            form_data.add_field('assertion', message+'.'+signature)

            async with ClientSession() as client_session:
                response = await client_session.post('https://oauth2.googleapis.com/token',
                                                     data=form_data)
                response_json = await response.json()

                if not(response.status == 200):
                    raise Exception(
                        f'Token request returns error: {response_json}')

                access_token = response_json['access_token']
                async with client_session.get(f'https://www.googleapis.com/drive/v3/files?q=%221vbuT3Ye50ihdOHe3UVaOeiQhT4t5KN8n%22%20in%20parents&access_token={access_token}') as response:
                    return {'status': response.status, 'json': await response.json()}

        loop = get_event_loop()
        result = loop.run_until_complete(test_get_token_async())
        loop.close()

        print(f'API call result is {result["json"]}')
        self.assertEqual(result['status'], 200)
