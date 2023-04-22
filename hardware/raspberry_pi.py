from OhmPi.hardware import ControllerAbstract
import board  # noqa
import busio  # noqa
from OhmPi.utils import get_platform
from gpiozero import CPUTemperature

class Controller(ControllerAbstract):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bus = busio.I2C(board.SCL, board.SDA)  # noqa
        platform, on_pi = get_platform()
        assert on_pi
        self.board_name = platform
        self._cpu_temp_available = True
        self.max_cpu_temp = 85. # °C

    @property
    def _get_cpu_temp(self):
        return CPUTemperature().temperature