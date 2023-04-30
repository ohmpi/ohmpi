from OhmPi.hardware_components import ControllerAbstract
import board  # noqa
import busio  # noqa
import os
from OhmPi.utils import get_platform
from gpiozero import CPUTemperature  # noqa

class Controller(ControllerAbstract):
    def __init__(self, **kwargs):
        kwargs.update({'board_name': os.path.basename(__file__).rstrip('.py')})
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