import time
from concurrent.futures._base import Future


class ScheduledFuture(Future):
    """
    Future with additional internal parameters
    """

    time = .0
    period = .0

    def get_delay(self) -> float:
        """
        Get remaining delay in seconds (float value),
        zero or negative values indicate that the delay has already elapsed.
        """
        return self.time - time.time()

    def is_periodic(self) -> float:
        """
        Returns True if this is a periodic (not a one-shot) action.
        """
        return self.period != 0
