from gzip import compress
from logging import getLogger
from mmap import ACCESS_READ, mmap
from os import walk
from os.path import abspath, exists, join, splitext
from tarfile import open as tarfile_open
from typing import Optional

from aiohttp import web

APPLICATION_JSON = 'application/json'


class StaticBundle(object):

    def __init__(self, bundle_name: str, folders: list = []):
        super().__init__()
        self.logger = getLogger(self.__class__.__name__)
        self.bundle_file_path = self.__find(folders, bundle_name + '.static')
        self.pathmap = {}
        self.file_object = None
        self.tar_file = None
        if self.bundle_file_path:
            file = open(self.bundle_file_path, 'rb')
            self.file_object = mmap(
                file.fileno(), 0, access=ACCESS_READ)
            self.tar_file = tarfile_open(mode='r', fileobj=self.file_object)
            for file_path in self.tar_file.getnames():
                file_path = file_path[1:]
                if file_path:
                    self.pathmap[file_path] = self.process
        self.content_types = {
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'text/javascript',
            '.apng': 'image/apng',
            '.png': 'image/png',
            '.svg': 'image/svg',
            '.ico': 'image/ico',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.json': APPLICATION_JSON,
            '.map': 'text/map',
            '.tiff': 'image/tiff',
            '.webp': 'image/webp',
            '.otf': 'font/otf',
            '.otf': 'font/otf',
            '.woff': 'font/woff',
            '.woff2': 'font/woff2',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        }
        self.logger.info('StaticBundle finish initialization')

    def __find(self, folders: list, file_name: str):
        for folder in folders:
            if exists(folder):
                for root, _, files in walk(folder, followlinks=True):
                    for _name in files:
                        if _name == file_name:
                            return abspath(join(root, file_name))
        return None

    def process(self, path: str, application_path: Optional[str] = None) -> web.Response:
        file_path = '.' + (path[len(application_path):]
                           if application_path else path)
        _, file_extension = splitext(path)
        # Auto-append index.html for folders
        if not file_extension:
            file_path += '/index.html'
            file_extension = '.html'
        with self.tar_file.extractfile(file_path) as entry:
            content = compress(entry.read())
            return web.Response(status=200, headers={
                'Content-Type': self.content_types[file_extension],
                'Content-Length': str(len(content)),
                'Content-Encoding': 'gzip'},
                body=content)

    def has_path(self, path: str, application_path: str = None):
        file_path = (path[len(application_path):]
                     if application_path else path)
        return file_path in self.pathmap

    def release(self):
        if self.tar_file:
            self.tar_file.close()
        if self.file_object:
            self.file_object.close()
