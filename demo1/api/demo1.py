import io
import json
import logging
import socketserver
import time
import mmap
import tarfile
import base64
from threading import Condition
from concurrent.futures._base import Future
from http import server
import urllib
import traceback
import argparse
from typing import Optional

from demo1.api.demo1_version import Demo1Version
from demo1.api.demo1_configuration import Demo1Configuration
from demo1.api.demo1_process_controller import Demo1ProcessController
from demo1.api.demo1_error import Demo1Error
from demo1.api.parallel.scheduled_thread_pool_executor import ScheduledThreadPoolExecutor

from demo1.api.tasks.load_data_task import LoadDataTask
from demo1.api.tasks.buy_task import BuyTask
from demo1.api.tasks.sell_task import SellTask
from demo1.api.tasks.status_task import StatusTask
from demo1.api.tasks.balance_task import BalanceTask
from demo1.api.tasks.price_task import PriceTask

import re
import datetime
import sys
import os


DEMO1_FLUTTER_PACK='demo1.flutter'
PR1_FLUTTER_PACK='pr1.flutter'
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
            self.demo1_executor.submit(LoadDataTask(json.loads(query['q'][0])).execute).add_done_callback(self.log_exception)
        return result

    def buy(self, get_request: str) -> dict:
        result = dict()
        if self.demo1_configuration:
            result['setup_mode'] = self.demo1_configuration.get_setup_mode()
        if self.demo1_executor:
            parsed_get_request = urllib.parse.urlparse(get_request)
            query = urllib.parse.parse_qs(parsed_get_request.query)
            self.demo1_executor.submit(BuyTask(json.loads(query['q'][0])).execute).add_done_callback(self.log_exception)
        return result

    def sell(self, get_request: str) -> dict:
        result = dict()
        if self.demo1_configuration:
            result['setup_mode'] = self.demo1_configuration.get_setup_mode()
        if self.demo1_executor:
            parsed_get_request = urllib.parse.urlparse(get_request)
            query = urllib.parse.parse_qs(parsed_get_request.query)
            self.demo1_executor.submit(SellTask(json.loads(query['q'][0])).execute).add_done_callback(self.log_exception)
        return result

    def status(self, get_request: str) -> dict:
        result = dict()
        if self.demo1_configuration:
            result['setup_mode'] = self.demo1_configuration.get_setup_mode()
        if self.demo1_executor:
            parsed_get_request = urllib.parse.urlparse(get_request)
            query = urllib.parse.parse_qs(parsed_get_request.query)
            self.demo1_executor.submit(StatusTask(json.loads(query['q'][0])).execute).add_done_callback(self.log_exception)
        return result

    def balance(self, get_request: str) -> dict:
        result = dict()
        if self.demo1_configuration:
            result['setup_mode'] = self.demo1_configuration.get_setup_mode()
        if self.demo1_executor:
            parsed_get_request = urllib.parse.urlparse(get_request)
            query = urllib.parse.parse_qs(parsed_get_request.query)
            self.demo1_executor.submit(BalanceTask(json.loads(query['q'][0])).execute).add_done_callback(self.log_exception)
        return result

    def price(self, get_request: str) -> dict:
        result = dict()
        if self.demo1_configuration:
            result['setup_mode'] = self.demo1_configuration.get_setup_mode()
        if self.demo1_executor:
            parsed_get_request = urllib.parse.urlparse(get_request)
            query = urllib.parse.parse_qs(parsed_get_request.query)
            self.demo1_executor.submit(PriceTask(json.loads(query['q'][0])).execute).add_done_callback(self.log_exception)
        return result

    def log_exception(self, future: Future):
        if future.exception():
            self.logger.error('Background task error', exc_info=(type(future.exception()), future.exception(), future.exception().__traceback__))
        else:
            self.logger.info('Success execution of background task')

    @staticmethod
    def _extract_date_time(metadata_id: list) -> str:
        if metadata_id:
            matcher = re.search(r'^(\d+)-(\d+)-(\d+)-(\d+)-(\d+)-(\d+)', metadata_id[0])
            if matcher:
                return '%s-%s-%sT%s:%s:%sZ' % (
                matcher.group(1), matcher.group(2), matcher.group(3), matcher.group(4), matcher.group(5),
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

    def process(self, handler: server.BaseHTTPRequestHandler, application_path: Optional[str] = None):
        file_path = '.' + (handler.path[len(application_path):] if application_path else handler.path)
        _, file_extension = os.path.splitext(handler.path)
        # Auto-append index.html for folders
        if not file_extension:
            file_path += '/index.html'
            file_extension = '.html'
        with self.tar_file.extractfile(file_path) as entry:
            content = entry.read()
            handler.send_response(200)
            handler.send_header(
                'Content-Type', self.content_types[file_extension])
            handler.send_header('Content-Length', str(len(content)))
            handler.end_headers()
            handler.wfile.write(content)

    def has_path(self, path: str):
        return path in self.pathmap

    def release(self):
        if self.tar_file:
            self.tar_file.close()
        if self.file_object:
            self.file_object.close()


class PresenterHandler(server.BaseHTTPRequestHandler):

    flutter_bundle = None
    logger = logging.getLogger(str('PresenterHandler'))

    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        if self.path == '/demo1' or self.path == '/demo1/':
            self.send_response(301)
            self.send_header('Location', '/demo1/index.html')
            self.end_headers()
        elif PresenterHandler.pr1_bundle.has_path(self.path):
            PresenterHandler.pr1_bundle.process(self)
        elif self.path.startswith('/demo1') and PresenterHandler.demo1_bundle.has_path(self.path[6:]):
            PresenterHandler.demo1_bundle.process(self, '/demo1')
        elif self.path == '/stream.mjpg':
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
        elif self.path == '/status':
            content = json.dumps(
                demo1_state_controller.get_status()).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        elif self.path.startswith('/api-1.0/load-data'):
            content = json.dumps(demo1_state_controller.load_data(self.path)).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        elif self.path.startswith('/api-1.0/buy'):
            content = json.dumps(demo1_state_controller.buy(self.path)).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        elif self.path.startswith('/api-1.0/sell'):
            content = json.dumps(demo1_state_controller.sell(self.path)).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        elif self.path.startswith('/api-1.0/status'):
            content = json.dumps(demo1_state_controller.status(self.path)).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        elif self.path.startswith('/api-1.0/balance'):
            content = json.dumps(demo1_state_controller.balance(self.path)).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        elif self.path.startswith('/api-1.0/price'):
            content = json.dumps(demo1_state_controller.price(self.path)).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/set-setup-mode-false':
            demo1_state_controller.set_setup_mode(False)
            self.__success_response()
        elif self.path == '/set-setup-mode-true':
            demo1_state_controller.set_setup_mode(True)
            self.__success_response()
        else:
            self.send_error(404)
            self.end_headers()

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

    def __success_response(self):
        content = '{"success": true}'.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)


