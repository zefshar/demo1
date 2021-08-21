
from base64 import b64encode
from datetime import datetime, timedelta
from json import dumps, loads
from os import environ

from aiohttp import ClientSession, web
from aiohttp.formdata import FormData
from amouse.auth_mouse import AuthMouse
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15


class GoogleDriveFiles:

    private_key = None

    @classmethod
    def _get_private_key(cls):
        if cls.private_key:
            return cls.private_key
        with open(environ['google_private_key_path'], 'r') as reader:
            private_key = loads(reader.read())['private_key']
            cls.private_key = private_key
            return private_key

    @classmethod
    async def process(cls, path: str, query: dict, application_path: str = None) -> web.Response:
        """/api/files?
        """
        folder_id = next(iter(query.keys()))

        async with ClientSession() as client_session:
            response = await AuthMouse(
                service_account=environ['google_service_account'],
                private_key=cls._get_private_key(),
                scope='https://www.googleapis.com/auth/drive.metadata.readonly'
            ).client(client_session).get(f'https://www.googleapis.com/drive/v3/files?q=%22{folder_id}%22%20in%20parents')

            content = dumps(
                await response.json()).encode('utf-8')
            return web.Response(status=response.status, body=content, headers={
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Content-Length': str(len(content))})
