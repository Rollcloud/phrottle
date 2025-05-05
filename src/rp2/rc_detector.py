import utime
from machine import Pin


class RcDetector:
    """A threshold-based detector for an RC sensor."""

    MAX_SENSE_TIME = 15 * 10**3  # us
    RISING_DEBOUNCE = 30 * MAX_SENSE_TIME  # us - min length of train
    FALLING_DEBOUNCE = 10 * MAX_SENSE_TIME  # us - min length of gap

    def calibrate(self):
        if self.value() < RcDetector.MAX_SENSE_TIME:
            self.calibration = self.value()
            self.calibrated = True

    def _filter(self, x) -> float:
        """
        Apply a simple 1st oder filter.

        alpha [0.0, 1.0]: lower is stronger
        """
        alpha = self._filter_alpha
        try:
            y = alpha * x + (1 - alpha) * self.y_last
        except AttributeError:
            # self.y_last not defined
            y = x

        self.y_last = y
        return y

    def _stop_read(self, _pin):
        self._stop_time = utime.ticks_us()
        self._sense_time = utime.ticks_diff(self._stop_time, self._start_time)
        self._sense_time = self._filter(self._sense_time)
        self.read_valid = True

    def __init__(self, gpio_number, threshold_us=30, filter_alpha=0.0) -> None:
        """
        Initialise an RC detector connected to the provided pin.

        filter_alpha [0.0, 1.0]: lower is stronger
        """
        self._gpio_number = gpio_number
        self._filter_alpha = filter_alpha
        self._sensor = Pin(gpio_number, Pin.IN)
        self._rising_callback = None
        self._falling_callback = None
        self.is_debouncing = False
        self._debounce_ticks = utime.ticks_add(utime.ticks_us(), 0)

        self.threshold_us = threshold_us
        self._last_present = (
            False  # convenience attribute, designed to be set from the calling code
        )
        self.read_valid = False
        self.calibrated = False
        self.calibration: float = RcDetector.MAX_SENSE_TIME  # us
        # Measure the time for the voltage to decay by waiting for the I/O line to go low.
        self._sensor.irq(handler=self._stop_read, trigger=Pin.IRQ_FALLING)

    def perform_read(self) -> None:
        """Execute callbacks and take a new reading."""
        # Callbacks and debouncing
        present = self.is_present()
        ticks = utime.ticks_us()
        debounce_ticks = utime.ticks_diff(self._debounce_ticks, ticks)

        if self.is_debouncing is False and present != self._last_present:
            self.is_debouncing = True

        elif self.is_debouncing and debounce_ticks <= 0:
            self._last_present = present
            self.is_debouncing = False

        if present and not self._last_present and debounce_ticks <= 0:
            if self._rising_callback:
                self._rising_callback()
            self._debounce_ticks = utime.ticks_add(ticks, RcDetector.RISING_DEBOUNCE)
            self._last_present = present

        if not present and self._last_present and debounce_ticks <= 0:
            if self._falling_callback:
                self._falling_callback()
            self._debounce_ticks = utime.ticks_add(ticks, RcDetector.FALLING_DEBOUNCE)
            self._last_present = present

        # Set the I/O line to an output and drive it high.
        self._sensor.init(mode=Pin.OUT, value=1)
        # Allow at least 10 μs for the sensor output to rise.
        utime.sleep_us(10)
        # Make the I/O line an input (high impedance).
        self._sensor.init(mode=Pin.IN)
        self._start_time = utime.ticks_us()
        self.read_valid = False

    def value(self) -> float:
        """Return the detector value in us or MAX_SENSE_TIME if no value present."""
        if self.read_valid is False:
            return RcDetector.MAX_SENSE_TIME
        try:
            return self._sense_time
        except AttributeError:
            #'RcDetector' object has no attribute '_sense_time'
            return RcDetector.MAX_SENSE_TIME

    def is_present(self) -> bool:
        """Return whether an object is present."""
        if self.read_valid is False:
            return False

        try:
            present = self._sense_time < self.calibration - self.threshold_us
            return present
        except AttributeError:
            #'RcDetector' object has no attribute '_sense_time'
            return False

    def register_rising_callback(self, callback):
        self._rising_callback = callback

    def register_falling_callback(self, callback):
        self._falling_callback = callback


if __name__ == "__main__":

    class Scheduler:
        """A very simple scheduler that can be used to schedule tasks at regular intervals."""

        def __init__(self, period, one_shot=False) -> None:
            self.period = period
            self.one_shot = one_shot
            self.active = True

            ticks_ms = utime.ticks_ms()
            self._deadline = utime.ticks_add(ticks_ms, self.period)
            self._last = ticks_ms

        def is_ready(self):
            if self.active is False:
                return False

            ticks_ms = utime.ticks_ms()
            is_ready = utime.ticks_diff(self._deadline, ticks_ms) <= 0
            if is_ready:
                self.delta = utime.ticks_diff(ticks_ms, self._last)
                self._last = ticks_ms
                self._deadline = utime.ticks_add(ticks_ms, self.period)
                if self.one_shot:
                    self.active = False
            return is_ready

    LOW_FREQUENCY_PERIOD_MS = 100
    SENSORS_PERIOD_MS = RcDetector.MAX_SENSE_TIME // 1000

    up_time = 0  # ms

    # detectors at 21, 26

    led = Pin("LED", Pin.OUT)
    detector = RcDetector(21, threshold_us=5 * 10**3, filter_alpha=0.1)

    def callback():
        print("Called rising.")

    detector.register_rising_callback(callback)

    def pos(value, scale, zero):
        pos = (value - zero) * scale
        return int(pos)

    def draw_graph(value, scale=1.0, zero=0, rulers=[], width=80):
        value_pos = pos(value, scale, zero)
        ruler_pos = [pos(value, scale, zero) for value in rulers]
        graph = [" "] * width
        for idx in ruler_pos:
            idx = min(width - 1, max(idx, 0))
            graph[idx] = "|"
        value_pos = min(width - 1, max(value_pos, 0))
        graph[value_pos] = "*"
        return "".join(graph)

    def print_feedback():
        global detector
        icon = "+" if detector.is_present() else "-"
        graph = draw_graph(
            detector.value(),
            # zero=int(detector.calibration - 150),
            scale=0.001,
            rulers=[detector.calibration - detector.threshold_us],
        )
        print(
            f"{detector.calibration / 1000: 6.3f} {detector.value() / 1000: 6.3f} ms {icon}{graph}"
        )

    def sensors_loop():
        global detector
        present = detector.is_present()
        led.value(present)
        detector.perform_read()

    def low_frequency_loop(ticks_delta):
        global up_time, detector
        up_time += ticks_delta
        print_feedback()

    sensors_scheduler = Scheduler(SENSORS_PERIOD_MS)
    lf_scheduler = Scheduler(LOW_FREQUENCY_PERIOD_MS)
    # calibration_scheduler = Scheduler(3000, one_shot=True)

    try:
        while True:
            if sensors_scheduler.is_ready():
                sensors_loop()

            if lf_scheduler.is_ready():
                low_frequency_loop(lf_scheduler.delta)

            # if calibration_scheduler.is_ready():
            #     detector.calibrate()

    except KeyboardInterrupt:
        print("Keyboard exit detected")
    finally:
        led.off()
