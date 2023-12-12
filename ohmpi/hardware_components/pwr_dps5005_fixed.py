from ohmpi.hardware_components.abstract_hardware_components import PwrAbstract
import numpy as np
import datetime
import os
import time
from ohmpi.utils import enforce_specs
from minimalmodbus import Instrument  # noqa
from ohmpi.hardware_components.pwr_batt import Pwr as Pwr_batt

# hardware characteristics and limitations
SPECS = {'model': {'default': os.path.basename(__file__).rstrip('.py')},
         'voltage': {'default': 12., 'max': 50., 'min': 0.},
         'voltage_min': {'default': 0},
         'voltage_max': {'default': 0},
         'current_max': {'default': 60.},
         'current_adjustable': {'default': False},
         'voltage_adjustable': {'default': False},
         'pwr_latency': {'default': .5}
         }


class Pwr(Pwr_batt):
    def __init__(self, **kwargs):
        if 'model' not in kwargs.keys():
            for key in SPECS.keys():
                kwargs = enforce_specs(kwargs, SPECS, key)
            subclass_init = False
        else:
            subclass_init = True
        super().__init__(**kwargs)
        if not subclass_init:
            self.exec_logger.event(f'{self.model}\tpwr_init\tbegin\t{datetime.datetime.utcnow()}')
        assert isinstance(self.connection, Instrument)
        self._voltage = kwargs['voltage']
        self._current_max = kwargs['current_max']
        self.voltage_adjustable = False
        self.current_adjustable = False
        self._current = np.nan
        self._pwr_state = 'off'
        self._pwr_latency = kwargs['pwr_latency']
        if not subclass_init:
            self.exec_logger.event(f'{self.model}\tpwr_init\tend\t{datetime.datetime.utcnow()}')
