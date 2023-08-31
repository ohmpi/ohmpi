from ohmpi.config import HARDWARE_CONFIG
import os
from ohmpi.hardware_components import CtlAbstract
CTL_CONFIG = HARDWARE_CONFIG['ctl']


class Ctl(CtlAbstract):
    def __init__(self, **kwargs):
        kwargs.update({'board_name': os.path.basename(__file__).rstrip('.py')})
        super().__init__(**kwargs)
        self.bus = None
