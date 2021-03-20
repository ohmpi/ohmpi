import time , board, busio, numpy, os, sys, json, glob,os.path,adafruit_tca9548a
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from pandas import DataFrame
from datetime import datetime
from adafruit_mcp230xx.mcp23008 import MCP23008
from adafruit_mcp230xx.mcp23017 import MCP23017
import digitalio
from digitalio import Direction
current_time = datetime.now()
print(current_time.strftime("%Y-%m-%d %H:%M:%S"))
"""
hardware parameters
"""
R_shunt = 0.2# reference resistance value in ohm
coef_p2 = 2.50# slope for current conversion for ADS.P2, measurement in V/V
coef_p3 = 2.50 # slope for current conversion for ADS.P3, measurement in V/V
offset_p2= 0
offset_p3= 0
integer=10
meas=numpy.zeros((3,integer))

"""
import parameters
"""

with open('ohmpi_param.json') as json_file:
    pardict = json.load(json_file)


i2c = busio.I2C(board.SCL, board.SDA) #activation du protocle I2C
mcp = MCP23008(i2c, address=0x20) #connexion I2C MCP23008, injection de courant
ads_current = ADS.ADS1115(i2c, gain=16,data_rate=860, address=0X48)# connexion ADS1115, pour la mesure de courant
ads_voltage = ADS.ADS1115(i2c, gain=2/3,data_rate=860, address=0X49)# connexion ADS1115, pour la mesure de courant
#initialisation desvoie pour la polarité
pin0 = mcp.get_pin(0)
pin0.direction = Direction.OUTPUT
pin0.value = False
pin0.value = False
   
