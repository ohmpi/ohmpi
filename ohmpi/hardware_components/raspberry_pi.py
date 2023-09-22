from ohmpi.hardware_components import CtlAbstract
import board  # noqa
import busio  # noqa
from adafruit_extended_bus import ExtendedI2C  # noqa
import minimalmodbus  # noqa
import os
from ohmpi.utils import get_platform
from gpiozero import CPUTemperature  # noqa


class Ctl(CtlAbstract):
    def __init__(self, **kwargs):
        kwargs.update({'board_name': os.path.basename(__file__).rstrip('.py')})
        modbus_baudrate = kwargs.pop('modbus_baudrate', 9600)
        modbus_bitesize = kwargs.pop('modbus_bitesize', 8)
        modbus_timeout = kwargs.pop('modbus_timeout', 1)
        modbus_debug = kwargs.pop('modbus_debug', False)
        modbus_parity = kwargs.pop('modbus_parity', 'N')
        modbus_mode = kwargs.pop('modbus_mode', minimalmodbus.MODE_RTU)
        modbus_port = kwargs.pop('modbus_port', '/dev/ttyUSB0')
        modbus_slave_address = kwargs.pop('modbus_slave_address', 1)

        super().__init__(**kwargs)
        self.connections = dict()
        # I2C
        self.connections['i2c'] = busio.I2C(board.SCL, board.SDA)  # noqa

        # Extended I2C
        try:
            self.connections['i2c_ext'] = ExtendedI2C(4)  # 4 is defined
        except Exception as e:
            self.exec_logger.warning('Could not initialize Extended I2C:\n{e}')
        # modbus
        try:
            self.connections['modbus'] = minimalmodbus.Instrument(port=modbus_port, slaveaddress=modbus_slave_address)
            self.connections['modbus'].serial.baudrate = modbus_baudrate  # Baud rate 9600 as listed in doc
            self.connections['modbus'].serial.bytesize = modbus_bitesize  #
            self.connections['modbus'].serial.timeout = modbus_timeout  # greater than 0.5 for it to work
            self.connections['modbus'].debug = modbus_debug  #
            self.connections['modbus'].serial.parity = modbus_parity  # No parity
            self.connections['modbus'].mode = modbus_mode  # RTU mode
        except Exception as e:
            self.exec_logger.warning('Could not initialize Extended modbus:\n{e}')

        platform, on_pi = get_platform()
        assert on_pi
        self.board_name = platform
        self._cpu_temp_available = True
        self.max_cpu_temp = 85.  # °C

    @property
    def _cpu_temp(self):
        return CPUTemperature().temperature
