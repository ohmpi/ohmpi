import matplotlib
matplotlib.use('TkAgg')
from ohmpi.utils import change_config
change_config('../configs/config_mb_2024_0_2__4_mux_2024_dps5005.py', verbose=False)
import importlib
import time
import logging
from ohmpi.config import HARDWARE_CONFIG
from ohmpi.ohmpi import OhmPi

k = OhmPi()
k.pwr_state = 'on'
k._hw.tx.voltage = 50
k._hw.tx.pwr.pwr_state = 'on'
time.sleep(.5)
k._hw.tx.voltage = 5
time.sleep(.5)
k._hw.tx.pwr.pwr_state = 'off'

k.pwr_state = 'off'
