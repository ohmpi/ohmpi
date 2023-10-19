from ohmpi.hardware_components.abstract_hardware_components import PwrAbstract
import numpy as np
import datetime
import os
import time
from ohmpi.utils import enforce_specs
from minimalmodbus import Instrument  # noqa

# hardware characteristics and limitations
SPECS = {'model': {'default': os.path.basename(__file__).rstrip('.py')},
         'voltage': {'default': 12., 'max': 50., 'min': 0.},
         'voltage_min': {'default': 0},
         'voltage_max': {'default': 0},
         'current_max': {'default': 60.},
         'current_adjustable': {'default': False},
         'voltage_adjustable': {'default': True},
         'pwr_latency': {'default': .5}
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
        assert isinstance(self.connection, Instrument)
        # if a controller is passed in kwargs, it will be instantiated
        #if self.ctl is None:
        #    self.ctl = ctl_module.Ctl(**CTL_CONFIG)
        #self.connection = self.ctl.interfaces[kwargs.pop('connection', ctl_connection)]
        self._voltage = kwargs['voltage']
        self._current_max = kwargs['current_max']
        self.voltage_adjustable = True
        self.current_adjustable = False
        self._current = np.nan
        self._pwr_state = 'off'
        self._pwr_latency = kwargs['pwr_latency']
        if not subclass_init:
            self.exec_logger.event(f'{self.model}\tpwr_init\tend\t{datetime.datetime.utcnow()}')

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, value, **kwargs):
        self.exec_logger.debug(f'Current cannot be set on {self.model}')

    def _retrieve_voltage(self):
        self._voltage = self.connection.read_register(0x0002, 2)

    @property
    def voltage(self):
        # return PwrAbstract.voltage.fget(self)
        return self._voltage

    @voltage.setter
    def voltage(self, value):
        self.connection.write_register(0x0000, value, 2)
        self._voltage = value

    def battery_voltage(self):
        self._battery_voltage = self.connection.read_register(0x05, 2)
        return self._battery_voltage

    def current_max(self, value):  # [mA]
        self.connection.write_register(0x0001, hex(int(value)), 0)

    @property
    def pwr_state(self):
        return self._pwr_state

    @pwr_state.setter
    def pwr_state(self, state):
        """Switches pwr on or off.

            Parameters
            ----------
            state : str
                'on', 'off'
            """
        if state == 'on':
            self.connection.write_register(0x09, 1)
            self.current_max(self._current_max)
            print(self._current_max)
            self._pwr_state = 'on'
            self.exec_logger.debug(f'{self.model} is on')
            time.sleep(self._pwr_latency) # from pwr specs

        elif state == 'off':
            self.connection.write_register(0x09, 0)
            self._pwr_state = 'off'
            self.exec_logger.debug(f'{self.model} is off')

    def reload_settings(self):
        # self.voltage(self._voltage)
        self.current_max(self._current_max)
