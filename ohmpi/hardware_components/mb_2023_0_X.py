import datetime
import importlib
# from ohmpi.config import HARDWARE_CONFIG  # TODO: Remove references at config here -> move it in ohmpi_hardware as done for mux_2024
import adafruit_ads1x15.ads1115 as ads  # noqa
from adafruit_ads1x15.analog_in import AnalogIn  # noqa
from adafruit_ads1x15.ads1x15 import Mode  # noqa
from adafruit_mcp230xx.mcp23008 import MCP23008  # noqa
from digitalio import Direction  # noqa
import time
import numpy as np
import os
from ohmpi.hardware_components import TxAbstract, RxAbstract
# ctl_name = HARDWARE_CONFIG['ctl'].pop('board_name', 'raspberry_pi')
# ctl_connection = HARDWARE_CONFIG['ctl'].pop('connection', 'i2c')
# ctl_module = importlib.import_module(f'ohmpi.hardware_components.{ctl_name}')

# TX_CONFIG = HARDWARE_CONFIG['tx']
# RX_CONFIG = HARDWARE_CONFIG['rx']

# hardware characteristics and limitations
# voltages are given in mV, currents in mA, sampling rates in Hz and data_rate in S/s
SPECS = {'RX': {'voltage_adc_voltage_min': 10., 'voltage_adc_voltage_max': 4500., 'sampling_rate': 20.,
                'data_rate': 860.},
         'TX': {'current_adc_voltage_min': 10., 'bias': 0., 'injection_voltage_max': 12000., 'low_battery': 12000.,
                'tx_mcp_board_address': 0x20, 'data_rate': 860., 'comptatible_power_sources': ['pwr_batt', 'dps5005'],
                'r_shunt': 2., 'activation_delay': 0.005, 'release_delay': 0.001}}

# TODO: move low_battery spec in pwr

# *** RX ***
# ADC for voltage
# voltage_adc_voltage_min = 10.  # mV
# voltage_adc_voltage_max = 4500.  # mV
# sampling_rate = 20.  # Hz
# data_rate = 860.  # S/s?

# RX_CONFIG['voltage_min'] = np.min([voltage_adc_voltage_min, RX_CONFIG.pop('voltage_min', np.inf)])  # mV
# RX_CONFIG['voltage_max'] = np.min([voltage_adc_voltage_max, RX_CONFIG.pop('voltage_max', np.inf)])  # mV
# RX_CONFIG['sampling_rate'] = RX_CONFIG.pop('sampling_rate', sampling_rate)
# RX_CONFIG['data_rate'] = RX_CONFIG.pop('data_rate', data_rate)
# RX_CONFIG['coef_p2'] = RX_CONFIG.pop('coef_p2', 2.5)
# RX_CONFIG['latency'] = RX_CONFIG.pop('latency', 0.01)
# RX_CONFIG['bias'] = RX_CONFIG.pop('bias', 0.)


# *** TX ***
# ADC for current
# current_adc_voltage_min = 10.  # mV
# current_adc_voltage_max = 4500.  # mV
# low_battery = 12.  # V (conventional value as it is not measured on this board)
# tx_mcp_board_address = 0x20  #
# pwr_voltage_max = 12.  # V
# pwr_default_voltage = 12.  # V
# pwr_switch_on_warmup = 0.  # seconds

# TX_CONFIG['current_min'] = np.min([current_adc_voltage_min / (TX_CONFIG['r_shunt'] * 50),
#                                    TX_CONFIG.pop('current_min', np.inf)])  # mA
# TX_CONFIG['current_max'] = np.min([current_adc_voltage_max / (TX_CONFIG['r_shunt'] * 50),
#                                    TX_CONFIG.pop('current_max', np.inf)])  # mA
# # TX_CONFIG['voltage_max'] = np.min([pwr_voltage_max, TX_CONFIG.pop('voltage_max', np.inf)])  # V
# TX_CONFIG['voltage_max'] = TX_CONFIG.pop('voltage_max', np.inf)  # V
# TX_CONFIG['voltage_min'] = -TX_CONFIG['voltage_max']  # V
# TX_CONFIG['default_voltage'] = np.min([TX_CONFIG.pop('default_voltage', np.inf), TX_CONFIG['voltage_max']])  # V
# # TX_CONFIG['pwr_switch_on_warm_up'] = TX_CONFIG.pop('pwr_switch_on_warmup', pwr_switch_on_warmup)
# TX_CONFIG['mcp_board_address'] = TX_CONFIG.pop('mcp_board_address', tx_mcp_board_address)
# TX_CONFIG['low_battery'] = TX_CONFIG.pop('low_battery', low_battery)
# TX_CONFIG['latency'] = TX_CONFIG.pop('latency', 0.01)
# TX_CONFIG['bias'] = TX_CONFIG.pop('bias', 0.)


