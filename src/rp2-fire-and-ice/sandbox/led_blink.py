import time

from machine import Pin

import rp2


@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def blink():
    # fmt: off
    wrap_target()
    set(pins, 1)    [31]
    nop()           [31]
    nop()           [31]
    # nop()           [31]
    # nop()           [31]
    set(pins, 0)    [31]
    nop()           [31]
    nop()           [31]
    # nop()           [31]
    # nop()           [31]
    wrap()
    # fmt: on


sm1 = rp2.StateMachine(0, blink, freq=2400, set_base=Pin(4))
sm2 = rp2.StateMachine(1, blink, freq=4800, set_base=Pin(13))

sm1.active(1)
sm2.active(1)

time.sleep(3)

sm1.active(0)
sm2.active(0)
