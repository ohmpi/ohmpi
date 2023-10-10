from ohmpi.hardware_components.abstract_hardware_components import PwrAbstract
import numpy as np
import datetime
import os
from ohmpi.utils import enforce_specs
#import minimalmodbus  # noqa

# hardware characteristics and limitations
SPECS = {'model': {'default': os.path.basename(__file__).rstrip('.py')},
         'voltage': {'default': 12., 'max': 50., 'min': 0.},
         'current_max': {'default': 100.},
         'current_adjustable': {'default': False},
         'voltage_adjustable': {'default': True}
         }

# TODO: Complete this code... handle modbus connection


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
        # if a controller is passed in kwargs, it will be instantiated
        #if self.ctl is None:
        #    self.ctl = ctl_module.Ctl(**CTL_CONFIG)
        #self.connection = self.ctl.interfaces[kwargs.pop('connection', ctl_connection)]
        self._voltage = kwargs['voltage']
        self._current_max = kwargs['current_max']
        self.voltage_adjustable = True
        self.current_adjustable = False
        self._current = np.nan
        if not subclass_init:
            self.exec_logger.event(f'{self.model}\tpwr_init\tend\t{datetime.datetime.utcnow()}')

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, value, **kwargs):
        self.exec_logger.debug(f'Current cannot be set on {self.model}')

    def turn_off(self):
        self.connection.write_register(0x09, 1)
        self.exec_logger.debug(f'{self.model} is off')

    def turn_on(self):
        self.connection.write_register(0x09, 1)
        self.exec_logger.debug(f'{self.model} is on')

    @property
    def voltage(self):
        return PwrAbstract.voltage.fget(self)

    @voltage.setter
    def voltage(self, value):
        self.connection.write_register(0x0000, value, 2)
    
    def battery_voltage(self):
        self.connection.read_register(0x05, 2)

    def current_max(self, value):
        self.connection.write_register(0x0001, value * 10, 0)
