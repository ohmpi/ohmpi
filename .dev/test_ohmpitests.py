import matplotlib
matplotlib.use('TkAgg')
from ohmpi.utils import change_config
change_config('../configs/config_mb_2024_0_2__2_mux_2024_dps5005.py', verbose=False)
import importlib
import time
import logging
from ohmpi.test import OhmPiTests

k = OhmPiTests()