def _gain_auto(channel):
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
    def __init__(self, **kwargs):
        kwargs.update({'board_name': os.path.basename(__file__).rstrip('.py')})
        super().__init__(**kwargs)
        kwargs.update({'pwr': kwargs.pop('pwr', SPECS['compatible_power_sources'][0])})
        if kwargs['pwr'] not in SPECS['TX']['compatible_power_sources']:
            self.exec_logger.warning(f'Incompatible power source specified check config')
            assert kwargs['pwr'] in SPECS['TX']
        #self.pwr = None  # TODO: set a list of compatible power system with the tx
        self.exec_logger.event(f'{self.board_name}\ttx_init\tbegin\t{datetime.datetime.utcnow()}')
        self._voltage = kwargs.pop('voltage', TX_CONFIG['default_voltage'])
        self.voltage_adjustable = False
        self.current_adjustable = False
        if self.ctl is None:
            self.ctl = ctl_module.Ctl()
        # elif isinstance(self.ctl, dict):
        #     self.ctl = ctl_module.Ctl(**self.ctl)
        self.connection = self.ctl.interfaces[kwargs.pop('connection', ctl_connection)]

        # I2C connexion to MCP23008, for current injection
        self.mcp_board = MCP23008(self.connection, address=SPECS['TX']['mcp_board_address'])
        # ADS1115 for current measurement (AB)
        self._ads_current_address = 0x48
        self._ads_current = ads.ADS1115(self.connection, gain=self.adc_gain, data_rate=860,
                                        address=self._ads_current_address)
        self._ads_current.mode = Mode.CONTINUOUS

        # Relays for pulse polarity
        self.pin0 = self.mcp_board.get_pin(0)
        self.pin0.direction = Direction.OUTPUT
        self.pin1 = self.mcp_board.get_pin(1)
        self.pin1.direction = Direction.OUTPUT
        self.polarity = 0
        self.adc_gain = 2 / 3

        # MCP23008 pins for LEDs
        self.pin4 = self.mcp_board.get_pin(4)  # TODO: Delete me? No LED on this version of the board
        self.pin4.direction = Direction.OUTPUT
        self.pin4.value = True

        self._bias = kwargs.pop('bias', TX_CONFIG['bias'])
        self.exec_logger.event(f'{self.board_name}\ttx_init\tend\t{datetime.datetime.utcnow()}')

    @property
    def adc_gain(self):
        return self._adc_gain

    @adc_gain.setter
    def adc_gain(self, value):
        assert value in [2/3, 2, 4, 8, 16]
        self._adc_gain = value
        self._ads_current = ads.ADS1115(self.connection, gain=self.adc_gain, data_rate=SPECS['TX']['data_rate'],
                                        address=self._ads_current_address)
        self._ads_current.mode = Mode.CONTINUOUS
        self.exec_logger.debug(f'Setting TX ADC gain to {value}')

    def adc_gain_auto(self):
        self.exec_logger.event(f'{self.board_name}\ttx_adc_auto_gain\tbegin\t{datetime.datetime.utcnow()}')
        gain = _gain_auto(AnalogIn(self._ads_current, ads.P0))
        self.exec_logger.debug(f'Setting TX ADC gain automatically to {gain}')
        self.adc_gain = gain
        self.exec_logger.event(f'{self.board_name}\ttx_adc_auto_gain\tend\t{datetime.datetime.utcnow()}')

    def current_pulse(self, **kwargs):
        TxAbstract.current_pulse(self, **kwargs)
        self.exec_logger.warning(f'Current pulse is not implemented for the {TX_CONFIG["model"]} board')

    @property
    def current(self):
        """ Gets the current IAB in Amps
        """
        iab = AnalogIn(self._ads_current, ads.P0).voltage * 1000. / (50 * TX_CONFIG['r_shunt'])  # measure current
        self.exec_logger.debug(f'Reading TX current:  {iab} mA')
        return iab

    @ current.setter
    def current(self, value):
        assert TX_CONFIG['current_min'] <= value <= TX_CONFIG['current_max']
        self.exec_logger.warning(f'Current pulse is not implemented for the {TX_CONFIG["model"]} board')

    def inject(self, polarity=1, injection_duration=None):
        self.polarity = polarity
        TxAbstract.inject(self, polarity=polarity, injection_duration=injection_duration)

    @property
    def polarity(self):
        return self._polarity

    @polarity.setter
    def polarity(self, polarity):
        assert polarity in [-1, 0, 1]
        self._polarity = polarity
        if polarity == 1:
            self.pin0.value = True
            self.pin1.value = False
            time.sleep(SPECS['TX']['activation_delay'])  # Max turn on time of 211EH relays = 5ms
        elif polarity == -1:
            self.pin0.value = False
            self.pin1.value = True
            time.sleep(SPECS['TX']['activation_delay'])  # Max turn on time of 211EH relays = 5ms
        else:
            self.pin0.value = False
            self.pin1.value = False
            time.sleep(SPECS['TX']['release_delay'])  # Max turn off time of 211EH relays = 1ms

    def turn_off(self):
        self.pwr.turn_off(self)

    def turn_on(self):
        self.pwr.turn_on(self)

    @property
    def tx_bat(self):
        self.soh_logger.warning(f'Cannot get battery voltage on {self.board_name}')
        self.exec_logger.debug(f'{self.board_name} cannot read battery voltage. Returning default battery voltage.')
        return TX_CONFIG['low_battery']

    def voltage_pulse(self, voltage=TX_CONFIG['default_voltage'], length=None, polarity=1):
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
        self.exec_logger.event(f'{self.board_name}\ttx_voltage_pulse\tbegin\t{datetime.datetime.utcnow()}')
        # self.exec_logger.info(f'injection_duration: {length}')  # TODO: delete me
        if length is None:
            length = self.injection_duration
        self.pwr.voltage = voltage
        self.exec_logger.debug(f'Voltage pulse of {polarity*self.pwr.voltage:.3f} V for {length:.3f} s')
        self.inject(polarity=polarity, injection_duration=length)
        self.exec_logger.event(f'{self.board_name}\ttx_voltage_pulse\tend\t{datetime.datetime.utcnow()}')


