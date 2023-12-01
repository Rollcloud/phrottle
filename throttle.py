import utime

from layout import RelativeDirection as dir
from layout import AbsoluteDirection as facing
from layout import Locomotive

engine = Locomotive(orientation=facing.RIGHT)


def move(direction):
    a = 0.2 if direction == dir.FORWARD else -0.2

    print("Accelerating")
    for _ in range(100):
        engine.accelerate(a)
        utime.sleep_ms(10)

    print("Coasting")
    utime.sleep(0.5)

    print("Stopping")
    for _ in range(100):
        engine.brake()
        utime.sleep_ms(10)


move(dir.FORWARD)
utime.sleep(2)
move(dir.REVERSE)

# engine._set_motor(dir.REVERSE, 10)
# utime.sleep(0.5)
# engine.stop()
