from ohmpi.config import HARDWARE_CONFIG
import os
from ohmpi.hardware_components import CtlAbstract
CTL_CONFIG = HARDWARE_CONFIG['ctl']


class Ctl(CtlAbstract):
    def __init__(self, **kwargs):
        kwargs.update({'model': os.path.basename(__file__).rstrip('.py')})
        super().__init__(**kwargs)
        self.interfaces = dict()

        # None interface for battery
        self.interfaces['none'] = None
        self.interfaces['i2c'] = None
        self.max_cpu_temp = 85.  # °C

    @property
    def _cpu_temp(self):
        return 42
