from ohmpi.hardware_components import CtlAbstract
import board  # noqa
import busio  # noqa
import os
from ohmpi.utils import get_platform
from gpiozero import CPUTemperature  # noqa
import minimalmodbus  # noqa


class Ctl(CtlAbstract):
    def __init__(self, **kwargs):
        kwargs.update({'board_name': os.path.basename(__file__).rstrip('.py')})
        super().__init__(**kwargs)
        self.bus = minimalmodbus.Instrument(port='/dev/ttyUSB0', slaveaddress=1)  # port name, address (decimal)
        self.configure_modbus() # TODO: check if this works on init
        platform, on_pi = get_platform()
        assert on_pi
        self.board_name = platform
        self._cpu_temp_available = True
        self.max_cpu_temp = 85.  # °C

    @property
    def _cpu_temp(self):
        return CPUTemperature().temperature

    def configure_modbus(self, baudrate=9600, bitesize=8, timeout=1, debug=False, parity='N',
                         mode=minimalmodbus.MODE_RTU):
        self.bus.serial.baudrate = baudrate  # Baud rate 9600 as listed in doc
        self.bus.serial.bytesize = bitesize  #
        self.bus.serial.timeout = timeout  # greater than 0.5 for it to work
        self.bus.debug = debug  #
        self.bus.serial.parity = parity  # No parity
        self.bus.mode = mode # RTU mode