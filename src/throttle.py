import utime

from layout import AbsoluteDirection as facing
from layout import Locomotive
from layout import RelativeDirection as rel_dir

_engine = Locomotive(id="Lourie", orientation=facing.LEFT)


def engine_id():
    return _engine.id


def profile():
    return _engine.profile


def velocity():
    return _engine.velocity


def step():
    return _engine._motor_step


def stop():
    _engine.stop()
    print(f"velocity={_engine.velocity:.2f} units/s")


def accelerate(direction):
    dir = 1 if direction == rel_dir.FORWARD else -1
    a = 1
    a *= dir
    _engine.accelerate(a)

    print(f"velocity={_engine.velocity:.2f} units/s")


def move(direction):
    dir = 1 if direction == rel_dir.FORWARD else -1
    a = 0.2 * dir
    start_step = 2 * dir

    _engine.accelerate(start_step)

    for _ in range(60):
        _engine.accelerate(a)
        utime.sleep_ms(10)

    print(f"velocity={_engine.velocity:.2f} units/s")

    # print("Coasting")
    # utime.sleep(0.5)

    # print("Stopping")
    # for _ in range(100):
    #     _engine.brake()
    #     utime.sleep_ms(10)


# move(dir.FORWARD)
# utime.sleep(2)
# move(dir.REVERSE)

# _engine._set_motor(dir.REVERSE, 10)
# utime.sleep(0.5)
# _engine.stop()
