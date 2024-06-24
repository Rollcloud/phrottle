import utime
from hardware import click_speaker, init_speaker, led
from layout import AbsoluteDirection as facing
from layout import Locomotive
from lever import Lever

REG_MOVE = 70
REG_BRAKE = 30

regulator = Lever(27, max_raw=385, max_out=100, filter_alpha=0.85)  # 362

regulator_position = regulator.read()
print(f"Regulator position: {regulator_position:.0f}%")

if regulator_position > 50:
    print("Starting web server")
    import server  # noqa: F401  # imports server and takes over thread
else:
    print("Using regulator control")

    init_speaker()
    engine = Locomotive(id="test", orientation=facing.LEFT)

    def move_forwards(regulator_position):
        acceleration = (regulator_position - REG_MOVE) / 200
        engine.accelerate(acceleration)

    def move_reverse(regulator_position):
        acceleration = (regulator_position - REG_MOVE) / 200
        engine.accelerate(-acceleration)

    def coast_forwards(regulator_position):
        engine.brake(0.01)

    def coast_reverse(regulator_position):
        engine.brake(0.01)

    def brake_forwards(regulator_position):
        acceleration = (regulator_position - REG_BRAKE) / 150
        engine.brake(abs(acceleration))

    def brake_reverse(regulator_position):
        acceleration = (regulator_position - REG_BRAKE) / 150
        engine.brake(abs(acceleration))

    def stop(regulator_position):
        engine.stop()

    state_machine = {
        # state: (callback, lt, lt_state, gt, gt_state)
        "move_forwards": (move_forwards, REG_MOVE, "coast_forwards", 100, "move_forwards"),
        "move_reverse": (move_reverse, REG_MOVE, "coast_reverse", 100, "move_reverse"),
        "coast_forwards": (coast_forwards, REG_BRAKE, "brake_forwards", REG_MOVE, "move_forwards"),
        "coast_reverse": (coast_reverse, REG_BRAKE, "brake_reverse", REG_MOVE, "move_reverse"),
        "brake_forwards": (brake_forwards, 3, "change_reverse", REG_BRAKE, "coast_forwards"),
        "brake_reverse": (brake_reverse, 3, "change_forwards", REG_BRAKE, "coast_reverse"),
        "change_forwards": (stop, 0, "change_forwards", 5, "brake_forwards"),
        "change_reverse": (stop, 0, "change_reverse", 5, "brake_reverse"),
    }
    state = "change_forwards"

    def herald_transition(new_state):
        if "move" in new_state:
            led.on()
        else:
            led.off()
        click_speaker(t=0.01)

    def run_state_machine(state, regulator_position):
        (callback, lt, lt_state, gt, gt_state) = state_machine[state]
        callback(regulator_position)
        if regulator_position < lt:
            herald_transition(lt_state)
            return lt_state
        if regulator_position > gt:
            herald_transition(gt_state)
            return gt_state
        return state

    try:
        while True:
            regulator_position = regulator.read()

            state = run_state_machine(state, regulator_position)

            print(
                f"state={state}, regulator={regulator_position:.0f}, velocity={engine.velocity:.1f}",
                end="    \r",
            )

            utime.sleep_ms(50)

    except KeyboardInterrupt:
        engine.stop()
