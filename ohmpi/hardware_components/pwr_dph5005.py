from ohmpi.hardware_components.abstract_hardware_components import PwrAbstract
import numpy as np
import datetime
import os
import time
from ohmpi.utils import enforce_specs
from minimalmodbus import Instrument  # noqa

# hardware characteristics and limitations
SPECS = {'model': {'default': os.path.basename(__file__).rstrip('.py')},
         'voltage': {'default': 5., 'max': 50., 'min': 0.},  # V
         'voltage_min': {'default': 0},  # V
         'voltage_max': {'default': 50.99},  # V
         'power_max': {'default': 2.5},  # W
         'current_max': {'default': 0.050},  # A
         'current_overload': {'default': 0.060},  # A
         'current_max_tolerance': {'default': 20},  # in %
         'current_adjustable': {'default': False},
         'voltage_adjustable': {'default': True},
         'pwr_latency': {'default': 4.},
         'pwr_discharge_latency': {'default': 1.},
         'pwr_accuracy': {'default': 1},  # V
         'interface_name': {'default': 'modbus'}
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
        self._current_max = kwargs['current_max']
        self._current_overload = kwargs['current_overload']
        self._voltage_max = kwargs['voltage_max']
        self._power_max = kwargs['power_max']
        self._current_max_tolerance = kwargs['current_max_tolerance']
        self.voltage_adjustable = True
        self.current_adjustable = False
        self._current = np.nan
        self._pwr_latency = kwargs['pwr_latency']
        self._pwr_discharge_latency = kwargs['pwr_discharge_latency']
        self._pwr_accuracy = kwargs['pwr_accuracy']
        self._pwr_state = 'off'
        if self.connect:
            if self.interface_name == 'modbus':
                assert isinstance(self.connection, Instrument)
            elif self.interface_name == 'bluetooth':
                raise Warning('Bluetooth communication with dph5050 is not implemented')
            elif self.interface_name == 'none':
                raise IOError('dph interface cannot be set to none')

        if not subclass_init:
            self.exec_logger.event(f'{self.model}\tpwr_init\tend\t{datetime.datetime.utcnow()}')

    def _retrieve_current(self):
        self._current = self.connection.read_register(0x0003, 2) * 100  # in mA (not sure why but value from DPS comes in [A*10]

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
        value = float(value)
        if value >= self._voltage_max:
            value = self._voltage_max
        if value <= self._voltage_min:
            value = self._voltage_min
        assert self._voltage_min <= value <= self._voltage_max
        self.exec_logger.event(f'{self.model}\tset_voltage\tbegin\t{datetime.datetime.utcnow()}')
        if value != self._voltage:
            self.connection.write_register(0x0000, np.round(value, 2), 2)
            if self._pwr_state == 'on' and self._pwr_accuracy > 0:
                for i in range(50):
                    self._retrieve_voltage()
                    if np.abs(self._voltage - value) < self._pwr_accuracy:  # arbitrary threshold
                        break
            # TODO: @Watlet, could you justify this formula?
#            time.sleep(max([0,1 - (self._voltage/value)]))  # NOTE: wait to enable DPS to reach new voltage as a function of difference between new and previous voltage
        self.exec_logger.event(f'{self.model}\tset_voltage\tend\t{datetime.datetime.utcnow()}')
        self._voltage = value

    def voltage_default(self, value):  # [A]
        self.connection.write_register(0x0050, np.round(value, 2), 2)

    @property
    def voltage_max(self):
        return self._voltage_max

    @voltage_max.setter
    def voltage_max(self, value):  # [V]
        if value >= 51.:  # DPS 5005 maximum accepted value
            value = 50.99
        self.connection.write_register(0x0052, np.round(value, 2), 2)
        self._voltage_max = value

    def battery_voltage(self):
        self._battery_voltage = self.connection.read_register(0x05, 2)
        return self._battery_voltage

    @property
    def current_max(self):
        return self._current_max

    @current_max.setter
    def current_max(self, value):
        new_value = value * (
                    1 + self._current_max_tolerance / 100)  # To set DPS max current slightly above (20% by default) the limit to avoid regulation artefacts
        self.connection.write_register(0x0001, np.round(new_value, 3), 3)
        self._current_max = value

    @property
    def current_overload(self):
        return self._current_overload

    @current_max.setter
    def current_overload(self, value):
        self.connection.write_register(0x0053, np.round(value, 3), 3)
        self._current_overload = value

    def current_max_default(self, value):  # [A]
        new_value = value * (
                    1 + self._current_max_tolerance / 100)  # To set DPS max current slightly above (20% by default) the limit to avoid regulation artefacts
        self.connection.write_register(0x0051, np.round((new_value), 3), 3)

    def power_max(self, value):  # [W]
        self.connection.write_register(0x0054, np.round(value,1), 1)

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
            if self._pwr_state != 'on':
                self.exec_logger.event(f'{self.model}\tpwr_state_on\tbegin\t{datetime.datetime.utcnow()}')
                self.connection.write_register(0x09, 1)
                self.exec_logger.event(f'{self.model}\tpwr_state_on\tend\t{datetime.datetime.utcnow()}')
                # self.current_max(self._current_max)
                self._pwr_state = 'on'
                # self.exec_logger.event(f'{self.model}\tpwr_latency\tbegin\t{datetime.datetime.utcnow()}')
                # time.sleep(self._pwr_latency)
                # self.exec_logger.event(f'{self.model}\tpwr_latency\tend\t{datetime.datetime.utcnow()}')
            self.exec_logger.debug(f'{self.model} is on')

        elif state == 'off':
            if self._pwr_state != 'off':
                self.exec_logger.event(f'{self.model}\tpwr_state_off\tbegin\t{datetime.datetime.utcnow()}')
                self.connection.write_register(0x09, 0)
                self._pwr_state = 'off'
                self.exec_logger.event(f'{self.model}\tpwr_state_off\tend\t{datetime.datetime.utcnow()}')
            self.exec_logger.debug(f'{self.model} is off')

    def reload_settings(self):
        self.voltage_default(self._voltage)
        self.voltage_max = self._voltage_max
        self.current_max_default(self._current_max)
        self.current_max = self._current_max
        self.current_overload = self._current_overload #np.max([self._current_max,self._current_overload]) # TODO: np.max could be placed in current_overload setter
        self.power_max(self._power_max)
