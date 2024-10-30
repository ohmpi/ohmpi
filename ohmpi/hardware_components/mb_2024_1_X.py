import datetime
import adafruit_ads1x15.ads1115 as ads  # noqa
from adafruit_ads1x15.analog_in import AnalogIn  # noqa
from adafruit_ads1x15.ads1x15 import Mode  # noqa
from adafruit_mcp230xx.mcp23008 import MCP23008  # noqa
from digitalio import Direction  # noqa
from busio import I2C  # noqa
import os
import time
from ohmpi.utils import enforce_specs
from ohmpi.hardware_components.mb_2024_0_2 import Tx as Tx_mb_2024_0_2
from ohmpi.hardware_components.mb_2024_0_2 import Rx as Rx_mb_2024_0_2

# hardware characteristics and limitations
# voltages are given in mV, currents in mA, sampling rates in Hz and data_rate in S/s
SPECS = {'rx': {'model': {'default': os.path.basename(__file__).rstrip('.py')},
                'sampling_rate': {'min': 0., 'default': 100., 'max': 500.},
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
                }}

# TODO: move low_battery spec in pwr


def _ads_1115_gain_auto(channel):  # Make it a class method ?
    """Automatically sets the gain on a channel

    Parameters
    ----------
    channel : ads.ADS1x15
        Instance of ADS where voltage is measured.

    Returns
    -------
    gain : float
        Gain to be applied on ADS1115.
    """

    gain = 2 / 3
    if (abs(channel.voltage) < 2.048) and (abs(channel.voltage) >= 1.024):
        gain = 2
    elif (abs(channel.voltage) < 1.024) and (abs(channel.voltage) >= 0.512):
        gain = 4
    elif (abs(channel.voltage) < 0.512) and (abs(channel.voltage) >= 0.256):
        gain = 8
    elif abs(channel.voltage) < 0.256:
        gain = 16
    return gain


class Tx(Tx_mb_2024_0_2):
    """TX Class"""
    def __init__(self, **kwargs):
        if 'model' not in kwargs.keys():
            for key in SPECS['tx'].keys():
                kwargs = enforce_specs(kwargs, SPECS['tx'], key)
            subclass_init = False
        else:
            subclass_init = True
        super().__init__(**kwargs)
        if not subclass_init:
            self.exec_logger.event(f'{self.model}\ttx_init\tbegin\t{datetime.datetime.utcnow()}')

        if self.connect:
            self.pin5 = self.mcp_board.get_pin(5)  # power_discharge_relay
            self.pin5.direction = Direction.OUTPUT
            self.pin5.value = False

        if not subclass_init:
            self.exec_logger.event(f'{self.model}\ttx_init\tend\t{datetime.datetime.utcnow()}')

    @property
    def measuring(self):
        return self._measuring

    @measuring.setter
    def measuring(self, mode="off"):
        self._measuring = mode

    def discharge_pwr(self, latency=None):
        if self.pwr.voltage_adjustable:
            if latency is None:
                latency = self.pwr._pwr_discharge_latency
            self.exec_logger.debug(f'Pwr discharge initiated for {latency} s')

            self.exec_logger.event(f'{self.model}\tpwr_discharge\tend\t{datetime.datetime.utcnow()}')
            self.pin5.value = True
            time.sleep(self._activation_delay)

            time.sleep(latency)

            if self.pwr.voltage_adjustable:
                self.pin5.value = False
                time.sleep(self._release_delay)
            self.exec_logger.event(f'{self.model}\tpwr_discharge\tend\t{datetime.datetime.utcnow()}')
        else:
            self.exec_logger.debug(f'Pwr discharge not supported by {self.pwr.model}')


class Rx(Rx_mb_2024_0_2):
    """RX Class"""
    def __init__(self, **kwargs):
        if 'model' not in kwargs.keys():
            for key in SPECS['rx'].keys():
                kwargs = enforce_specs(kwargs, SPECS['rx'], key)
            subclass_init = False
        else:
            subclass_init = True
        super().__init__(**kwargs)
        if not subclass_init:
            self.exec_logger.event(f'{self.model}\trx_init\tbegin\t{datetime.datetime.utcnow()}')

        if not subclass_init:
            self.exec_logger.event(f'{self.model}\trx_init\tend\t{datetime.datetime.utcnow()}')
