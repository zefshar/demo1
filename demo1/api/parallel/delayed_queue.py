import threading
from queue import PriorityQueue, Empty

from demo1.api.parallel.scheduled_future import ScheduledFuture
from demo1.api.parallel.scheduled_future_task import ScheduledFutureTask, ScheduledFutureTaskEntry

FINISH_TASK_FUTURE = ScheduledFuture()
FINISH_TASK_FUTURE.cancel()
FINISH_TASK = ScheduledFutureTask(ScheduledFutureTaskEntry(0, 0, 0, FINISH_TASK_FUTURE, None), max, (1, 2), {})


class DelayedQueue(PriorityQueue):
    """
    Specific tasks storage for ScheduledThreadPoolExecutor,
    implementation based on PriorityQueue
    """

    def __init__(self, maxsize: int = 16) -> None:
        super().__init__(maxsize)
        # Thread designated to wait for the task at the head of the
        # queue.  This variant of the Leader-Follower pattern
        # (http://www.cs.wustl.edu/~schmidt/POSA/POSA2/)
        self.leader = None

        self.lock = threading.RLock()
        # Condition signalled when a newer task becomes available at the
        # head of the queue or a new thread may need to become leader.
        self.available = threading.Condition(self.lock)
        self.__shutdown = False

    def _get(self) -> object:
        with self.available:
            try:
                if self._qsize() == 0:
                    self.available.wait()

                task = super()._get()
                if task == FINISH_TASK:
                    return None

                delay = task.future.get_delay()
                if delay > .0:
                    if self.leader:
                        self.available.wait()
                    else:
                        self.leader = threading.current_thread()
                        try:
                            self.available.wait(delay)
                        finally:
                            if self.leader == threading.current_thread():
                                self.leader = None

                return task
            finally:
                if not self.leader and self._qsize() > 0:
                    self.available.notify_all()

    def _put(self, item: object) -> None:
        with self.available:
            try:
                if not item:
                    super()._put(FINISH_TASK)
                    return
                if self.__shutdown:
                    return
                super()._put(item)
            finally:
                self.available.notify_all()

    def shutdown(self) -> None:
        """
        Notify all waiters for shutdown signal
        """
        with self.lock:
            self.__shutdown = True
            self.available.notify_all()

        if self._qsize() > 0:
            self.queue.clear()
            with self.not_full:
                self.not_full.notify_all()

    def __del__(self):
        self.shutdown()

    def is_not_shutdown(self) -> bool:
        return not self.__shutdown
