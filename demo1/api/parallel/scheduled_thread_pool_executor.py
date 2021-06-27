import queue
import sys
import threading
import time
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Optional

from demo1.api.parallel.delayed_queue import DelayedQueue
from demo1.api.parallel.execution_local_time_constraint import ExecutionUtcTimeConstraint
from demo1.api.parallel.scheduled_future import ScheduledFuture
from demo1.api.parallel.scheduled_future_task import ScheduledFutureTask, ScheduledFutureTaskEntry


class Tracker:
    """
    Tracker for tasks in fly, contain to major methods:
    in_fly, on_ground
    """

    def __init__(self, max_workers: Optional[int] = ...) -> None:
        super().__init__()
        self.lock = threading.Lock()
        self.storage = set()

    def in_fly(self, identity):
        if identity is None:
            return
        with self.lock:
            self.storage.add(identity)

    def on_ground(self, identity):
        if identity is None:
            return
        with self.lock:
            self.storage.remove(identity)

    def list_of(self):
        result = list()
        if len(self.storage) == 0:
            return result
        with self.lock:
            for element in self.storage:
                result.append(element)
        return result


class TaskDecorator(ScheduledFutureTask):
    """
    Decorator for scheduled future task, decorate scheduled future task with additional methods,
    which helped to interact with ScheduledThreadPoolExecutor
    """

    def __init__(self, entry: ScheduledFutureTaskEntry, queue: DelayedQueue, tracker: Tracker, fn, args, kwargs):
        super().__init__(entry, fn, args, kwargs)
        self.queue = queue
        self.tracker = tracker

    def run(self):
        try:
            self.tracker.in_fly(self.id)
            super().run()
        finally:
            if self.outer_task and not (self.period == .0):
                # o: ScheduledFutureTask
                self.re_execute_periodic(self.outer_task)
            self.tracker.on_ground(self.id)

    def re_execute_periodic(self, outer_task: ScheduledFutureTask):
        try:
            outer_task.time = self._next_executing_time(outer_task)
            self._refresh_future(outer_task.time, outer_task.period)
            self.queue.put_nowait(outer_task)
        except queue.Full:
            outer_task.time = self._next_executing_time(outer_task)
            self._refresh_future(outer_task.time, outer_task.period)
            while queue.is_not_shutdown():
                try:
                    self.queue.put(outer_task, timeout=1)
                except TimeoutError:
                    continue
                else:
                    break

    def _next_executing_time(self, outer_task):
        if outer_task.period < 0:
            # Fixed delay case
            return time.time() - outer_task.period
        else:
            # Fixed rate case
            return self.time + outer_task.period


class ScheduledThreadPoolExecutor(ThreadPoolExecutor):
    """
    Extension of ThreadPoolExecutor for run periodical and triggered by time tasks
    Storage based on priority queue, see #DelayedQueue class implementation
    """

    def __init__(self, max_workers: Optional[int] = ..., thread_name_prefix: str = ..., max_queue_size: int = 16) \
            -> None:
        if sys.version_info >= (3, 6):
            super().__init__(max_workers, thread_name_prefix)
        else:
            super().__init__(max_workers)

        self._work_queue = DelayedQueue(max_queue_size)
        self._tracker = Tracker(max_workers)

        # SLOW VERSION OF SEQUENCER
        self._sequencer = 0
        self._sequencer_lock = threading.Lock()

    @staticmethod
    def _trigger_time(delay: float) -> float:
        return delay < 0 if 0 else delay

    def _sequence_number(self):
        with self._sequencer_lock:
            self._sequencer += 1
            return self._sequencer

    def _delayed_execute(self, scheduled_future_task: ScheduledFutureTask):
        with self._shutdown_lock:
            if self._shutdown:
                raise RuntimeError('cannot schedule new futures after shutdown')
            while self._work_queue.is_not_shutdown():
                try:
                    self._work_queue.put(scheduled_future_task, 1)
                except TimeoutError:
                    continue
                else:
                    break

            self._adjust_thread_count()

    def _schedule_future(self, delay: float, period: float,
                         execution_utc_time_constraint: Optional[ExecutionUtcTimeConstraint],
                         fn, *args, **kwargs):
        scheduled_future = ScheduledFuture()
        scheduled_future_task = TaskDecorator(
            ScheduledFutureTaskEntry(self._trigger_time(delay), period, self._sequence_number(),
                                     scheduled_future, execution_utc_time_constraint),
            self._work_queue,
            self._tracker,
            fn, args, kwargs)
        scheduled_future_task.outer_task = period == .0 if None else scheduled_future_task

        self._delayed_execute(scheduled_future_task)

        return scheduled_future

    def schedule(self, delay, fn, *args, **kwargs):
        return self._schedule_future(time.time() + delay, 0, None, fn, *args, **kwargs)

    def schedule_at_fixed_rate(self, initial_delay, period, fn, *args, **kwargs):
        return self._schedule_future(time.time() + initial_delay, period, None, fn, *args, **kwargs)

    def constrained_schedule_at_fixed_rate(self, execution_time_constraint: ExecutionUtcTimeConstraint,
                                           initial_delay, period, fn, *args, **kwargs):
        return self._schedule_future(time.time() + initial_delay, period, execution_time_constraint,
                                     fn, *args, **kwargs)

    def schedule_with_fixed_delay(self, initial_delay: float, delay: float, fn, *args, **kwargs):
        return self._schedule_future(time.time() + initial_delay, -delay, None, fn, *args, **kwargs)

    def submit(self, fn, *args, **kwargs):
        """
        Overriding this method for support task priorities
        """
        return self._schedule_future(0, 0, None, fn, *args, **kwargs)

    def in_process_ids(self) -> list:
        """
        For switch on, identity for executing tasks
        add field id for class which is own of the submitting method
        :return:
        """
        result = list()
        # ADD TASKS IN QUEUE
        for task in self._work_queue.queue:
            if task.id:
                result.append(task.id)
        # ADD EXECUTING TASKS
        for identity in self._tracker.list_of():
            result.append(identity)
        return result

    def shutdown(self, wait: bool = True) -> None:
        self._work_queue.shutdown()
        super().shutdown(wait)
