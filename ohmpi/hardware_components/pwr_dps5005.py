from ohmpi.hardware_components.abstract_hardware_components import PwrAbstract
from ohmpi.config import HARDWARE_CONFIG
import importlib
import numpy as np
import minimalmodbus  # noqa
import os

CTL_CONFIG = HARDWARE_CONFIG['ctl']
ctl_name = HARDWARE_CONFIG['ctl'].pop('board_name', 'raspberry_pi')
ctl_connection = HARDWARE_CONFIG['ctl'].pop('connection', 'modbus')
ctl_module = importlib.import_module(f'ohmpi.hardware_components.{ctl_name}')
CTL_CONFIG['baudrate'] = CTL_CONFIG.pop('baudrate', 9600)
CTL_CONFIG['bitesize'] = CTL_CONFIG.pop('bitesize', 8)
CTL_CONFIG['timeout'] = CTL_CONFIG.pop('timeout', 1)
CTL_CONFIG['debug'] = CTL_CONFIG.pop('debug', False)
CTL_CONFIG['parity'] = CTL_CONFIG.pop('parity', 'N')
CTL_CONFIG['mode'] = CTL_CONFIG.pop('mode', minimalmodbus.MODE_RTU)
CTL_CONFIG['port'] = CTL_CONFIG.pop('port', '/dev/ttyUSB0')
CTL_CONFIG['slave_address'] = CTL_CONFIG.pop('slave_address', 1)


class Pwr(PwrAbstract):
    def __init__(self, **kwargs):
        kwargs.update({'board_name': os.path.basename(__file__).rstrip('.py')})
        voltage = kwargs.pop('voltage', 12.)
        super().__init__(**kwargs)
        # if a controller is passed in kwargs, it will be instantiated
        if self.ctl is None:
            self.ctl = ctl_module.Ctl(**CTL_CONFIG)
        self.connection = self.ctl.interfaces[kwargs.pop('connection', ctl_connection)]
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

    @property
    def current_max(self,value):
        self.connection.write_register(0x0001, value * 10, 0)
