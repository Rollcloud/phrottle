import pytest
import layout

mock_hardware = layout.hardware


@pytest.fixture
def locomotive():
    return layout.Locomotive()


class TestLocomotive:
    def test_stop(self, locomotive):
        locomotive.stop()
        assert mock_hardware.motor_off.called
        assert locomotive.velocity == 0
