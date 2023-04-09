from OhmPi.config import HARDWARE_CONFIG
import os
from OhmPi.hardware import ControllerAbstract
CONTROLLER_CONFIG = HARDWARE_CONFIG['controller']


class Controller(ControllerAbstract):
    def __init__(self, **kwargs):
        kwargs.update({'board_name': os.path.basename(__file__).rstrip('.py')})
        super().__init__(**kwargs)
        self.bus = None