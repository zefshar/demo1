
from json import dumps

from aiohttp import web


class GoogleDriveFiles:

    @classmethod
    def process(cls, path: str, query: dict, application_path: str = None) -> web.Response:
        """/api/files?
        """
        folder_id = next(iter(query.keys()))
        content = dumps(
            {}).encode('utf-8')
        return web.Response(status=200, body=content, headers={
            'Content-Type': 'application/json',
            'Content-Length': str(len(content))})
