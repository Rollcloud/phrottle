import utime

from layout import RelativeDirection as rel_dir
from layout import AbsoluteDirection as facing
from layout import Locomotive

engine = Locomotive(orientation=facing.LEFT)


def velocity():
    return engine.velocity


def stop():
    engine.stop()
    print(f"velocity={engine.velocity:.2f} units/s")


def accelerate(direction):
    dir = 1 if direction == rel_dir.FORWARD else -1
    a = 1 if abs(engine.velocity) >= 5 else 5
    a *= dir
    engine.accelerate(a)

    print(f"velocity={engine.velocity:.2f} units/s")


def move(direction):
    dir = 1 if direction == rel_dir.FORWARD else -1
    a = 0.2 * dir
    start_step = 2 * dir

    engine.accelerate(start_step)

    for _ in range(60):
        engine.accelerate(a)
        utime.sleep_ms(10)

    print(f"velocity={engine.velocity:.2f} units/s")

    # print("Coasting")
    # utime.sleep(0.5)

    # print("Stopping")
    # for _ in range(100):
    #     engine.brake()
    #     utime.sleep_ms(10)


# move(dir.FORWARD)
# utime.sleep(2)
# move(dir.REVERSE)

# engine._set_motor(dir.REVERSE, 10)
# utime.sleep(0.5)
# engine.stop()
