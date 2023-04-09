from OhmPi.config import HARDWARE_CONFIG
import os
from OhmPi.hardware import MuxAbstract
MUX_CONFIG = HARDWARE_CONFIG['mux']

class Mux(MuxAbstract):
    def __init__(self, **kwargs):
        kwargs.update({'board_name': os.path.basename(__file__).rstrip('.py')})
        super().__init__(**kwargs)
        self.max_elec = MUX_CONFIG['max_elec']