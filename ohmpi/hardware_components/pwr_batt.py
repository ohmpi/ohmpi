from ohmpi.hardware_components.abstract_hardware_components import PwrAbstract
import numpy as np
import os


class Pwr(PwrAbstract):
    def __init__(self, **kwargs):
        kwargs.update({'board_name': os.path.basename(__file__).rstrip('.py')})
        voltage = kwargs.pop('voltage', 12.)
        super().__init__(**kwargs)
        self.voltage_adjustable = False
        self._voltage = voltage
        self._current_adjustable = False
        self._current = np.nan
        self._state = 'on'

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, value, **kwargs):
        self.exec_logger.debug(f'Current cannot be set on {self.board_name}')

    def turn_off(self):
        self.exec_logger.debug(f'{self.board_name} cannot be turned off')

    def turn_on(self):
        self.exec_logger.debug(f'{self.board_name} is always on')

    @property
    def voltage(self):
        return PwrAbstract.voltage.fget(self)

    @voltage.setter
    def voltage(self, value):
        PwrAbstract.voltage.fset(self, value)