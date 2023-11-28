from ohmpi.hardware_components import CtlAbstract
import board  # noqa
import busio  # noqa
from adafruit_extended_bus import ExtendedI2C  # noqa
import minimalmodbus  # noqa
import os
from ohmpi.utils import get_platform, enforce_specs
from gpiozero import CPUTemperature  # noqa
import warnings

# hardware characteristics and limitations
SPECS = {'model': {'default': os.path.basename(__file__).rstrip('.py')},
         'voltage': {'default': 12., 'max': 50., 'min': 0.},
         'modbus_baudrate': {'default': 19200},
         'modbus_bitesize': {'default': 8},
         'modbus_timeout': {'default': 1},
         'modbus_debug': {'default': False},
         'modbus_parity': {'default': 'N'},
         'modbus_mode': {'default': minimalmodbus.MODE_RTU},
         'modbus_port': {'default': '/dev/ttyUSB0'},
         'modbus_slave_address': {'default': 1}
         }


class Ctl(CtlAbstract):
    def __init__(self, **kwargs):
        if 'model' not in kwargs.keys():
            for key in SPECS.keys():
                kwargs = enforce_specs(kwargs, SPECS, key)
            subclass_init = False
        else:
            subclass_init = True

        super().__init__(**kwargs)
        self.interfaces = dict()

        # None interface for battery
        self.interfaces['none'] = None

        warnings.filterwarnings("error")  # to filter out adafruit warning about setting I2C frequency
        # I2C
        try:
            self.interfaces['i2c'] = busio.I2C(board.SCL, board.SDA)  # noqa
        except RuntimeWarning:
            pass

        # Extended I2C
        try:
            self.interfaces['i2c_ext'] = ExtendedI2C(4)  # 4 is defined
        except RuntimeWarning:
            pass
        except Exception as e:
            self.exec_logger.warning(f'Could not initialize Extended I2C:\n{e}')

        warnings.resetwarnings()

        # modbus
        try:
            self.interfaces['modbus'] = minimalmodbus.Instrument(port=kwargs['modbus_port'],
                                                                 slaveaddress=kwargs['modbus_slave_address'])
            self.interfaces['modbus'].serial.baudrate = kwargs['modbus_baudrate']  # Baud rate 9600 as listed in doc
            self.interfaces['modbus'].serial.bytesize = kwargs['modbus_bitesize']  #
            self.interfaces['modbus'].serial.timeout = kwargs['modbus_timeout']  # greater than 0.5 for it to work
            self.interfaces['modbus'].debug = kwargs['modbus_debug']  #
            self.interfaces['modbus'].serial.parity = kwargs['modbus_parity']  # No parity
            self.interfaces['modbus'].mode = kwargs['modbus_mode']  # RTU mode
        except Exception as e:
            self.exec_logger.warning(f'Could not initialize Extended modbus:\n{e}')

        platform, on_pi = get_platform()
        assert on_pi
        self.model = platform
        self._cpu_temp_available = True
        self.max_cpu_temp = 85.  # °C

    @property
    def _cpu_temp(self):
        return CPUTemperature().temperature
