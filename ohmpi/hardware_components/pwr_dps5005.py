from ohmpi.hardware_components.abstract_hardware_components import PwrAbstract
from ohmpi.config import HARDWARE_CONFIG
import importlib
import numpy as np
import os

ctl_name = HARDWARE_CONFIG['ctl'].pop('board_name', 'raspberry_pi_modbus')
ctl_module = importlib.import_module(f'ohmpi.hardware_components.{ctl_name}')

class Pwr(PwrAbstract):
    def __init__(self, **kwargs):
        kwargs.update({'board_name': os.path.basename(__file__).rstrip('.py')})
        voltage = kwargs.pop('voltage', 12.)
        super().__init__(**kwargs)
        if self.ctl is None:
            self.ctl = ctl_module.Ctl()
        self.ctl.bus.configure_modbus()
        self.voltage_adjustable = True
        self._voltage = voltage
        self._current_adjustable = False
        self._current = np.nan
        self._current_max = kwargs.pop('current_max', 100.)

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, value, **kwargs):
        self.exec_logger.debug(f'Current cannot be set on {self.board_name}')

    def turn_off(self):
        self.ctl.bus.write_register(0x09, 1)
        self.exec_logger.debug(f'{self.board_name} is off')

    def turn_on(self):
        self.ctl.bus.write_register(0x09, 1)
        self.exec_logger.debug(f'{self.board_name} is on')

    @property
    def voltage(self):
        return PwrAbstract.voltage.fget(self)

    @voltage.setter
    def voltage(self, value):
        self.ctl.bus.write_register(0x0000, value, 2)
    
    def battery_voltage(self):
        self.ctl.bus.read_register(0x05, 2)

    @property
    def current_max(self,value):
        self.ctl.bus.write_register(0x0001, value * 10, 0)
