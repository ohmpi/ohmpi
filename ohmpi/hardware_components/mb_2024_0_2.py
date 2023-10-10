import datetime
import adafruit_ads1x15.ads1115 as ads  # noqa
from adafruit_ads1x15.analog_in import AnalogIn  # noqa
from adafruit_ads1x15.ads1x15 import Mode  # noqa
from adafruit_mcp230xx.mcp23008 import MCP23008  # noqa
from digitalio import Direction  # noqa
from busio import I2C  # noqa
from ohmpi.hardware_components.mb_2023_0_X import Tx as Tx_mb_2023
from ohmpi.hardware_components.mb_2023_0_X import Rx as Rx_mb_2023

# hardware characteristics and limitations
# voltages are given in mV, currents in mA, sampling rates in Hz and data_rate in S/s
SPECS = {'rx': {'sampling_rate': {'min': 2., 'default': 10., 'max': 100.},
                'data_rate': {'default': 860.},
                'bias':  {'min': -5000., 'default': 0., 'max': 5000.},
                'coef_p2': {'default': 1.00},
                'mcp_address': {'default': 0x27},
                'ads_address': {'default': 0x49},
                'voltage_min': {'default': 10.0},
                'vmn_hardware_offset': {'default': 2500.},
                },
         'tx': {'adc_voltage_min': {'default': 10.},  # Minimum voltage value used in vmin strategy
                'adc_voltage_max': {'default': 4500.},  # Maximum voltage on ads1115 used to measure current
                'voltage_max': {'min': 0., 'default': 12., 'max': 12.},  # Maximum input voltage
                'data_rate': {'default': 860.},
                'mcp_address': {'default': 0x21},
                'ads_address': {'default': 0x48},
                'compatible_power_sources': {'default': 'pwr_batt', 'others' : ['dps5005']},
                'r_shunt':  {'min': 0., 'default': 2.},
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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # I2C connexion to MCP23008, for current injection
        self.mcp_board = MCP23008(self.connection, address=kwargs['mcp_address'])

        # Initialize LEDs
        self.pin4 = self.mcp_board.get_pin(4)  # Ohmpi_run
        self.pin4.direction = Direction.OUTPUT
        self.pin4.value = True
        self.pin6 = self.mcp_board.get_pin(6)
        self.pin6.direction = Direction.OUTPUT
        self.pin6.value = False
        self.exec_logger.event(f'{self.board_name}\ttx_init\tend\t{datetime.datetime.utcnow()}')

    def inject(self, polarity=1, injection_duration=None):
        # add leds?
        self.pin6.value=True
        Tx_mb_2023.inject(self, polarity=polarity, injection_duration=injection_duration)
        self.pin6.value = False

class Rx(Rx_mb_2023):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # I2C connexion to MCP23008, for voltage
        self.mcp_board = MCP23008(self.connection, address=kwargs['mcp_address'])
        # ADS1115 for voltage measurement (MN)
        self._coef_p2 = 1.
        # Define default DG411 gain
        self._dg411_gain = 1/2
        # Define pins for DG411
        self.pin_DG0 = self.mcp_board.get_pin(0)
        self.pin_DG0.direction = Direction.OUTPUT
        self.pin_DG1 = self.mcp_board.get_pin(1)
        self.pin_DG1.direction = Direction.OUTPUT
        self.pin_DG2 = self.mcp_board.get_pin(2)
        self.pin_DG2.direction = Direction.OUTPUT
        self.pin_DG0.value = True  # open
        self.pin_DG1.value = True  # open gain 1 inactive
        self.pin_DG2.value = False  # close gain 0.5 active
        self.gain = 1/3
        # TODO: try to only log this event and not the one created by super()
        self.exec_logger.event(f'{self.board_name}\trx_init\tend\t{datetime.datetime.utcnow()}')

    def _dg411_gain_auto(self):
        if self.voltage < self._vmn_hardware_offset :
            self._dg411_gain = 1.
        else:
            self._dg411_gain = 1/2

    @property
    def gain(self):
        return self._adc_gain*self._dg411_gain

    @gain.setter
    def gain(self, value):
        assert value in [1/3, 2/3]
        self._dg411_gain = value / self._adc_gain
        if self._dg411_gain == 1.:
            self.pin_DG1.value = False  # closed gain 1 active
            self.pin_DG2.value = True  # open gain 0.5 inactive
        elif self._dg411_gain == 1/2:
            self.pin_DG1.value = True  # closed gain 1 active
            self.pin_DG2.value = False  # open gain 0.5 inactive

    def gain_auto(self):
        self._dg411_gain_auto()

    @property
    def voltage(self):
        """ Gets the voltage VMN in Volts
        """
        self.exec_logger.event(f'{self.board_name}\trx_voltage\tbegin\t{datetime.datetime.utcnow()}')
        u = (AnalogIn(self._ads_voltage, ads.P0).voltage * self._coef_p2 * 1000. - self._vmn_hardware_offset) / self._dg411_gain - self._bias  # TODO: check how to handle bias and _vmn_hardware_offset
        self.exec_logger.event(f'{self.board_name}\trx_voltage\tend\t{datetime.datetime.utcnow()}')
        return u
