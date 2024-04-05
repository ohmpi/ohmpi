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
from ohmpi.hardware_components.mb_2023_0_X import Tx as Tx_mb_2023
from ohmpi.hardware_components.mb_2023_0_X import Rx as Rx_mb_2023

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


class Tx(Tx_mb_2023):
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

        # Initialize LEDs
        if self.connect:
            self.pin4 = self.mcp_board.get_pin(4)  # OhmPi_run
            self.pin4.direction = Direction.OUTPUT
            self.pin4.value = True
            self.pin5 = self.mcp_board.get_pin(5)  # OhmPi_measure
            self.pin5.direction = Direction.OUTPUT
            self.pin5.value = False
            self.pin6 = self.mcp_board.get_pin(6)  # OhmPi_stack
            self.pin6.direction = Direction.OUTPUT
            self.pin6.value = False

            # Initialize DPS relays
            self.pin2 = self.mcp_board.get_pin(2)  # dps -
            self.pin2.direction = Direction.OUTPUT
            self.pin2.value = False
            self.pin3 = self.mcp_board.get_pin(3)  # dps -
            self.pin3.direction = Direction.OUTPUT
            self.pin3.value = False

        if not subclass_init:
            self.exec_logger.event(f'{self.model}\ttx_init\tend\t{datetime.datetime.utcnow()}')

    @property
    def measuring(self):
        return self._measuring

    @measuring.setter
    def measuring(self, mode="off"):
        self._measuring = mode
        if mode == "on":
            self.pin5.value = True
        elif mode == "off":
            self.pin5.value = False

    def inject(self, polarity=1, injection_duration=None):
        # add leds?
        self.pin6.value = True
        Tx_mb_2023.inject(self, polarity=polarity, injection_duration=injection_duration)
        self.pin6.value = False

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
            self.exec_logger.event(f'{self.model}\ttx_pwr_state_on\tbegin\t{datetime.datetime.utcnow()}')
            self.pin2.value = True
            self.pin3.value = True
            self.exec_logger.debug(f'Switching DPS on')
            self._pwr_state = 'on'
            time.sleep(self.pwr._pwr_latency) # from pwr specs
            self.pwr.pwr_state = 'off'
            self.pwr.reload_settings()
            self.exec_logger.event(f'{self.model}\ttx_pwr_state_on\tend\t{datetime.datetime.utcnow()}')
            self.pwr.battery_voltage()
            if self.pwr.voltage_adjustable:
                if self.pwr._battery_voltage < 11.8:
                    self.exec_logger.warning(f'TX Battery voltage from {self.pwr.model} = {self.pwr._battery_voltage} V')
                else:
                    self.exec_logger.info(f'TX Battery voltage from {self.pwr.model} = {self.pwr._battery_voltage} V')

        elif state == 'off':
            self.exec_logger.event(f'{self.model}\ttx_pwr_state_off\tbegin\t{datetime.datetime.utcnow()}')
            self.pwr.pwr_state = 'off'
            self.pin2.value = False
            self.pin3.value = False
            self.exec_logger.debug(f'Switching DPS off')
            self._pwr_state = 'off'
            self.exec_logger.event(f'{self.model}\ttx_pwr_state_off\tend\t{datetime.datetime.utcnow()}')

    def current_pulse(self, current=None, length=None, polarity=1):
        """ Generates a square current pulse. Currenttly no DPS can handle this...

        Parameters
        ----------
        voltage: float, optional
            Voltage to apply in volts, tx_v_def is applied if omitted.
        length: float, optional
            Length of the pulse in seconds
        polarity: 1,0,-1
            Polarity of the pulse
        """
        self.exec_logger.event(f'{self.model}\ttx_current_pulse\tbegin\t{datetime.datetime.utcnow()}')
        # self.exec_logger.info(f'injection_duration: {length}')  # TODO: delete me
        if length is None:
            length = self.injection_duration
        if current is not None:
            self.pwr.current = current
        self.exec_logger.debug(f'Current pulse of {polarity*self.pwr.current:.3f} V for {length:.3f} s')
        self.inject(polarity=polarity, injection_duration=length)
        self.exec_logger.event(f'{self.model}\ttx_current_pulse\tend\t{datetime.datetime.utcnow()}')

    @property
    def polarity(self):
        return self._polarity

    @Tx_mb_2023.polarity.setter
    def polarity(self, polarity):
        assert polarity in [-1, 0, 1]
        self._polarity = polarity
        if polarity == 1:
            if not self.pwr.voltage_adjustable:
                self.pwr_state = 'on'
            self.pin0.value = True
            self.pin1.value = False
            time.sleep(self._activation_delay)
        elif polarity == -1:
            if not self.pwr.voltage_adjustable:
                self.pwr_state = 'on'
            self.pin0.value = False
            self.pin1.value = True
            time.sleep(self._activation_delay)
        else:
            if not self.pwr.voltage_adjustable:
                self.pwr_state = 'off'
            self.pin0.value = False
            self.pin1.value = False
            time.sleep(self._release_delay)


