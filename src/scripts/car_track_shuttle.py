"""
This script is used to test the shuttle train on the track with wagons.

The script will prompt the user for commands to set the number of wagons on each block,
move the train, and change the point.
The script will also display the state of the sensors and blocks in the console.

Commands:
- SET block_number wagon_count: Set the number of wagons on a block
- PNT 0|1: Change the point to through or diverge
- MOV FWD|BWD block_number wagon_count: Move the train forwards or backwards to a block until a number of wagons are detected
- DIS: Display the state of the sensors and blocks
"""

import gc
import json

import utime
import wifi  # type: ignore
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
from hardware import get_internal_temperature, get_iso_datetime, led, set_rtc_time  # type: ignore
from layout import AbsoluteDirection as Facing  # type: ignore
from umqtt.simple import MQTTClient  # type: ignore

MONITOR = False
MOVEMENT_TIMEOUT = 5000 if MONITOR else 10000  # milliseconds

# Set up the locomotive
loco.orientation = Facing.RIGHT
loco.profile["max_speed"] = 1  # set really slow for shuttle tests
loco.profile["start_step_forward"] = 15
loco.profile["start_step_reverse"] = 7

# Set up the script

is_running = False
stop_when = (-1, 0)

connections = {
    "POINT_BASE_C": (0, 1),  # EOT to Point
    "POINT_THROUGH_C": (1, 2),  # Point to Through route
    "POINT_DIVERGE_C": (1, 3),  # Point to Diverging route
}

# store sensor data
MQTT_BROKER = "192.168.88.117"
qt = MQTTClient("pico", MQTT_BROKER, keepalive=300) if MONITOR else None
timestamps = []
sensor_data = []


def send_sensor_data():
    global timestamps, sensor_data
    num_samples = len(timestamps)
    try:
        qt.connect()
        for timestamp, data in zip(timestamps, sensor_data):
            payload = {"timestamp": timestamp, "temperature": get_internal_temperature()}
            payload.update(data)
            qt.publish(b"paper_wifi/test/phrottle", json.dumps(payload))
        qt.disconnect()
        timestamps = []
        sensor_data = []
        print(f"Sent {num_samples} samples")
    except OSError as e:
        if e.args[0] == 103:
            # connection aborted, server most not available
            timestamps = []
            sensor_data = []
        else:
            raise e


def getBlockEntrySensor(block_number: int, is_moving_left: bool) -> str:
    """Get the sensor key for sensor that will be triggered when the block is entered."""
    connection_index = 0 if is_moving_left else 1
    for key, block_numbers in connections.items():
        if block_numbers[connection_index] == block_number:
            return key

    available_connections = ", ".join(
        map(str, sorted({connection[connection_index] for connection in connections.values()}))
    )
    message = (
        "Block number {number} not found in connections\n"
        "Choose from block numbers: [{options}]\n"
        "Or check locomotive direction"
    )
    raise ValueError(
        message.format(
            number=block_number,
            options=available_connections,
        )
    )


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
    """Wait for a duration in milliseconds before returning True."""
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
    global stop_when, wait_until

    if is_running:
        block_number, wagon_count = stop_when
        block_entry_sensor = getBlockEntrySensor(block_number, is_moving_left)
        if not is_waiting_for(MOVEMENT_TIMEOUT):
            loco.stop()
            print("Move Timed Out")
            send_sensor_data() if MONITOR else None
            is_running = False
        if blocks[block_number] >= wagon_count and not sensors[block_entry_sensor].is_present():
            loco.stop()
            print("Move Completed")
            send_sensor_data() if MONITOR else None
            wait_until = None
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
    wifi.connect_with_saved_credentials(verbose=False)

    led.off()

    print("Track Car Shuttle Test")

    if MONITOR:
        set_rtc_time()

    print("Min trigger interval:", min_trigger_interval, "ms")
    print("Min trigger duration:", min_trigger_duration, "ms")

    try:
        while True:
            loop_start = utime.ticks_ms()
            timestamp = get_iso_datetime()

            is_moving_left = loco.movement_direction() == Facing.LEFT

            is_running = run_train(is_running, is_moving_left, blocks, sensors)

            # Update sensor data
            if MONITOR:
                timestamps.append(timestamp)
                sensor_data.append({})
                sensor_data[-1]["loop_start"] = loop_start

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
                    if MONITOR and is_running:
                        sensor_data[-1][key] = sensors[
                            key
                        ].parent_behaviour.parent_behaviour.detector.value()

            # Show display
            print(display(sensors, blocks), end="")

            # Periodically free memory
            if MONITOR and len(sensor_data) % 50 == 0:
                gc.collect()

            # Loop timing
            loop_end = utime.ticks_ms()
            loop_time = utime.ticks_diff(loop_end, loop_start)
            loop_delay = min_trigger_duration - loop_time

            utime.sleep_ms(max(0, loop_delay))

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
