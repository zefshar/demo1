import argparse
import asyncio
import base64
import datetime
import io
import json
import logging
import mmap
import os
import re
import socketserver
import sys
import tarfile
import time
import traceback
import urllib
from asyncio import Condition, new_event_loop, set_event_loop
from asyncio.events import AbstractEventLoop
from concurrent.futures._base import Future
from http import server
from threading import current_thread
from typing import Optional

from aiohttp import web
from aiohttp.web_request import BaseRequest

from demo1.api.demo1_configuration import Demo1Configuration
from demo1.api.demo1_error import Demo1Error
from demo1.api.demo1_version import Demo1Version
from demo1.api.parallel.scheduled_thread_pool_executor import \
    ScheduledThreadPoolExecutor
from demo1.api.process_controller import ProcessController
from demo1.api.tasks.balance_task import BalanceTask
from demo1.api.tasks.buy_task import BuyTask
from demo1.api.tasks.load_data_task import LoadDataTask
from demo1.api.tasks.price_task import PriceTask
from demo1.api.tasks.sell_task import SellTask
from demo1.api.tasks.status_task import StatusTask

DEMO1_FLUTTER_PACK = 'demo1.flutter'
PR1_FLUTTER_PACK = 'pr1.flutter'
APPLICATION_JSON = 'application/json'


class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)


