from utils import change_config
change_config('config_ohmpi_card_3_15.py', verbose=False)
from OhmPi.measure import OhmPiHardware

k = OhmPiHardware()
k._vab_pulse(vab=12, length=1., sampling_rate=20., polarity=1)
change_config('config_default.py', verbose=False)
