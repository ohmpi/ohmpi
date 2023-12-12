from ohmpi.hardware_components.abstract_hardware_components import PwrAbstract
import numpy as np
import datetime
import os
from ohmpi.utils import enforce_specs

# hardware characteristics and limitations
SPECS = {'model': {'default': os.path.basename(__file__).rstrip('.py')},
         'voltage': {'default': 12., 'max': 12., 'min': 12.},
         'current_adjustable': {'default': False},
         'voltage_adjustable': {'default': False},
         'interface': {'default': 'none'},
         }


class Pwr(PwrAbstract):
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
        self._voltage = kwargs['voltage']
        self._current = np.nan
        self._switch_pwr_on_zero = True
        # self._state = 'on'
        if not subclass_init:
            self.exec_logger.event(f'{self.model}\tpwr_init\tend\t{datetime.datetime.utcnow()}')

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, value, **kwargs):
        self.exec_logger.debug(f'Current cannot be set on {self.model}')

    @property
    def voltage(self):
        return PwrAbstract.voltage.fget(self)

    @voltage.setter
    def voltage(self, value):
        PwrAbstract.voltage.fset(self, value)

    def voltage_pulse(self, voltage=0., length=None, polarity=1):
        self.voltage_pulse(voltage=voltage, length=length, polarity=polarity, switch_pwr=self._switch_pwr_on_zero)

    def inject(self, polarity=1, injection_duration=None):
        self.inject(polarity=polarity, injection_duration=injection_duration, switch_pwr=self._switch_pwr_on_zero)