class Demo1StateController(object):

    def __init__(self) -> None:
        super().__init__()
        self.logger = logging.getLogger(str(self.__class__))
        self.streaming_output = StreamingOutput()
        self.released = False

        self.demo1_executor = None
        self.demo1_configuration = None
        self.blank_image = None

        self.live_stream_width = 320
        self.live_stream_height = 240
        self.live_stream_frame_rate = 5

    def is_setup_mode(self):
        if self.demo1_configuration:
            return self.demo1_configuration.get_setup_mode()
        return True

    def get_status(self) -> dict:
        result = dict()
        if self.demo1_configuration:
            result['setup_mode'] = self.demo1_configuration.get_setup_mode()
        return result

    def load_data(self, get_request: str) -> dict:
        result = dict()
        if self.demo1_configuration:
            result['setup_mode'] = self.demo1_configuration.get_setup_mode()
        if self.demo1_executor:
            parsed_get_request = urllib.parse.urlparse(get_request)
            query = urllib.parse.parse_qs(parsed_get_request.query)
            self.demo1_executor.submit(LoadDataTask(json.loads(
                query['q'][0])).execute).add_done_callback(self.log_exception)
        return result

    def buy(self, get_request: str) -> dict:
        result = dict()
        if self.demo1_configuration:
            result['setup_mode'] = self.demo1_configuration.get_setup_mode()
        if self.demo1_executor:
            parsed_get_request = urllib.parse.urlparse(get_request)
            query = urllib.parse.parse_qs(parsed_get_request.query)
            self.demo1_executor.submit(BuyTask(json.loads(
                query['q'][0])).execute).add_done_callback(self.log_exception)
        return result

    def sell(self, get_request: str) -> dict:
        result = dict()
        if self.demo1_configuration:
            result['setup_mode'] = self.demo1_configuration.get_setup_mode()
        if self.demo1_executor:
            parsed_get_request = urllib.parse.urlparse(get_request)
            query = urllib.parse.parse_qs(parsed_get_request.query)
            self.demo1_executor.submit(SellTask(json.loads(
                query['q'][0])).execute).add_done_callback(self.log_exception)
        return result

    def status(self, get_request: str) -> dict:
        result = dict()
        if self.demo1_configuration:
            result['setup_mode'] = self.demo1_configuration.get_setup_mode()
        if self.demo1_executor:
            parsed_get_request = urllib.parse.urlparse(get_request)
            query = urllib.parse.parse_qs(parsed_get_request.query)
            self.demo1_executor.submit(StatusTask(json.loads(
                query['q'][0])).execute).add_done_callback(self.log_exception)
        return result

    def balance(self, get_request: str) -> dict:
        result = dict()
        if self.demo1_configuration:
            result['setup_mode'] = self.demo1_configuration.get_setup_mode()
        if self.demo1_executor:
            parsed_get_request = urllib.parse.urlparse(get_request)
            query = urllib.parse.parse_qs(parsed_get_request.query)
            self.demo1_executor.submit(BalanceTask(json.loads(
                query['q'][0])).execute).add_done_callback(self.log_exception)
        return result

    def price(self, get_request: str) -> dict:
        result = dict()
        if self.demo1_configuration:
            result['setup_mode'] = self.demo1_configuration.get_setup_mode()
        if self.demo1_executor:
            parsed_get_request = urllib.parse.urlparse(get_request)
            query = urllib.parse.parse_qs(parsed_get_request.query)
            self.demo1_executor.submit(PriceTask(json.loads(
                query['q'][0])).execute).add_done_callback(self.log_exception)
        return result

    def log_exception(self, future: Future):
        if future.exception():
            self.logger.error('Background task error', exc_info=(
                type(future.exception()), future.exception(), future.exception().__traceback__))
        else:
            self.logger.info('Success execution of background task')

    @staticmethod
    def _extract_date_time(metadata_id: list) -> str:
        if metadata_id:
            matcher = re.search(
                r'^(\d+)-(\d+)-(\d+)-(\d+)-(\d+)-(\d+)', metadata_id[0])
            if matcher:
                return '%s-%s-%sT%s:%s:%sZ' % (
                    matcher.group(1), matcher.group(2), matcher.group(
                        3), matcher.group(4), matcher.group(5),
                    matcher.group(6))
        return None

    def set_setup_mode(self, setup_mode: bool):
        if not self.demo1_configuration:
            raise Demo1Error('demo1 configuration does not set')

        if self.is_setup_mode() == setup_mode:
            return

        self.demo1_configuration.set_setup_mode(setup_mode)

        if setup_mode:
            self.__write_blank_image()
        else:
            self.__write_blank_image()

        self.demo1_configuration.flush()

    def create(self):
        if self.is_setup_mode():
            self.__write_blank_image()
        else:
            self.__write_blank_image()

    def release(self):
        try:
            ...
        except Exception as e:
            self.logger.error('Stop recording error: %s', e, exc_info=True)
        finally:
            self.__write_blank_image()

        with self.streaming_output.condition:
            self.released = True
            self.streaming_output.condition.notify_all()

    def __write_blank_image(self):
        # if not self.blank_image:
        #     self.blank_image = np.zeros((self.live_stream_height, self.live_stream_width, 3), np.uint8)
        #     rgb_color = (255, 255, 255)  # White color RGB
        #     self.blank_image[:] = tuple(reversed(rgb_color))
        #     success, buffer = cv2.imencode(".jpg", self.blank_image)
        #     self.blank_image = buffer.tobytes()
        # self.streaming_output.write(self.blank_image)
        # self.streaming_output.write(self.blank_image)
        pass


demo1_state_controller = Demo1StateController()


