import datetime
import adafruit_ads1x15.ads1115 as ads  # noqa
from adafruit_ads1x15.analog_in import AnalogIn  # noqa
from adafruit_ads1x15.ads1x15 import Mode  # noqa
from adafruit_mcp230xx.mcp23008 import MCP23008  # noqa
from digitalio import Direction  # noqa
from busio import I2C  # noqa
from termcolor import colored
import time
import os
import numpy as np
from ohmpi.hardware_components import TxAbstract, RxAbstract
from ohmpi.utils import enforce_specs
from ohmpi.tests import test_i2c_devices_on_bus

# hardware characteristics and limitations
# voltages are given in mV, currents in mA, sampling rates in Hz and data_rate in S/s
SPECS = {'rx': {'model': {'default': os.path.basename(__file__).rstrip('.py')},
                'sampling_rate': {'min': 0., 'default': 100., 'max': 500.},
                'data_rate': {'default': 860.},
                'bias':  {'min': -5000., 'default': 0., 'max': 5000.},
                'coef_p2': {'default': 2.50},
                'mcp_address': {'default': None},
                'ads_address': {'default': 0x49},
                'voltage_min': {'default': 10.0},
                'voltage_max': {'default': 5000.0},  # [mV]
                'vmn_hardware_offset': {'default': 0.}
                },
         'tx': {'model': {'default': os.path.basename(__file__).rstrip('.py')},
                'adc_voltage_min': {'default': 10.},  # Minimum voltage value that can be measured reliably
                'adc_voltage_max': {'default': 4500.},  # Maximum voltage on ads1115 used to measure current
                'voltage_max': {'min': 0., 'default': 12., 'max': 12.},  # Maximum input voltage
                'data_rate': {'default': 860.},
                'mcp_address': {'default': 0x20},
                'ads_address': {'default': 0x48},
                'compatible_power_sources': {'default': ['pwr_batt', 'dps5005']},
                'r_shunt':  {'min': 0., 'default': 2.},
                'activation_delay': {'default': 0.005},  # Max turn on time of 211EH relays = 5ms
                'release_delay': {'default': 0.001},  # Max turn off time of 211EH relays = 1ms
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


class Tx(TxAbstract):
    """Tx Class
        """
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
        assert isinstance(self.connection, I2C)
        kwargs.update({'pwr': kwargs.pop('pwr', SPECS['tx']['compatible_power_sources']['default'][0])})
        if kwargs['pwr'] not in SPECS['tx']['compatible_power_sources']['default']:
            self.exec_logger.warning(f'Incompatible power source specified check config')
            assert kwargs['pwr'] in SPECS['tx']
        self._activation_delay = kwargs['activation_delay']
        self._release_delay = kwargs['release_delay']
        self.voltage_adjustable = False
        self.current_adjustable = False

        # I2C connection to MCP23008, for current injection
        self._mcp_address = kwargs['mcp_address']
        if test_i2c_devices_on_bus(self._mcp_address, self.connection):
            if self.connect:
                try:
                    self.reset_mcp()
                    self.soh_logger.info(colored(
                        f'TX: MCP23008 ({hex(self._mcp_address)}) found on I2C bus...OK', 'green'))
                except Exception as e:

                    self.soh_logger.info(colored(
                        f'TX: MCP23008 ({hex(self._mcp_address)}) found on I2C bus...NOT OK', 'green'))
        else:
            
                    self.soh_logger.info(colored(
                        f'TX: MCP23008 ({hex(self._mcp_address)}) NOT found on I2C bus', 'green'))

        # ADS1115 for current measurement (AB)
        self._ads_current_address = kwargs['ads_address']
        self._ads_current_data_rate = kwargs['data_rate']
        self._adc_gain = 2 / 3
        if test_i2c_devices_on_bus(self._ads_current_address, self.connection):
            if self.connect:
                try:
                    self.reset_ads()
                    self._ads_current.mode = Mode.CONTINUOUS
                    self.soh_logger.info(colored(
                        f'TX: ADS1115 current ({hex(self._ads_current_address)}) found on I2C bus...OK', 'green'))
                except Exception as e:
                    self.soh_logger.info(colored(
                        f'TX: ADS1115 current ({hex(self._ads_current_address)}) found on I2C bus...NOT OK', 'red')) 
        else:
            self.soh_logger.info(colored(
                f'TX: ADS1115 current ({hex(self._ads_current_address)}) NOT found on I2C bus', 'red'))
            
        
        self._r_shunt = kwargs['r_shunt']
        self.adc_voltage_min = kwargs['adc_voltage_min']
        self.adc_voltage_max = kwargs['adc_voltage_max']

        # Relays for pulse polarity
        if self.connect:
            self.pin0 = self.mcp_board.get_pin(0)
            self.pin0.direction = Direction.OUTPUT
            self.pin1 = self.mcp_board.get_pin(1)
            self.pin1.direction = Direction.OUTPUT
            # self.polarity = 0
            self.gain = 2 / 3

        if not subclass_init:
            self.exec_logger.event(f'{self.model}\ttx_init\tend\t{datetime.datetime.utcnow()}')

    @property
    def gain(self):
        return self._adc_gain

    @gain.setter
    def gain(self, value):
        assert value in [2/3, 2, 4, 8, 16]
        self._adc_gain = value
        self._ads_current = ads.ADS1115(self.connection, gain=self._adc_gain,
                                        data_rate=SPECS['tx']['data_rate']['default'],
                                        address=self._ads_current_address)
        self._ads_current.mode = Mode.CONTINUOUS
        self.exec_logger.debug(f'Setting TX ADC gain to {value}')

    def _adc_gain_auto(self):
        self.exec_logger.event(f'{self.model}\ttx_adc_auto_gain\tbegin\t{datetime.datetime.utcnow()}')
        gain = _ads_1115_gain_auto(AnalogIn(self._ads_current, ads.P0))
        self.exec_logger.debug(f'Setting TX ADC gain automatically to {gain}')
        self.gain = gain
        self.exec_logger.event(f'{self.model}\ttx_adc_auto_gain\tend\t{datetime.datetime.utcnow()}')

    def current_pulse(self, **kwargs):
        TxAbstract.current_pulse(self, **kwargs)
        self.exec_logger.warning(f'Current pulse is not implemented for the {self.model} board')

    @property
    def current(self):
        """ Gets the current IAB in Amps
        """
        iab = AnalogIn(self._ads_current, ads.P0).voltage * 1000. / (50 * self._r_shunt)  # measure current
        self.exec_logger.debug(f'Reading TX current: {iab} mA')
        return iab

    @ current.setter
    def current(self, value):
        assert self.adc_voltage_min / (50 * self._r_shunt) <= value <= self.adc_voltage_max / (50 * self._r_shunt)
        self.exec_logger.warning(f'Current pulse is not implemented for the {self.model} board')

    def gain_auto(self):
        self._adc_gain_auto()

    def inject(self, polarity=1, injection_duration=None, switch_pwr=False):
        self.polarity = polarity
        TxAbstract.inject(self, polarity=polarity, injection_duration=injection_duration, switch_pwr=switch_pwr)

    @property
    def polarity(self):
        return self._polarity

    @polarity.setter
    def polarity(self, polarity):
        assert polarity in [-1, 0, 1]
        self._polarity = polarity
        if polarity == 1:
            self.pin1.value = False
            time.sleep(self._release_delay)
            self.pin0.value = True
            time.sleep(self._activation_delay)
        elif polarity == -1:
            self.pin0.value = False
            time.sleep(self._release_delay)
            self.pin1.value = True
            time.sleep(self._activation_delay)
        else:
            self.pin0.value = False
            self.pin1.value = False
            time.sleep(self._release_delay)
    #
    # def turn_off(self):
    #     self.pwr.turn_off(self)
    #
    # def turn_on(self):
    #     self.pwr.turn_on(self)

    def reset_ads(self, mode=Mode.CONTINUOUS):
        self._ads_current = ads.ADS1115(self.connection, gain=self._adc_gain, data_rate=self._ads_current_data_rate,
                                    address=self._ads_current_address)
        self._ads_current.mode = mode

    def reset_gain(self):
        self.exec_logger.debug('resetting tx gain to 2/3')
        self.gain = 2/3

    def reset_mcp(self):
        self.mcp_board = MCP23008(self.connection, address=self._mcp_address)

    @property
    def tx_bat(self):
        if np.isnan(self.pwr.battery_voltage):
            self.soh_logger.warning(f'Cannot get battery voltage on {self.model}')
            self.exec_logger.debug(f'{self.model} cannot read battery voltage. Returning default battery voltage.')
            return self.pwr.voltage
        else:
            return self.pwr.battery_voltage

    def voltage_pulse(self, voltage=None, length=None, polarity=1):
        """ Generates a square voltage pulse

        Parameters
        ----------
        voltage: float, optional
            Voltage to apply in volts, tx_v_def is applied if omitted.
        length: float, optional
            Length of the pulse in seconds
        polarity: 1,0,-1
            Polarity of the pulse
        """
        self.exec_logger.event(f'{self.model}\ttx_voltage_pulse\tbegin\t{datetime.datetime.utcnow()}')
        # self.exec_logger.info(f'injection_duration: {length}')  # TODO: delete me
        if length is None:
            length = self.injection_duration
        if voltage is not None:
            self.pwr.voltage = voltage
        self.exec_logger.debug(f'Voltage pulse of {polarity*self.pwr.voltage:.3f} V for {length:.3f} s')
        self.inject(polarity=polarity, injection_duration=length)
        self.exec_logger.event(f'{self.model}\ttx_voltage_pulse\tend\t{datetime.datetime.utcnow()}')

    def test_ads(self, nsample=100, channel=0):
        samples = []
        pindic = {
            0: ads.P0,
            1: ads.P1,
            2: ads.P2,
            3: ads.P3
        }
        for i in range(nsample):
            samples.append(AnalogIn(self._ads_current, pindic[channel]).voltage)
        std = np.std(samples)
        ok = std < 1
        res = {
            'name': 'test_ads_current',
            'passed': ok,
            'value': std,
            'unit': 'mV'
        }
        if ok:
            msg = 'OK'
            color = 'green'
        else:
            msg = 'FAILED'
            color = 'red'
        self.exec_logger.info(colored(
            'test_ads_voltage (channel {:d})...{:s} (std: {:.3f})'.format(
                channel, msg, std), color))   
        return res

    def test(self):
        results = []
        results.append(self.test_ads())
        return results

class Rx(RxAbstract):
    """RX class"""
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
        assert isinstance(self.connection, I2C)

        # ADS1115 for voltage measurement (MN)
        self._ads_voltage_address = kwargs['ads_address']
        self._ads_voltage_data_rate = kwargs['data_rate']
        self._adc_gain = 2/3
        if test_i2c_devices_on_bus(self._ads_voltage_address, self.connection):
            if self.connect:
                try:
                    self.reset_ads(mode=Mode.CONTINUOUS)
                    self.soh_logger.info(colored(
                        f"RX: ADS1115 voltage ({hex(self._ads_voltage_address)}) found on I2C...OK", "green"))
                except Exception as e:
                    self.soh_logger.info(colored(
                        f"RX: ADS1115 voltage ({hex(self._ads_voltage_address)}) found on I2C...NOT OK", "red"))
        else:
            self.soh_logger.info(colored(
                f"RX: ADS1115 voltage ({hex(self._ads_voltage_address)}) NOT found on I2C", "red"))

        self._coef_p2 = kwargs['coef_p2']
        # self._voltage_max = kwargs['voltage_max']
        self._sampling_rate = kwargs['sampling_rate']
        self._bias = kwargs['bias']
        if not subclass_init:
            self.exec_logger.event(f'{self.model}\trx_init\tend\t{datetime.datetime.utcnow()}')

    @property
    def gain(self):  # TODO: should be in abstract_hardware_components
        return self._adc_gain

    @gain.setter
    def gain(self, value):
        assert value in [2/3, 2, 4, 8, 16]
        self._adc_gain = value
        self._ads_voltage = ads.ADS1115(self.connection, gain=self._adc_gain,
                                        data_rate=SPECS['rx']['data_rate']['default'],
                                        address=self._ads_voltage_address)
        self._ads_voltage.mode = Mode.CONTINUOUS
        self.exec_logger.debug(f'Setting RX ADC gain to {value}')

    def _adc_gain_auto(self):
        self.exec_logger.event(f'{self.model}\trx_adc_auto_gain\tbegin\t{datetime.datetime.utcnow()}')
        gain = _ads_1115_gain_auto(AnalogIn(self._ads_voltage, ads.P0, ads.P1))
        self.exec_logger.debug(f'Setting RX ADC gain automatically to {gain}')
        self._adc_gain = gain
        self.exec_logger.event(f'{self.model}\trx_adc_auto_gain\tend\t{datetime.datetime.utcnow()}')

    def gain_auto(self):
        self._adc_gain_auto()

    def reset_gain(self):
        self.exec_logger.debug('resetting rx gain to 2/3')
        self.gain = 2/3

    def reset_ads(self, mode=Mode.CONTINUOUS):
        self._ads_voltage = ads.ADS1115(self.connection, gain=self._adc_gain, data_rate=self._ads_voltage_data_rate,
                                    address=self._ads_voltage_address)
        self._ads_voltage.mode = mode

    @property
    def voltage(self):
        """ Gets the voltage VMN in Volts
        """
        self.exec_logger.event(f'{self.model}\trx_voltage\tbegin\t{datetime.datetime.utcnow()}')
        u = AnalogIn(self._ads_voltage, ads.P0, ads.P1).voltage * self._coef_p2 * 1000. - self.bias  # TODO: check if it should be negated
        self.exec_logger.event(f'{self.model}\trx_voltage\tend\t{datetime.datetime.utcnow()}')
        return u

    def test_ads(self, nsample=100, channel=0):
        samples = []
        pindic = {
            0: ads.P0,
            1: ads.P1,
            2: ads.P2,
            3: ads.P3
        }
        for i in range(nsample):
            samples.append(AnalogIn(self._ads_voltage, pindic[channel]).voltage)
        std = np.std(samples)
        res = {
            'name': 'test_ads_voltage_' + str(channel),
            'passed': std < 1,
            'std': std,
            'unit': 'mV'
        }
        if ok:
            msg = 'OK'
            color = 'green'
        else:
            msg = 'FAILED'
            color = 'red'
        self.exec_logger.info(colored(
            'test_ads_voltage (channel {:d})...{:s} (std: {:.3f})'.format(
                channel, msg, std), color))

        return res

    def test(self):
        results = []
        results.append(self.test_ads(channel=0))
        return results
