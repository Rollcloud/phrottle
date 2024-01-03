from machine import Pin
import utime


class RcDetector:
    def calibrate(self, *args):
        # args provided for callback use
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
        """Initialise an RC detector connected to the provided pin"""
        self._pin_number = pin_number
        self._filter_alpha = filter_alpha
        self._sensor = Pin(pin_number, Pin.IN)

        self.threshold_us = threshold_us
        self.read_taken = False
        self.calibration = 0  # us
        # Measure the time for the voltage to decay by waiting for the I/O line to go low.
        self._sensor.irq(handler=self._stop_read, trigger=Pin.IRQ_FALLING)

    def perform_read(self) -> None:
        """Take a new reading."""
        # Set the I/O line to an output and drive it high.
        self._sensor.init(mode=Pin.OUT, value=1)
        # Allow at least 10 μs for the sensor output to rise.
        utime.sleep_us(15)
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
    LOW_FREQUENCY_PERIOD_MS = 100
    SENSORS_PERIOD_MS = 5

    up_time = 0  # ms
    is_lf_loop_ready = False
    is_sensors_loop_ready = False

    led = Pin("LED", Pin.OUT)
    detector = RcDetector(26, threshold_us=5, filter_alpha=0.05)

    def pos(value, scale, zero):
        pos = (value - zero) * scale
        return int(pos)

    def draw_graph(value, scale=1.0, zero=0, rulers=[], width=80):
        value_pos = pos(value, scale, zero)
        ruler_pos = [pos(value, scale, zero) for value in rulers]
        graph = [" "] * width
        for idx in ruler_pos:
            try:
                graph[idx] = "|"
            except IndexError as err:
                print(f"Ruler position {idx} is not <= {width}")
                raise err
        try:
            graph[value_pos] = "*"
        except IndexError as err:
            print(f"Value position {value_pos} is not <= {width}")
            raise err
        return "".join(graph)

    def print_feedback():
        global detector
        present = detector.is_present()
        icon = "|" if present else "-"  # if detector.read_taken else "X"
        graph = draw_graph(
            detector.value(),
            scale=0.05,
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

        if up_time >= 2000 and detector.calibration == 0.0:  # ms
            detector.calibrate()

        print_feedback()
        # print(up_time)

    try:
        ticks_last = utime.ticks_ms()
        sensors_loop_deadline = ticks_last
        lf_loop_deadline = ticks_last
        while True:
            ticks_ms = utime.ticks_ms()

            if utime.ticks_diff(sensors_loop_deadline, ticks_ms) < 0:
                is_sensors_loop_ready = True

            if utime.ticks_diff(lf_loop_deadline, ticks_ms) < 0:
                is_lf_loop_ready = True

            if is_sensors_loop_ready:
                sensors_loop()
                is_sensors_loop_ready = False
                sensors_loop_deadline = utime.ticks_add(ticks_ms, SENSORS_PERIOD_MS)

            if is_lf_loop_ready:
                ticks_delta = utime.ticks_diff(ticks_ms, ticks_last)
                ticks_last = ticks_ms
                low_frequency_loop(ticks_delta)
                is_lf_loop_ready = False
                lf_loop_deadline = utime.ticks_add(ticks_ms, LOW_FREQUENCY_PERIOD_MS)

    except KeyboardInterrupt:
        print("Keyboard exit detected")
