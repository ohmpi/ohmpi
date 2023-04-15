from OhmPi.measure import OhmPiHardware
from utils import change_config

change_config('config_ohmpi_card_3_15.py', verbose=False)
k = OhmPiHardware()
k._vab_pulse(vab=12, length=1., sampling_rate=100., polarity=1)
change_config('config_default.py', verbose=False)
