import importlib
from ..config import OHMPI_CONFIG
import adafruit_ads1x15.ads1115 as ads  # noqa
from adafruit_ads1x15.analog_in import AnalogIn  # noqa
from adafruit_mcp230xx.mcp23008 import MCP23008  # noqa
from digitalio import Direction  # noqa
import minimalmodbus  # noqa
import time
from hardware import TxAbstract, RxAbstract
controller_module = importlib.import_module(f'{OHMPI_CONFIG["hardware"]["controller"]["model"]}')
TX_CONFIG = OHMPI_CONFIG['hardware']['TX']

class TX(TxAbstract):
    def __init__(self, **kwargs):
        self.controller = kwargs.pop('controller', controller_module.Controller())
        super().__init__(**kwargs)

        # I2C connexion to MCP23008, for current injection
        self.mcp_board = MCP23008(self.controller.bus, address=TX_CONFIG['mcp_board_address'])
        self.pin4 = self.mcp_board.get_pin(4)  # Ohmpi_run
        self.pin4.direction = Direction.OUTPUT
        self.pin4.value = True

        # ADS1115 for current measurement (AB)
        self.ads_current = ads.ADS1115(self.controller.bus, gain=2/3, data_rate=860, address=0x48)

        # DPH 5005 Digital Power Supply
        self.pin2 = self.mcp_board.get_pin(2)  # dps +
        self.pin2.direction = Direction.OUTPUT
        self.pin2.value = True
        self.pin3 = self.mcp_board.get_pin(3)  # dps -
        self.pin3.direction = Direction.OUTPUT
        self.pin3.value = True
        time.sleep(4)
        self.DPS = minimalmodbus.Instrument(port='/dev/ttyUSB0', slaveaddress=1)  # port name, address (decimal)
        self.DPS.serial.baudrate = 9600  # Baud rate 9600 as listed in doc
        self.DPS.serial.bytesize = 8  #
        self.DPS.serial.timeout = 1  # greater than 0.5 for it to work
        self.DPS.debug = False  #
        self.DPS.serial.parity = 'N'  # No parity
        self.DPS.mode = minimalmodbus.MODE_RTU  # RTU mode
        self.DPS.write_register(0x0001, 1000, 0)  # max current allowed (100 mA for relays)
        # (last number) 0 is for mA, 3 is for A

        # self.soh_logger.debug(f'Battery voltage: {self.DPS.read_register(0x05,2 ):.3f}') TODO: SOH logger
        print(self.DPS.read_register(0x05, 2))
        self.switch_dps('off')

    def turn_on(self):
        self.pin2.value = True
        self.pin3.value = True
        self.exec_logger.debug(f'Switching DPS on')
        time.sleep(4)

    def turn_off(self):
        self.pin2.value = False
        self.pin3.value = False
        self.exec_logger.debug(f'Switching DPS off')


class RX(RxAbstract):
    def __init__(self, **kwargs):
        self.controller = kwargs.pop('controller', controller_module.Controller())
        super().__init__(**kwargs)

        # ADS1115 for voltage measurement (MN)
        self.ads_voltage = ads.ADS1115(self.controller.bus, gain=2/3, data_rate=860, address=0x49)