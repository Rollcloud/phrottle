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

import utime
import wifi  # type: ignore
from commands import (
    check_and_change_point,
    display,  # type: ignore
    getBlockEntrySensor,
    init_mqtt,
    move_wagon,
    send_sensor_data,
)
from definitions import (
    loco,
    min_trigger_duration,  # type: ignore
    min_trigger_interval,
    point,
    sensors,
)
from detectors import BehaviourEvent  # type: ignore

# type: ignore
from hardware import get_iso_datetime, led, set_rtc_time  # type: ignore
from layout import AbsoluteDirection as Facing  # type: ignore

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
if MONITOR:
    init_mqtt()

timestamps = []
sensor_data = []


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
        block_entry_sensor = getBlockEntrySensor(connections, block_number, is_moving_left)
        if not is_waiting_for(MOVEMENT_TIMEOUT):
            loco.stop()
            print("Move Timed Out")
            send_sensor_data(timestamps, sensor_data) if MONITOR else None
            is_running = False
        if blocks[block_number] >= wagon_count and not sensors[block_entry_sensor].is_present():
            loco.stop()
            print("Move Completed")
            send_sensor_data(timestamps, sensor_data) if MONITOR else None
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
            check_and_change_point(blocks, sensors, diverge=diverge)

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
                        blocks = move_wagon(blocks, connections, key, True, is_moving_left)
                    elif event == BehaviourEvent.RELEASE:
                        blocks = move_wagon(blocks, connections, key, False, is_moving_left)
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