class FlutterBundle(object):

    def __init__(self, bundle_name: str, folders: list = []):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.bundle_file_path = self.__find(folders, bundle_name + '.flutter')
        self.pathmap = {}
        self.file_object = None
        self.tar_file = None
        if self.bundle_file_path:
            file = open(self.bundle_file_path, 'rb')
            self.file_object = mmap.mmap(
                file.fileno(), 0, access=mmap.ACCESS_READ)
            self.tar_file = tarfile.open(mode='r', fileobj=self.file_object)
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
            '.tiff': 'image/tiff',
            '.webp': 'image/webp',
            '.ttf': 'font/ttf',
            '.otf': 'font/otf',
            '.woff': 'font/woff',
            '.woff2': 'font/woff2',
        }
        self.logger.info('FlutterBundle finish initialization')

    def __find(self, folders: list, file_name: str):
        for folder in folders:
            if os.path.exists(folder):
                for root, _, files in os.walk(folder, followlinks=True):
                    for _name in files:
                        if _name == file_name:
                            return os.path.abspath(os.path.join(root, file_name))
        return None

    def process(self, path: str, application_path: Optional[str] = None) -> web.Response:
        file_path = '.' + (path[len(application_path):] if application_path else path)
        _, file_extension = os.path.splitext(path)
        # Auto-append index.html for folders
        if not file_extension:
            file_path += '/index.html'
            file_extension = '.html'
        with self.tar_file.extractfile(file_path) as entry:
            content = entry.read()
            return web.Response(status=200, headers={
                'Content-Type': self.content_types[file_extension],
                'Content-Length': str(len(content))},
                body=content)

    def has_path(self, path: str, application_path: str = None):
        file_path = (path[len(application_path):] if application_path else path)
        return file_path in self.pathmap

    def release(self):
        if self.tar_file:
            self.tar_file.close()
        if self.file_object:
            self.file_object.close()


class PresenterHandler:

    flutter_bundle = None
    logger = logging.getLogger(str('PresenterHandler'))

    async def do_GET(self, request: BaseRequest) -> web.Response:
        path = request.path
        if path == '/':
            return web.Response(status=301, headers={'Location': '/index.html'})
        if path == '/demo1' or path == '/demo1/':
            return web.Response(status=301, headers={'Location': '/demo1/index.html'})
        elif PresenterHandler.pr1_bundle.has_path(path):
            return PresenterHandler.pr1_bundle.process(path)
        elif path.startswith('/demo1') and PresenterHandler.demo1_bundle.has_path(path, '/demo1'):
            return PresenterHandler.demo1_bundle.process(path, '/demo1')
        elif path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control',
                             'private, no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.send_header(
                'Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                self.__streaming()
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        elif path == '/status':
            content = json.dumps(
                demo1_state_controller.get_status()).encode('utf-8')
            return web.Response(status=200, body=content, headers={
                'Content-Type': 'application/json',
                'Content-Length': str(len(content))
            })
        elif path.startswith('/api-1.0/load-data'):
            content = json.dumps(
                demo1_state_controller.load_data(path)).encode('utf-8')
            return web.Response(status=200, body=content, headers={
                'Content-Type': 'application/json',
                'Content-Length': str(len(content))
            })
        elif path.startswith('/api-1.0/buy'):
            content = json.dumps(
                demo1_state_controller.buy(path)).encode('utf-8')
            return web.Response(status=200, body=content, headers={
                'Content-Type': 'application/json',
                'Content-Length': str(len(content))
            })
        elif path.startswith('/api-1.0/sell'):
            content = json.dumps(
                demo1_state_controller.sell(path)).encode('utf-8')
            return web.Response(status=200, body=content, headers={
                'Content-Type': 'application/json',
                'Content-Length': str(len(content))
            })
        elif path.startswith('/api-1.0/status'):
            content = json.dumps(
                demo1_state_controller.status(path)).encode('utf-8')
            return web.Response(status=200, body=content, headers={
                'Content-Type': 'application/json',
                'Content-Length': str(len(content))
            })
        elif path.startswith('/api-1.0/balance'):
            content = json.dumps(
                demo1_state_controller.balance(path)).encode('utf-8')
            return web.Response(status=200, body=content, headers={
                'Content-Type': 'application/json',
                'Content-Length': str(len(content))
            })
        elif path.startswith('/api-1.0/price'):
            content = json.dumps(
                demo1_state_controller.price(path)).encode('utf-8')
            self.send_response(200)
            return web.Response(status=200, body=content, headers={
                'Content-Type': 'application/json',
                'Content-Length': str(len(content))
            })
        elif path == '/set-setup-mode-false':
            demo1_state_controller.set_setup_mode(False)
            return self.__success_response()
        elif path == '/set-setup-mode-true':
            demo1_state_controller.set_setup_mode(True)
            return self.__success_response()
        else:
            return web.Response(status=404)

    def __streaming(self):
        # Write request immediately if not setup_mode
        if not demo1_state_controller.is_setup_mode():
            frame = demo1_state_controller.streaming_output.frame
            self.__write_frame(frame)
        while demo1_state_controller.is_setup_mode():
            with demo1_state_controller.streaming_output.condition:
                demo1_state_controller.streaming_output.condition.wait(3)
                frame = demo1_state_controller.streaming_output.frame
            self.__write_frame(frame)

            if demo1_state_controller.released:
                break

    def __write_frame(self, frame):
        self.wfile.write(b'--FRAME\r\n')
        self.send_header('Content-Type', 'image/jpeg')
        self.send_header('X-Timestamp', str(time.time()))
        self.send_header('Content-Length', str(len(frame)))
        self.end_headers()
        self.wfile.write(frame)
        self.wfile.write(b'\r\n')

    def __success_response(self) -> web.Request:
        content = '{"success": true}'.encode('utf-8')
        return web.Response(status=200, body=content, headers={
            'Content-Type': 'application/json',
            'Content-Length': str(len(content))
        })


