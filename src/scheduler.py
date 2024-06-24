from utime import ticks_add, ticks_diff, ticks_ms


class Scheduler:
    """A simple scheduler that can be used to schedule tasks at regular intervals."""

    def __init__(self, period, one_shot=False) -> None:
        """
        Create a new scheduler.

        Args:
          period: time interval in ms
          one_shot: True to only occur once
        """
        self.period = period
        self.one_shot = one_shot
        self.active = True

        ticks = ticks_ms()
        self._deadline = ticks_add(ticks, self.period)
        self._last = ticks

    def is_ready(self):
        if self.active is False:
            return False

        ticks = ticks_ms()
        is_ready = ticks_diff(self._deadline, ticks) <= 0
        if is_ready:
            self.delta = ticks_diff(ticks, self._last)
            self._last = ticks
            self._deadline = ticks_add(ticks, self.period)
            if self.one_shot:
                self.active = False
        return is_ready
