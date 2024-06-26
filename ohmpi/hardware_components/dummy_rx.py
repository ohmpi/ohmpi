from ohmpi.config import HARDWARE_CONFIG
import numpy as np
import os
from ohmpi.hardware_components import RxAbstract
RX_CONFIG = HARDWARE_CONFIG['rx']

# hardware characteristics and limitations
# voltages are given in mV, currents in mA, sampling rates in Hz and data_rate in S/s
SPECS = {'rx': {'model': {'default': os.path.basename(__file__).rstrip('.py')},
                'sampling_rate': {'min': 2., 'default': 10., 'max': 100.},
                'data_rate': {'default': 860.},
                'bias':  {'min': -5000., 'default': 0., 'max': 5000.},
                'coef_p2': {'default': 1.00},
                'mcp_address': {'default': 0x27},
                'ads_address': {'default': 0x49},
                'voltage_min': {'default': 10.0},
                'voltage_max': {'default': 5000.0},  # [mV]
                'dg411_gain_ratio': {'default': 1/2},  # lowest resistor value over sum of resistor values
                'vmn_hardware_offset': {'default': 2500.},
                },
         'tx': {'model': {'default': os.path.basename(__file__).rstrip('.py')},
                'adc_voltage_min': {'default': 10.},  # Minimum voltage value used in vmin strategy
                'adc_voltage_max': {'default': 4500.},  # Maximum voltage on ads1115 used to measure current
                'voltage_max': {'min': 0., 'default': 12., 'max': 50.},  # Maximum input voltage
                'data_rate': {'default': 860.},
                'mcp_address': {'default': 0x21},
                'ads_address': {'default': 0x48},
                'compatible_power_sources': {'default': ['pwr_batt', 'dps5005']},
                'r_shunt':  {'min': 0.001, 'default': 2.},
                'activation_delay': {'default': 0.010},  # Max turn on time of OMRON G5LE-1 5VDC relays
                'release_delay': {'default': 0.005},  # Max turn off time of OMRON G5LE-1 5VDC relays = 1ms
                'pwr_latency': {'default': 4.}
                }}

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
        
    def gain_auto(self):
        self._adc_gain_auto()

    @property
    def voltage(self):
        """ Gets the voltage VMN in Volts
        """
        u = np.random.uniform(-.200,.200) # gets the max between u0 & u2 and set the sign
        self.exec_logger.debug(f'Reading random voltage on RX. Returning {u} V')
        return u