class Rx(Rx_mb_2023):
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
        # I2C connection to MCP23008, for voltage
        self._mcp_address = kwargs['mcp_address']
        # self.mcp_board = MCP23008(self.connection, address=kwargs['mcp_address'])
        if self.connect:
            self.reset_mcp()
        # ADS1115 for voltage measurement (MN)
        self._coef_p2 = 1.
        # Define default DG411 gain
        self._dg411_gain_ratio = kwargs['dg411_gain_ratio']
        self._dg411_gain = self._dg411_gain_ratio

        # Define pins for DG411
        if self.connect:
            self.pin_DG0 = self.mcp_board.get_pin(0)
            self.pin_DG0.direction = Direction.OUTPUT
            self.pin_DG1 = self.mcp_board.get_pin(1)
            self.pin_DG1.direction = Direction.OUTPUT
            self.pin_DG2 = self.mcp_board.get_pin(2)
            self.pin_DG2.direction = Direction.OUTPUT
            self.pin_DG0.value = True  # open
            self.pin_DG1.value = True  # open gain 1 inactive
            self.pin_DG2.value = False  # close gain 0.5 active
            self.gain = self._adc_gain * self._dg411_gain_ratio  # 1/3 by default since self._adc_gain is equal to 2/3 and self._dg411_gain_ratio to 1/2 by default

        if not subclass_init:  # TODO: try to only log this event and not the one created by super()
            self.exec_logger.event(f'{self.model}\trx_init\tend\t{datetime.datetime.utcnow()}')

    def _adc_gain_auto(self):
        self.exec_logger.event(f'{self.model}\trx_adc_auto_gain\tbegin\t{datetime.datetime.utcnow()}')
        gain = _ads_1115_gain_auto(AnalogIn(self._ads_voltage, ads.P0))
        self.exec_logger.debug(f'Setting RX ADC gain automatically to {gain}')
        self._adc_gain = gain
        self.exec_logger.event(f'{self.model}\trx_adc_auto_gain\tend\t{datetime.datetime.utcnow()}')

    def _dg411_gain_auto(self):
        if -self._vmn_hardware_offset < self.voltage + self.bias < self._vmn_hardware_offset:
            self._dg411_gain = 1.
        else:
            self._dg411_gain = self._dg411_gain_ratio
        self.exec_logger.debug(f'Setting RX DG411 gain automatically to {self._dg411_gain}')

    @property
    def gain(self):
        return self._adc_gain*self._dg411_gain

    @gain.setter
    def gain(self, value):
        assert value in [1/3, 2/3, self._adc_gain * self._dg411_gain_ratio]  #TODO: 1/3 could be removed since self._adc_gain * self._dg411_gain_ratio is 1/3 by default
        self._dg411_gain = value / self._adc_gain  # _adc_gain is kept to 2/3 in this board version so _dg411_gain is 1 or 1/2 by default
        if self._dg411_gain == 1.:
            self.pin_DG1.value = False  # closed gain 1 active
            self.pin_DG2.value = True  # open gain 0.5 inactive
        elif self._dg411_gain == self._dg411_gain_ratio:
            self.pin_DG1.value = True  # closed gain 1 active
            self.pin_DG2.value = False  # open gain 0.5 inactive

    def gain_auto(self):
        self._dg411_gain_auto()
        self.exec_logger.debug(f'Setting RX gain automatically to {self.gain}')

    def reset_gain(self):
        self.gain =  self._adc_gain * self._dg411_gain_ratio  # 1/3 by default since self._adc_gain is equal to 2/3 and self._dg411_gain_ratio to 1/2 by default

    def reset_mcp(self):
        self.mcp_board = MCP23008(self.connection, address=self._mcp_address)

    @property
    def voltage(self):
        """ Gets the voltage VMN in Volts
        """
        self.exec_logger.event(f'{self.model}\trx_voltage\tbegin\t{datetime.datetime.utcnow()}')
        u = (AnalogIn(self._ads_voltage, ads.P0).voltage * self._coef_p2 * 1000. - self._vmn_hardware_offset) / self._dg411_gain - self._bias  # TODO: check how to handle bias and _vmn_hardware_offset
        self.exec_logger.event(f'{self.model}\trx_voltage\tend\t{datetime.datetime.utcnow()}')
        return u
