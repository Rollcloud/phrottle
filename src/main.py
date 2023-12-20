import utime

from layout import AbsoluteDirection as facing
from layout import Locomotive
from lever import Lever
from hardware import flash_led

regulator = Lever(27, max_raw=362, max_out=100, filter_alpha=0.3)

regulator_position = regulator.read()
print(f"Regulator position: {regulator_position:.0f}%")

if regulator_position > 50:
    print("Starting web server")
    import server  # imports server and takes over thread
else:
    print("Using regulator control")

    engine = Locomotive(id="test", orientation=facing.LEFT)
    throttle_split = 50

    def move_forwards(acceleration):
        engine.accelerate(acceleration)

    def move_reverse(acceleration):
        engine.accelerate(acceleration)

    def brake_forwards(acceleration):
        engine.brake(abs(acceleration))

    def brake_reverse(acceleration):
        engine.brake(abs(acceleration))

    def stop(acceleration):
        engine.stop()

    state_machine = {
        # state: (callback, lt, lt_state, gt, gt_state)
        "move_forwards": (move_forwards, 50, "brake_forwards", 100, "move_forwards"),
        "move_reverse": (move_reverse, 0, "move_reverse", 50, "brake_reverse"),
        "brake_forwards": (brake_forwards, 10, "change_reverse", 50, "move_forwards"),
        "brake_reverse": (brake_reverse, 50, "move_reverse", 90, "change_forwards"),
        "change_forwards": (stop, 50, "brake_forwards", 100, "change_forwards"),
        "change_reverse": (stop, 0, "change_reverse", 50, "brake_reverse"),
    }
    state = "change_forwards"

    def run_state_machine(state, regulator_position, acceleration):
        (callback, lt, lt_state, gt, gt_state) = state_machine[state]
        callback(acceleration)
        if regulator_position < lt:
            flash_led()
            return lt_state
        if regulator_position > gt:
            flash_led()
            return gt_state
        return state

    try:
        while True:
            regulator_position = regulator.read()
            throttle = regulator_position - throttle_split
            acceleration = throttle / 200

            state = run_state_machine(state, regulator_position, acceleration)

            print(
                f"state={state}, throttle={throttle:.0f}, velocity={engine.velocity:.1f}", end="\r"
            )

            utime.sleep_ms(50)

    except KeyboardInterrupt:
        engine.stop()
