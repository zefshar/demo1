import signal
import threading

from demo1.api.demo1_error import Demo1Error
from demo1.api.demo1_version import Demo1Version
from demo1.api.utils import print_threads


class ProcessController:
    """
    System signal mapper on internal state variable
    """

    def __init__(self, launcher_folder: str = None):
        signal.signal(signal.SIGINT, self.__exit_gracefully)
        signal.signal(signal.SIGTERM, self.__exit_gracefully)
        self.kill_now = False
        self.lock = threading.RLock()
        self.signal_condition = threading.Condition(self.lock)

    def __exit_gracefully(self, sig_num, frame):
        with self.lock:
            print_threads()
            self.kill_now = True
            self.signal_condition.notify_all()

    def get_kill_now(self):
        """
        Wait before get signal from os
        """
        with self.lock:
            self.signal_condition.wait()
            return self.kill_now

    def get_kill_now_nowait(self):
        """
        Check application status immediately
        """
        return self.kill_now

    def set_kill_immediately(self):
        """
        Set immediately stop mode
        """
        self.kill_now = True
