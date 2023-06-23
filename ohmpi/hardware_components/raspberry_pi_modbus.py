from ohmpi.hardware_components import CtlAbstract
from ohmpi.config import HARDWARE_CONFIG
import board  # noqa
import busio  # noqa
import os
from ohmpi.utils import get_platform
from gpiozero import CPUTemperature  # noqa
import minimalmodbus  # noqa



class Ctl(CtlAbstract):
    def __init__(self, **kwargs):
        kwargs.update({'board_name': os.path.basename(__file__).rstrip('.py')})
        baudrate = kwargs.pop('baudrate', 9600)
        bitesize = kwargs.pop('bitesize', 8)
        timeout = kwargs.pop('timeout', 1)
        debug = kwargs.pop('debug', False)
        parity = kwargs.pop('parity', 'N')
        mode = kwargs.pop('mode', minimalmodbus.MODE_RTU)
        port = kwargs.pop('port', '/dev/ttyUSB0')
        slave_address = kwargs.pop('slave_address', 1)
        port = kwargs.pop('port', '/dev/ttyUSB0')
        slave_address = kwargs.pop('slave_address', 1)
        super().__init__(**kwargs)
        self.bus = minimalmodbus.Instrument(port=port, slaveaddress=slave_address)  # port name, address (decimal)
        self.bus.serial.baudrate = baudrate  # Baud rate 9600 as listed in doc
        self.bus.serial.bytesize = bitesize  #
        self.bus.serial.timeout = timeout  # greater than 0.5 for it to work
        self.bus.debug = debug  #
        self.bus.serial.parity = parity  # No parity
        self.bus.mode = mode  # RTU mode
        platform, on_pi = get_platform()
        assert on_pi
        self.board_name = platform
        self._cpu_temp_available = True
        self.max_cpu_temp = 85.  # °C

    @property
    def _cpu_temp(self):
        return CPUTemperature().temperature
