from ohmpi.hardware_components.abstract_hardware_components import PwrAbstract
import numpy as np
import datetime
import os
import time
from ohmpi.utils import enforce_specs
from minimalmodbus import Instrument  # noqa

# hardware characteristics and limitations
SPECS = {'model': {'default': os.path.basename(__file__).rstrip('.py')},
         'voltage': {'default': 5., 'max': 50., 'min': 0.},
         'voltage_min': {'default': 0}, # V
         'voltage_max': {'default': 50}, # V
         'power_max': {'default': 2.5}, # W
         'current_max': {'default': 0.050}, # mA
         'current_max_tolerance': {'default': 20}, # in %
         'current_adjustable': {'default': False},
         'voltage_adjustable': {'default': True},
         'pwr_latency': {'default': .5}
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
        assert isinstance(self.connection, Instrument)
        self._voltage = kwargs['voltage']
        self._current_max = kwargs['current_max']
        self._voltage_max = kwargs['voltage_max']
        self._power_max = kwargs['voltage_max']
        self._current_max_tolerance = kwargs['current_max_tolerance']
        # self.current_max = self._current_max
        # self.voltage_max(self._voltage_max)
        # self.power_max(self._power_max)
        self.voltage_adjustable = True
        self.current_adjustable = False
        self._current = np.nan
        self._pwr_state = 'off'
        self._pwr_latency = kwargs['pwr_latency']
        if not subclass_init:
            self.exec_logger.event(f'{self.model}\tpwr_init\tend\t{datetime.datetime.utcnow()}')

    def _retrieve_current(self):
        self._current = self.connection.read_register(0x0003, 2) * 100  # in mA (not sure why but value from DPS comes in [A*10]

    # @property
    # def current(self):
    #     return self._current
    #
    # @current.setter
    # def current(self, value, **kwargs):
    #     self.exec_logger.debug(f'Current cannot be set on {self.model}')

    def _retrieve_voltage(self):
        self._voltage = self.connection.read_register(0x0002, 2)

    @property
    def voltage(self):
        # return PwrAbstract.voltage.fget(self)
        return self._voltage

    @voltage.setter
    def voltage(self, value):
        self.connection.write_register(0x0000, np.round(value, 2), 2)
        self._voltage = value

    def battery_voltage(self):
        self._battery_voltage = self.connection.read_register(0x05, 2)
        return self._battery_voltage

    # @current_max.setter
    # def current_max(self, value):  # [mA]
    #     new_value = value * (1 + self._current_max_tolerance / 100)  # To set DPS max current slightly above (20% by default) the limit to avoid regulation artefacts
    #     self.connection.write_register(0x0001, np.round((new_value * 1000), 3), 0)
    #     self._current_max = value
    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, value, **kwargs):
        value = value  # To set DPS max current slightly above (20%) the limit to avoid regulation artefacts
        self.connection.write_register(0x0001, int(value * 1000), 0)
        self._current = value
        # self.exec_logger.debug(f'Current cannot be set on {self.model}')

    @property
    def current_max(self):
        return self._current_max

    @current_max.setter
    def current_max(self, value):  # [mA]
        print(value)
        new_value = value * (1 + self._current_max_tolerance / 100)  # To set DPS max current slightly above (20% by default) the limit to avoid regulation artefacts
        self.connection.write_register(0x0053, np.round((new_value * 1000), 3), 0)
        self._current_max = value

    def voltage_max(self, value):  # [V]
        print(value)
        new_value = value * (1 + self._current_max_tolerance / 100)# To set DPS max current slightly above (20%) the limit to avoid regulation artefacts
        self.connection.write_register(0x0052, int(new_value), 0)

    def power_max(self, value):  # [W]
        value = value * 1.2  # To set DPS max current slightly above (20%) the limit to avoid regulation artefacts
        self.connection.write_register(0x0054, int(value), 0)

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
            self.current_max = self._current_max
            self._pwr_state = 'on'
            self.exec_logger.debug(f'{self.model} is on')
            time.sleep(self._pwr_latency)

        elif state == 'off':
            self.connection.write_register(0x09, 0)
            self._pwr_state = 'off'
            self.exec_logger.debug(f'{self.model} is off')

    def reload_settings(self):
        self.current_max = self._current_max
