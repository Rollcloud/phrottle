import utime
from definitions import (  # type: ignore
    loco,
    min_trigger_duration,
    min_trigger_interval,
    point,
    sensors,
)
from detectors import (  # type: ignore
    BehaviourEvent,
)
from hardware import led  # type: ignore
from layout import AbsoluteDirection as Facing  # type: ignore

loco.profile["max_speed"] = 1  # set really slow for shuttle tests

is_running = False
stop_when = (-1, 0)

connections = {
    "POINT_BASE_C": (0, 1),
    "POINT_THROUGH_C": (1, 2),
    "POINT_DIVERGE_C": (1, 3),
}


def getBlockEntrySensor(block_number: int, is_moving_left: bool) -> str:
    """Get the sensor key for sensor that will be triggered when the block is entered."""
    connection_index = 0 if is_moving_left else 1
    for key, block_numbers in connections.items():
        if block_numbers[connection_index] == block_number:
            return key

    raise ValueError(f"Block number {block_number} not found in connections")


def move_wagon(
    blocks, connections, sensor_key: str, is_triggered: bool, is_moving_left: bool
) -> None:
    """Move a wagon based on the sensor key and trigger state."""
    if is_triggered:
        block_number = connections[sensor_key][0 if is_moving_left else 1]
        blocks[block_number] += 1
    else:
        # is released
        block_number = connections[sensor_key][1 if is_moving_left else 0]
        blocks[block_number] -= 1


def check_and_change_point(diverge=False, toggle=False):
    """Check if there are any wagons on the point and change the point."""
    if (
        blocks[1] > 0
        # or sensors["POINT_BASE_P"].is_present()
        # or sensors["POINT_THROUGH_P"].is_present()
        # or sensors["POINT_DIVERGE_P"].is_present()
    ):
        print("Wagon present, cannot toggle point.")
    else:
        if toggle:
            print("Toggling point")
            point.toggle()
        else:
            print("Changing point to", "diverge" if diverge else "through")
            point.change(diverge)


def display(sensors, blocks):
    """Show a small diagram of sensor states in the console."""
    hide_cursor = "\033[?25l"
    show_cursor = "\033[?25h"
    start_of_previous_line = "\033[F"
    red = "\033[91m"
    reset = "\033[0m"

    sensor_replacements = {
        "A": "EOT_P",
        "B": "POINT_BASE_P",
        "C": "POINT_THROUGH_P",
        "D": "POINT_DIVERGE_P",
    }

    # fmt: off
    track_diagram = (
        "            /C--2--\n"
        "  |A--0--B=1       \n"
        "            \D--3--\n"
    )
    # fmt: on

    block_replacements = [
        red + str(abs(block)) + reset if block < 0 else str(block) for block in blocks
    ]
    # replace digits with {digits} to avoid replacing the same number twice
    track_diagram_format = "".join(
        f"{{{char}}}" if char.isdigit() else char for char in track_diagram
    )

    track_diagram = track_diagram_format.format(*block_replacements)

    for key, sensor_key in sensor_replacements.items():
        track_diagram = track_diagram.replace(key, "!" if sensors[sensor_key].is_present() else ":")

    return "".join(
        [
            hide_cursor,
            track_diagram,
            start_of_previous_line * 3,
            show_cursor,
        ]
    )


blocks = [0, 0, 0, 0]
wait_until = None


def is_waiting_for(duration):
    global wait_until

    if wait_until is None:
        wait_until = utime.ticks_ms() + duration
        return True

    if utime.ticks_diff(wait_until, utime.ticks_ms()) <= 0:
        wait_until = None
        return False

    return True


def run_train(is_running, is_moving_left, blocks, sensors):
    """Shuttle train over the sensor."""
    global stop_when

    if is_running:
        block_number, wagon_count = stop_when
        block_entry_sensor = getBlockEntrySensor(block_number, is_moving_left)
        if blocks[block_number] >= wagon_count and not sensors[block_entry_sensor].is_present():
            loco.stop()
            print("Move Completed")
            is_running = False

    else:
        # Show display
        print(display(sensors, blocks), end="")
        print("\n\n")

        command = input("Enter command [INSTR OBJ param1 param2]:\n").split(" ")

        if command[0].upper() == "SET":
            if len(command) != 3:
                print("Invalid command")
                return
            block_number = int(command[1])
            wagon_count = int(command[2])
            blocks[block_number] = wagon_count
            print("Set block", block_number, "to", wagon_count)

        elif command[0].upper() == "PNT":
            if len(command) != 2:
                print("Invalid command")
                return
            diverge = command[1] == "1"
            check_and_change_point(diverge=diverge)

        elif command[0].upper() == "MOV":
            if len(command) != 4:
                print("Invalid command")
                return
            forwards = command[1].upper() == "FWD"
            loco.accelerate(10 if forwards else -10)  # full speed
            block_number = int(command[2])
            wagon_count = int(command[3])
            stop_when = (block_number, wagon_count)
            print(
                "Moving",
                "forwards" if forwards else "backwards",
                "to block",
                block_number,
                "until",
                wagon_count,
                "wagons are detected",
            )
            is_running = True

        elif command[0].upper() == "DIS":
            stop_when = (0, 1)
            print("Displaying sensors")
            is_running = True

    return is_running


if __name__ == "__main__":
    led.off()

    print("Track Car Shuttle Test")
    print("Min trigger interval:", min_trigger_interval, "ms")
    print("Min trigger duration:", min_trigger_duration, "ms")

    try:
        while True:
            is_moving_left = loco.movement_direction() == Facing.LEFT

            is_running = run_train(is_running, is_moving_left, blocks, sensors)

            # Monitor end of track
            event = sensors["EOT_P"].check_event()
            if is_moving_left and event == BehaviourEvent.TRIGGER:
                loco.stop()
                is_running = False
                print("End of track reached, stopping train")

            # Monitor wagon counters
            for key in sensors:
                if key.endswith("_C"):
                    event = sensors[key].check_event()
                    if event == BehaviourEvent.TRIGGER:
                        move_wagon(blocks, connections, key, True, is_moving_left)
                    elif event == BehaviourEvent.RELEASE:
                        move_wagon(blocks, connections, key, False, is_moving_left)

            # Show display
            print(display(sensors, blocks), end="")

            utime.sleep_ms(min_trigger_duration)

    except KeyboardInterrupt:
        loco.stop()
        point.off()
        led.off()
        print("Train stopped")
    except Exception as e:
        loco.stop()
        point.off()
        led.off()
        print("Train stopped")
        raise e
