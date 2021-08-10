import argparse
import base64
import datetime
import io
import json
import logging
import mmap
import os
import re
import sys
import tarfile
import time
import traceback
from concurrent.futures._base import Future
from http import server
from os.path import expanduser, join
from threading import Condition, Thread
from typing import Optional

from demo1.api.demo1_configuration import Demo1Configuration
from demo1.api.demo1_error import Demo1Error
from demo1.api.demo1_version import Demo1Version
from demo1.api.parallel.scheduled_thread_pool_executor import \
    ScheduledThreadPoolExecutor
from demo1.api.process_controller import ProcessController
from demo1.api.state_presenter import StatePresenter
from demo1.api.tasks.maintenance import UpdateRoute53Task


def log_exception(future: Future):
    if future.exception():
        logging.getLogger().error('Background task error', exc_info=(
            type(future.exception()), future.exception(), future.exception().__traceback__))
    else:
        logging.getLogger().info('Success execution of background task')


if __name__ == "__main__":
    print(f'{Demo1Version.standard()} start')
    # root logger
    logging.basicConfig(
        format='[%(levelname)-8s] [%(threadName)-11s] %(message)s',
        encoding='utf-8', level=logging.DEBUG)
    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel(logging.DEBUG)

    logger = logging.getLogger(str(__file__))
    try:

        process_controller = ProcessController()
        # LOAD CONFIGURATION
        demo1_configuration = Demo1Configuration()

        # PARSE COMMAND LINE ARGUMENTS
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '-p', '--http-or-https-port', help='Specify http/https port for listening.'
            ' If port end with 3 (as decimal number) it automatically switch onto the listening port with https protocol.', default=8000)
        parser.add_argument(
            '-k', '--keys-folder', help='Specify folder where keys archive placed.', default=join(expanduser("~"), '.ssl'))
        parser.add_argument(
            '-a', '--host', help='Specify host for port allocation.', default='127.0.0.1')
        parser.add_argument(
            '-g1', '--google-service-account', help='Specify service account from google cloud console.', default=None)
        parser.add_argument(
            '-g2', '--google-private-key-json', help='Specify a name for private key JSON. Key should be download from google cloud console.', default=None)

        args = parser.parse_args()
        demo1_configuration.set_port(int(args.http_or_https_port))
        demo1_configuration.set_ssl_enable(
            str(args.http_or_https_port)[-1] == '3')
        demo1_configuration.set_keys_folder(args.keys_folder)
        demo1_configuration.set_host(args.host)

        demo1_configuration.set_google_service_account(
            args.google_service_account)
        demo1_configuration.set_google_private_key_json(
            args.google_private_key_json)

        # UPDATE ENVIRONMENT VARIABLES FROM THE CONFIGURATION
        demo1_configuration.log_environ(logging.INFO)
        demo1_configuration.refresh_environ()

        if process_controller.get_kill_now_nowait():
            raise Demo1Error('Catch the external interruption signal')

        main_pool = ScheduledThreadPoolExecutor(max_workers=2,
                                                thread_name_prefix='main-thread')
        # SENSOR STATE PRESENTER
        demo1_state_presenter = StatePresenter(demo1_configuration)
        demo1_state_presenter_thread = Thread(
            target=demo1_state_presenter.start, daemon=True)
        demo1_state_presenter_thread.start()

        # MAINTENACE TASKS
        main_pool.submit(UpdateRoute53Task().execute).add_done_callback(
            log_exception)

        # END OF TASKS CONFIGURATION
        logger.debug('Wait for os signal, start time: %s',
                     datetime.datetime.utcnow())

        # Wait until stop from os
        process_controller.get_kill_now()

        timer = time.time()
        # Stop presenter
        demo1_state_presenter.stop()

        # Shutdown pools
        main_pool.shutdown()
        logger.info('Shutdown in %ss' % (time.time() - timer))
    finally:
        logger.debug('Finish execution, finish time: %s',
                     datetime.datetime.utcnow())
