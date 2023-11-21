from ohmpi.ohmpi.config import HARDWARE_CONFIG
import numpy as np
import os
from ohmpi.hardware_components import RxAbstract
RX_CONFIG = HARDWARE_CONFIG['rx']

# hardware characteristics and limitations
# ADC for voltage
voltage_adc_voltage_min = 10.  # mV
voltage_adc_voltage_max = 4500.

RX_CONFIG['voltage_min'] = np.min([voltage_adc_voltage_min, RX_CONFIG.pop('voltage_min', np.inf)])  # mV
RX_CONFIG['voltage_max'] = np.min([voltage_adc_voltage_max, RX_CONFIG.pop('voltage_max', np.inf)])  # mV


class Rx(RxAbstract):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._adc_gain = 1.

    @property
    def adc_gain(self):
        return self._adc_gain

    @adc_gain.setter
    def adc_gain(self, value):
        self.exec_logger.debug(f'Setting RX ADC gain to {value}')

    def adc_gain_auto(self):
        gain = 1.
        self.exec_logger.debug(f'Setting RX ADC gain automatically to {gain}')
        self.adc_gain = gain

    @property
    def voltage(self):
        """ Gets the voltage VMN in Volts
        """
        u = np.random.uniform(-.200,.200) # gets the max between u0 & u2 and set the sign
        self.exec_logger.debug(f'Reading random voltage on RX. Returning {u} V')
        return u