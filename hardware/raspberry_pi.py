from OhmPi.hardware import ControllerAbstract
import board  # noqa
import busio  # noqa
from OhmPi.utils import get_platform

class Controller(ControllerAbstract):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bus = busio.I2C(board.SCL, board.SDA)  # noqa
        platform, on_pi = get_platform()
        assert on_pi
        self.board_name = platform