class Demo1StatePresenter(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, demo1_configuration: Demo1Configuration) -> None:
        super().__init__(('', demo1_configuration.get_http_port()), PresenterHandler)
        self.logger = logging.getLogger(str(self.__class__))
        self.demo1_configuration = demo1_configuration

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
            self.logger.info(f'Start web-server on port {self.demo1_configuration.get_http_port()}')
            self.serve_forever(1)
        finally:
            demo1_state_controller.release()

    def stop(self):
        self.logger.debug('Stop demo1 state presenter')
        demo1_state_controller.release()
        self.shutdown()


if __name__ == "__main__":
    print(f'{Demo1Version.standard()} start')
    # root logger
    logging.basicConfig(format='[%(levelname)-8s] [%(threadName)-11s] %(message)s')
    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel(logging.DEBUG)

    logger = logging.getLogger(str(__file__))
    try:

        process_controller = Demo1ProcessController()
        # LOAD CONFIGURATION
        demo1_configuration = Demo1Configuration()

        # PARSE COMMAND LINE ARGUMENTS
        parser = argparse.ArgumentParser()
        parser.add_argument('-p', '--http-port', help='Specify http port for listening', default=8080)
        args = parser.parse_args()
        demo1_configuration.set_http_port(args.http_port)

        if process_controller.get_kill_now_nowait():
            raise Demo1Error('Catch the external interruption signal')

        main_pool = ScheduledThreadPoolExecutor(max_workers=2,
                                                thread_name_prefix='http-thread')
        # SENSOR STATE PRESENTER
        demo1_state_presenter = Demo1StatePresenter(demo1_configuration)
        main_pool.submit(demo1_state_presenter.start)

        # END OF TASKS CONFIGURATION
        logger.debug('Wait for os signal, start time: %s', datetime.datetime.utcnow())

        # Wait until stop from os
        process_controller.get_kill_now()

        timer = time.time()
        # Stop presenter
        demo1_state_presenter.stop()

        # Shutdown pools
        main_pool.shutdown()
        logger.info('Shutdown in %ss' % (time.time() - timer))
    finally:
        logger.debug('Finish execution, finish time: %s', datetime.datetime.utcnow())