class StatePresenter:
    event_loop:     AbstractEventLoop = None
    stop_condition: Condition = None

    def __init__(self, demo1_configuration: Demo1Configuration) -> None:
        super().__init__()
        self.logger = logging.getLogger(StatePresenter.__class__.__name__)
        self.demo1_configuration = demo1_configuration

    @classmethod
    async def _serve_until_stop_signal(cls, host: str, port: int):
        if not current_thread().isDaemon():
            raise Demo1Error('Thread not a daemon')
        current_thread().setName('http-thread')
        server = web.Server(PresenterHandler().do_GET)
        runner = web.ServerRunner(server)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()

        await cls.stop_condition.acquire()
        try:
            await cls.stop_condition.wait()
            print('Ok')
        finally:
            cls.stop_condition.release()

    @classmethod
    def serve(cls, request_timeout: int = 1, handler=None, port: int = 0, host: str = 'localhost'):
        if cls.event_loop:
            raise Demo1Error('Another event loop is active')
        cls.event_loop = new_event_loop()
        cls.stop_condition = Condition(loop=cls.event_loop)
        set_event_loop(cls.event_loop)
        cls.event_loop.run_until_complete(
            cls._serve_until_stop_signal(host, port))

    @classmethod
    def not_serve(cls):
        if cls.cls.stop_condition:
            cls.stop_condition.acquire()
            try:
                cls.stop_condition.notify()
                print('Ok')
            finally:
                cls.stop_condition.release()
        if cls.event_loop:
            cls.event_loop.stop()
            cls.event_loop = None

    def start(self):

        PresenterHandler.demo1_bundle = FlutterBundle(
            'demo1', [self.demo1_configuration.get_application_folder()])  # [.] for debug
        PresenterHandler.pr1_bundle = FlutterBundle(
            'pr1', [self.demo1_configuration.get_application_folder()])  # [.] for debug
        demo1_state_controller.demo1_executor = ScheduledThreadPoolExecutor(max_workers=1,
                                                                            thread_name_prefix='executor-thread')
        demo1_state_controller.demo1_configuration = self.demo1_configuration
        demo1_state_controller.create()
        try:
            self.logger.info(
                f'Start web-server on port {self.demo1_configuration.get_http_port()}')
            self.serve(request_timeout=1,
                       port=self.demo1_configuration.get_http_port())
        except Exception as ex:
            self.logger.error(ex, exc_info=True)
        finally:
            demo1_state_controller.release()

    def stop(self):
        self.logger.debug('Stop demo1 state presenter')
        self.not_serve()
        demo1_state_controller.release()
