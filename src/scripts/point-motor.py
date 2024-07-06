import utime
from lib.SimplyRobotics import SimplePWMMotor  # type: ignore

FORWARD = "f"
REVERSE = "r"

motor = SimplePWMMotor(4, 3, 100)

print("Motor on")


try:
    while True:
        command = input("Enter [T]hrough, [D]iverge, or [Q]uit: ").lower()

        if command not in ["t", "d", "q"]:
            print("Invalid command")
            continue  # Skip the rest of the loop and ask for input again

        if command == "t":
            print("Moving through")
            motor.on(FORWARD, 100)
        elif command == "d":
            print("Moving diverge")
            motor.on(REVERSE, 100)
        elif command == "q":
            print("Quitting")
            motor.off()
            break

        utime.sleep(3)  # Wait for 3 seconds to complete the movement

except KeyboardInterrupt:
    motor.off()
    print("Stopped")
except Exception as e:
    motor.off()
    print("Stopped")
    print("Error: ", e)
