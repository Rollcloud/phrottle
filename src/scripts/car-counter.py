import utime
from detectors import AnalogueDetector, DetectorEvent, AGCDetector, SchmittDetector
from hardware import led

COUNT_THRESHOLD = 50
CLEAR_THRESHOLD = 70
FOUND_THRESHOLD = 90

MAX_SPEED = 300  # mm/s
MIN_WAGON_LENGTH = 25  # 1 inch in mm
REFLECTOR_LENGTH = 5  # mm

min_trigger_interval = int(MIN_WAGON_LENGTH / MAX_SPEED * 1000)  # 83 ms
min_trigger_duration = int(REFLECTOR_LENGTH / MAX_SPEED * 1000)  # 17 ms

detector = AnalogueDetector(28)
agc_detector = AGCDetector(detector, base_threshold=15, gain=0.05)
schmitt_detector = SchmittDetector(
    detector, trigger_threshold=COUNT_THRESHOLD, release_threshold=CLEAR_THRESHOLD
)
counts = 0


if __name__ == "__main__":
    led.off()

    while True:
        led.value(agc_detector.is_present())
        # print(agc_detector.value(), agc_detector.base)

        event = schmitt_detector.is_present(time_hysteresis=min_trigger_interval)
        if event == DetectorEvent.TRIGGER:
            counts += 1
            print(counts, end="")
        elif event == DetectorEvent.RELEASE:
            print(".")

        utime.sleep_ms(min_trigger_duration)
