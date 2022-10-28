import board  # noqa
import busio  # noqa
import time
from adafruit_mcp230xx.mcp23008 import MCP23008  # noqa
from digitalio import Direction  # noqa


i2c = busio.I2C(board.SCL, board.SDA)
mcp = MCP23008(i2c, address=0x20)

pin0 = mcp.get_pin(0)
pin0.direction = Direction.OUTPUT
pin1 = mcp.get_pin(1)
pin1.direction = Direction.OUTPUT


pin0.value = False
pin1.value = False

pin0.value = True
pin1.value = False
time.sleep(2)
