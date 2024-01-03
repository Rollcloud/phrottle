from machine import Pin, Timer
import utime

LOW_FREQUENCY_PERIOD_MS = 100

up_time = 0  # ms


class RcDetector:
    def calibrate(self, *args):
        # args provided for callback use
        try:
            self.calibration = self.sense_time
        except AttributeError:
            #'RcDetector' object has no attribute 'sense_time'
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
        self.sense_time = utime.ticks_diff(self._stop_time, self._start_time)
        self.sense_time = self._filter(self.sense_time)
        self.read_taken = True

    def __init__(self, pin_number, threshold_us=30, filter_alpha=0.0) -> None:
        """Initialise an RC detector connected to the provided pin"""
        self._pin_number = pin_number
        self._filter_alpha = filter_alpha
        self._sensor = Pin(pin_number, Pin.IN)

        self.threshold_us = threshold_us
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

    def is_present(self) -> bool:
        """Return whether an object is present."""
        try:
            present = self.sense_time <= self.calibration - self.threshold_us
            return present
        except AttributeError:
            #'RcDetector' object has no attribute 'sense_time'
            return False


if __name__ == "__main__":
    led = Pin("LED", Pin.OUT)
    detector = RcDetector(26, threshold_us=5, filter_alpha=0.05)

    def read_sensors(_timer):
        """Take a sensor reading and prep for the next reading."""
        global detector
        # present = detector.is_present()
        # led.value(present)
        detector.perform_read()
        print("-", end="")

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
                print(f"position {idx} is not <= {width}")
        graph[value_pos] = "*"
        return "".join(graph)

    def print_feedback():
        global detector
        present = detector.is_present()
        sense_time = detector.sense_time
        icon = "|" if present else "-" if detector.read_taken else "X"
        graph = draw_graph(
            detector.sense_time,
            scale=0.05,
            rulers=[detector.calibration - detector.threshold_us],
        )
        print(f"{detector.calibration/1000:.3f} {sense_time/1000: 4.3f} ms {icon}{graph}")

    def low_frequency_callback(_timer):
        global detector, up_time
        up_time += LOW_FREQUENCY_PERIOD_MS

        print("*", end="")

        if up_time == 2000:  # ms
            detector.calibrate()

    sensor_timer = Timer()
    sensor_timer.init(mode=Timer.PERIODIC, period=50, callback=read_sensors)

    lf_timer = Timer()
    lf_timer.init(
        mode=Timer.PERIODIC, period=LOW_FREQUENCY_PERIOD_MS, callback=low_frequency_callback
    )

    # while True:
    #     detector.perform_read()
    #     utime.sleep_ms(5)
    #     present = detector.is_present()
    #     led.value(present)
    #     sense_time = detector.sense_time
    #     icon = "|" if present else "-" if detector.read_taken else "X"
    #     graph = draw_graph(
    #         detector.sense_time,
    #         scale=0.05,
    #         rulers=[detector.calibration - detector.threshold_us],
    #     )
    #     print(f"{detector.calibration/1000:.3f} {sense_time/1000: 4.3f} ms {icon}{graph}")

    utime.sleep_ms(500)

    try:
        while True:
            utime.sleep_ms(100)
            # print_feedback()
            print(".", end="")
    except KeyboardInterrupt:
        print("Keyboard exit detected")

    sensor_timer.deinit()
    lf_timer.deinit()
