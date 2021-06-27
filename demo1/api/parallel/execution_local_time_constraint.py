import datetime
from typing import Callable


class ExecutionUtcTimeConstraint(object):
    """
    Constraint for job trigger, if can_work return False, task not executed at current moment
    """

    def __init__(self, inclusion_utc_time_range: tuple = None, delegate: Callable[[], bool] = None) -> None:
        super().__init__()
        self.delegate = delegate
        self.inclusion_utc_time_range = inclusion_utc_time_range
        self.on_exiting_from_constraint = None
        self.on_entering_to_constraint = None

    def can_execute_at_this_moment(self, moment: datetime = None) -> bool:
        if self.delegate:
            return self.delegate()
        # LOCAL TIME CONSTRAINT -> RIGHT DIRECTION
        if self.inclusion_utc_time_range and self.inclusion_utc_time_range[0] <= self.inclusion_utc_time_range[1]:
            dt = moment if moment else datetime.datetime.utcnow()
            time = datetime.time(dt.hour, dt.minute, dt.second, tzinfo=datetime.timezone.utc)
            return self.inclusion_utc_time_range[0] <= time <= self.inclusion_utc_time_range[1]
        # LOCAL TIME CONSTRAINT <- LEFT DIRECTION
        if self.inclusion_utc_time_range and self.inclusion_utc_time_range[0] > self.inclusion_utc_time_range[1]:
            dt = moment if moment else datetime.datetime.utcnow()
            time = datetime.time(dt.hour, dt.minute, dt.second, tzinfo=datetime.timezone.utc)
            return self.inclusion_utc_time_range[0] <= time <= datetime.time(23, 59, 59, 999999,
                                                                             tzinfo=datetime.timezone.utc) or \
                   datetime.time(0, tzinfo=datetime.timezone.utc) <= time <= self.inclusion_utc_time_range[1]
        return True

    def __str__(self) -> str:
        if self.inclusion_utc_time_range:
            return 'local time interval ' + str(self.inclusion_utc_time_range)
        if self.delegate:
            return 'Delegate: ' + str(self.delegate)
        super().__str__()
