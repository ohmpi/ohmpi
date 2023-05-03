import board  # noqa
import busio  # noqa
import time
import adafruit_ads1x15.ads1115 as ads  # noqa
from adafruit_ads1x15.analog_in import AnalogIn 
from adafruit_mcp230xx.mcp23008 import MCP23008  # noqa
import digitalio  # noqa
from digitalio import Direction  # noqa
from gpiozero import CPUTemperature  # noqa
import minimalmodbus

#Initialisation du module d'injection de current
DPS = minimalmodbus.Instrument(port='/dev/ttyUSB0', slaveaddress=1) # port name, slave address (in decimal)
DPS.serial.baudrate = 9600                      # Baud rate 9600 as listed in doc
DPS.serial.bytesize = 8                         # 
DPS.serial.timeout  = 1                         # > a 0.5 pour que cela fonctionne
DPS.debug           = False                     # 
DPS.serial.parity   = 'N'                       # No parity
DPS.mode            = minimalmodbus.MODE_RTU    # RTU mode

DPS.write_register(0x0001, 40, 0)  # (last number) 0 is for mA, 3 is for A
DPS.write_register(0x0000, 5, 0)  self.pwr.write_register(0x0000, tx_volt, 2)