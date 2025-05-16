from unittest.mock import patch

import pytest

from rp2 import layout

mock_hardware = layout.hardware
Locomotive = layout.Locomotive


@pytest.fixture
def locomotive() -> Locomotive:
    return layout.Locomotive(0)


class TestLocomotive:
    def test_stop(self, locomotive: Locomotive):
        locomotive.stop()
        assert locomotive.velocity == 0
        assert locomotive._motor_step == 0
        mock_hardware.motor_off.assert_called

    @pytest.mark.parametrize(
        ("velocity", "expected_step", "expected_direction"),
        [
            (5, 10, mock_hardware.FORWARD),
            (1, 6, mock_hardware.FORWARD),
            (0, 0, mock_hardware.FORWARD),
            (-1, 6, mock_hardware.REVERSE),
            (-5, 10, mock_hardware.REVERSE),
        ],
    )
    def test_set_motor(self, velocity, expected_step, expected_direction, locomotive: Locomotive):
        locomotive.velocity = velocity
        locomotive.velocity_direction = (
            layout.RelativeDirection.FORWARD if velocity >= 0 else layout.RelativeDirection.REVERSE
        )
        with patch.object(layout.Locomotive, "_set_motor") as mock_set_motor:
            locomotive._set_motor_step()
        assert locomotive._motor_step == expected_step
        assert locomotive._motor_dir == expected_direction
        mock_set_motor.assert_called()

    @pytest.mark.parametrize(
        ("motor_step", "motor_dir", "expected_hardware_call"),
        [
            (5, mock_hardware.FORWARD, mock_hardware.motor_on),
            (1, mock_hardware.FORWARD, mock_hardware.motor_on),
            (0, mock_hardware.FORWARD, mock_hardware.motor_off),
            (1, mock_hardware.REVERSE, mock_hardware.motor_on),
            (5, mock_hardware.REVERSE, mock_hardware.motor_on),
            (-1, mock_hardware.FORWARD, mock_hardware.motor_off),
        ],
    )
    def test_set_motor_step(
        self, motor_step, motor_dir, expected_hardware_call, locomotive: Locomotive
    ):
        locomotive._motor_step = motor_step
        locomotive._motor_dir = motor_dir

        locomotive._set_motor()

        expected_hardware_call.assert_called()

    @pytest.mark.parametrize(
        ("velocity", "acceleration", "expected_velocity"),
        [
            (0, 1, 1),  # 0 >>
            (0, -1, -1),  # 0 <<
            (5, 1, 6),  # -> >>
            (5, -1, 4),  # -> <<
            (-5, -1, -6),  # <- <<
            (-5, 1, -4),  # <- >>
            (120, 1, 100),  # ->> >>
            (-120, -1, -100),  # <<- <<
        ],
    )
    def test_accelerate(self, velocity, acceleration, expected_velocity, locomotive: Locomotive):
        locomotive.velocity = velocity
        with patch.object(layout.Locomotive, "_set_motor_step") as mock_set_motor_step:
            locomotive.accelerate(acceleration)
        assert locomotive.velocity == expected_velocity
        mock_set_motor_step.assert_called()

    def test_brake(self, locomotive: Locomotive):
        locomotive.velocity = 0.13

        with patch.object(layout.Locomotive, "_set_motor_step") as mock_set_motor_step:
            locomotive.brake(0.1)
        assert locomotive.velocity == 0.03
        mock_set_motor_step.assert_called()

        with patch.object(layout.Locomotive, "_set_motor_step") as mock_set_motor_step:
            locomotive.brake(0.1)
        assert locomotive.velocity == 0.00
        mock_set_motor_step.assert_called()
