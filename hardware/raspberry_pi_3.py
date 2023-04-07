from hardware import ControllerAbstract
import board  # noqa
import busio  # noqa

class Controller(ControllerAbstract):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bus = busio.I2C(board.SCL, board.SDA)  # noqa