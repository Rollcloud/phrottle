from machine import Pin
import utime


class RcDetector:
    def calibrate(self):
        try:
            self.calibration = self._sense_time
        except AttributeError:
            #'RcDetector' object has no attribute '_sense_time'
            pass

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
        self.read_taken = True

    def __init__(self, pin_number, threshold_us=30, filter_alpha=0.0) -> None:
        """
        Initialise an RC detector connected to the provided pin.

        filter_alpha [0.0, 1.0]: lower is stronger
        """
        self._pin_number = pin_number
        self._filter_alpha = filter_alpha
        self._sensor = Pin(pin_number, Pin.IN)

        self.threshold_us = threshold_us
        self.read_taken = False
        self.calibration: float = 0  # us
        # Measure the time for the voltage to decay by waiting for the I/O line to go low.
        self._sensor.irq(handler=self._stop_read, trigger=Pin.IRQ_FALLING)

    def is_calibrated(self) -> bool:
        return self.calibration != 0

    def perform_read(self) -> None:
        """Take a new reading."""
        # Set the I/O line to an output and drive it high.
        self._sensor.init(mode=Pin.OUT, value=1)
        # Allow at least 10 μs for the sensor output to rise.
        utime.sleep_us(50)
        # Make the I/O line an input (high impedance).
        self._sensor.init(mode=Pin.IN)
        self._start_time = utime.ticks_us()
        self.read_taken = False

    def value(self) -> float:
        """Return the detector value in us or zero if no value present."""
        try:
            return self._sense_time
        except AttributeError:
            return 0.0

    def is_present(self) -> bool:
        """Return whether an object is present."""
        try:
            present = self._sense_time <= self.calibration - self.threshold_us
            return present
        except AttributeError:
            #'RcDetector' object has no attribute '_sense_time'
            return False


if __name__ == "__main__":

    class Scheduler:
        def __init__(self, period) -> None:
            self.period = period

            ticks_ms = utime.ticks_ms()
            self._deadline = utime.ticks_add(ticks_ms, self.period)
            self._last = ticks_ms

        def is_ready(self):
            ticks_ms = utime.ticks_ms()
            is_ready = utime.ticks_diff(self._deadline, ticks_ms) <= 0
            if is_ready:
                self.delta = utime.ticks_diff(ticks_ms, self._last)
                self._last = ticks_ms
                self._deadline = utime.ticks_add(ticks_ms, self.period)
            return is_ready

    LOW_FREQUENCY_PERIOD_MS = 31
    SENSORS_PERIOD_MS = 3

    up_time = 0  # ms

    led = Pin("LED", Pin.OUT)
    detector = RcDetector(26, threshold_us=10, filter_alpha=0.1)

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
            zero=int(detector.calibration - 150),
            scale=0.3,
            rulers=[detector.calibration - detector.threshold_us],
        )
        print(f"{detector.calibration/1000:.3f} {detector.value()/1000: 4.3f} ms {icon}{graph}")

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
    calibration_scheduler = Scheduler(3000)

    try:
        while True:
            if sensors_scheduler.is_ready():
                sensors_loop()

            if lf_scheduler.is_ready():
                low_frequency_loop(lf_scheduler.delta)

            if detector.is_calibrated() is False and calibration_scheduler.is_ready():
                detector.calibrate()

    except KeyboardInterrupt:
        print("Keyboard exit detected")
    finally:
        led.off()
