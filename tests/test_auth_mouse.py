
from asyncio import get_event_loop
from aiohttp import ClientSession
from unittest import TestCase

from authmouse import AuthMouse


class TestCameraAdapter(TestCase):

    def setUp(self) -> None:
        # Copy create init file for test
        pass

    def test_get_token(self):

        async def test_get_token_async():
            return await AuthMouse(
                client_id='',
                client_secret='',
                scope='',
                user_agent='',
                oauth_displayname='',
                api_key=''
            ).client(ClientSession()).get('https://www.googleapis.com/drive/v3/files?q=%221vbuT3Ye50ihdOHe3UVaOeiQhT4t5KN8n%22%20in%20parents')

        loop = get_event_loop()
        result = loop.run_until_complete(test_get_token_async())
        loop.close()

        self.assertIsNotNone(result)
