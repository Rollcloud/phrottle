from hardware import TriColourLED

fwd_led = TriColourLED(4, 2, 3)
rev_led = TriColourLED(13, 12, 11)

fwd_led.colour(TriColourLED.WHITE)
rev_led.colour(TriColourLED.WHITE)

try:
    while True:
        pass
except KeyboardInterrupt:
    fwd_led.colour(TriColourLED.OFF)
    rev_led.colour(TriColourLED.OFF)