class Rx(RxAbstract):
    def __init__(self, **kwargs):
        kwargs.update({'board_name': os.path.basename(__file__).rstrip('.py')})
        super().__init__(**kwargs)
        self.exec_logger.event(f'{self.board_name}\trx_init\tbegin\t{datetime.datetime.utcnow()}')
        if self.ctl is None:
            self.ctl = ctl_module.Ctl()
        self.connection = self.ctl.interfaces[kwargs.pop('connection', ctl_connection)]

        # ADS1115 for voltage measurement (MN)
        self._ads_voltage_address = 0x49
        self._adc_gain = 2/3
        self._ads_voltage = ads.ADS1115(self.connection, gain=self._adc_gain, data_rate=860,
                                        address=self._ads_voltage_address)
        self._ads_voltage.mode = Mode.CONTINUOUS
        self._coef_p2 = kwargs.pop('coef_p2', RX_CONFIG['coef_p2'])
        self._voltage_max = kwargs.pop('voltage_max', RX_CONFIG['voltage_max'])
        self._sampling_rate = kwargs.pop('sampling_rate', sampling_rate)
        self._latency = kwargs.pop('latency', RX_CONFIG['latency'])
        self._bias = kwargs.pop('bias', RX_CONFIG['bias'])
        self.exec_logger.event(f'{self.board_name}\trx_init\tend\t{datetime.datetime.utcnow()}')

    @property
    def adc_gain(self):
        return self._adc_gain

    @adc_gain.setter
    def adc_gain(self, value):
        assert value in [2/3, 2, 4, 8, 16]
        self._adc_gain = value
        self._ads_voltage = ads.ADS1115(self.connection, gain=self.adc_gain, data_rate=860,
                                        address=self._ads_voltage_address)
        self._ads_voltage.mode = Mode.CONTINUOUS
        self.exec_logger.debug(f'Setting RX ADC gain to {value}')

    def adc_gain_auto(self):
        self.exec_logger.event(f'{self.board_name}\trx_adc_auto_gain\tbegin\t{datetime.datetime.utcnow()}')
        gain_0 = _gain_auto(AnalogIn(self._ads_voltage, ads.P0))
        gain_2 = _gain_auto(AnalogIn(self._ads_voltage, ads.P2))
        gain = np.min([gain_0, gain_2])
        self.exec_logger.debug(f'Setting RX ADC gain automatically to {gain}')
        self.adc_gain = gain
        self.exec_logger.event(f'{self.board_name}\trx_adc_auto_gain\tend\t{datetime.datetime.utcnow()}')

    @property
    def voltage(self):
        """ Gets the voltage VMN in Volts
        """
        self.exec_logger.event(f'{self.board_name}\trx_voltage\tbegin\t{datetime.datetime.utcnow()}')
        u = -AnalogIn(self._ads_voltage, ads.P0, ads.P1).voltage * self._coef_p2 * 1000. - self._bias  # TODO: check if it should be negated
        self.exec_logger.event(f'{self.board_name}\trx_voltage\tend\t{datetime.datetime.utcnow()}')
        return u
