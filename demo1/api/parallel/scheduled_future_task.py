from concurrent.futures._base import PENDING
from typing import Optional

from demo1.api.parallel.execution_local_time_constraint import ExecutionUtcTimeConstraint
from demo1.api.parallel.scheduled_future import ScheduledFuture


class ScheduledFutureTaskEntry(object):
    """
    Tuple of the internal future parameters.
    """

    def __init__(self, trigger_time: float, period: float, sequence_number: int,
                 future: ScheduledFuture, execution_time_constraint: Optional[ExecutionUtcTimeConstraint]) -> None:
        super().__init__()
        self.trigger_time = trigger_time
        self.period = period
        self.sequence_number = sequence_number
        self.future = future
        self.execution_time_constraint = execution_time_constraint


class ScheduledFutureTask(object):
    """
    Basic task for ScheduleThreadPoolExecutor
    """

    def __init__(self,
                 entry: ScheduledFutureTaskEntry,
                 fn, args, kwargs):
        """
        entry is a tuple of the internal feature parameters:


        Period for repeating tasks
         * A positive value indicates fixed-rate execution.
         * A negative value indicates fixed-delay execution.
         * A value of 0 indicates a non-repeating (one-shot) task.
        """
        self.id = self.__identity_or_none(fn and fn.__self__ and hasattr(fn.__self__, 'id') and fn.__self__.id)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

        self.future = entry.future

        self.sequence_number = entry.sequence_number
        self.time = entry.trigger_time
        self.period = entry.period
        self.execution_time_constraint = entry.execution_time_constraint
        self.last_execution_time_constraint = None
        self.heap_index = 0
        self.outer_task = None

        self._refresh_future(entry.trigger_time, entry.period)

    def _refresh_future(self, trigger_time: float, period: float):
        # adjust scheduled time
        self.future.time = trigger_time
        # sync period value with scheduled future
        self.future.period = period

        # reset state instead recreate future, reason: memory issues
        self.future._state = PENDING

    def __eq__(self, other: object) -> bool:
        return self.sequence_number == \
               (other and hasattr(other, 'sequence_number') and getattr(other, 'sequence_number'))

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __le__(self, other: object) -> bool:
        """ Return self<=value. """
        return other and self.__eq__(other) or self.__lt__(other)

    def __lt__(self, other: object) -> bool:
        """ Return self<value. """
        return other and self.time < other.time or (self.time == other.time
                                                    if self.sequence_number < other.sequence_number else False)

    def run(self):
        if not self.future.set_running_or_notify_cancel():
            return

        if self._is_constraint_exists_and_fail():
            return

        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception as exc:
            self.future.set_exception(exc)
            # Break a reference cycle with the exception 'exc'
            self = None
        else:
            self.future.set_result(result)

    def _is_constraint_exists_and_fail(self) -> bool:
        if self.execution_time_constraint:
            if self.execution_time_constraint.can_execute_at_this_moment():
                # Detect first true after false
                if not self.last_execution_time_constraint:
                    self._head_execution()
                self.last_execution_time_constraint = True
                return False
            else:
                # Detect first false after success
                if self.last_execution_time_constraint:
                    self._tail_execution()
                self.last_execution_time_constraint = False
                return True

        return False

    def _head_execution(self):
        if self.execution_time_constraint and self.execution_time_constraint.on_entering_to_constraint:
            try:
                self.execution_time_constraint.on_entering_to_constraint(*self.args, **self.kwargs)
            except Exception as exc:
                self.future.set_exception(exc)
                # Break a reference cycle with the exception 'exc'
                self = None

    def _tail_execution(self):
        if self.execution_time_constraint and self.execution_time_constraint.on_exiting_from_constraint:
            try:
                result = self.execution_time_constraint.on_exiting_from_constraint(*self.args, **self.kwargs)
            except Exception as exc:
                self.future.set_exception(exc)
                # Break a reference cycle with the exception 'exc'
                self = None
            else:
                self.future.set_result(result)

    @staticmethod
    def __identity_or_none(identity: object):
        if isinstance(identity, str):
            return identity
        if isinstance(identity, int):
            return identity
        return None
