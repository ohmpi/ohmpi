import numpy as np
from utils import change_config
change_config('config_ohmpi_card_3_15.py', verbose=False)
from OhmPi.measure import OhmPiHardware

k = OhmPiHardware()
k._vab_pulse(vab=12, length=1., sampling_rate=10., polarity=1)
r = k.readings[:,2]/k.readings[:,1]
print(f'Mean resistance: {np.mean(r):.3f} Ohms, Dev. {100*np.std(r)/np.mean(r):.1f} %')
change_config('config_default.py', verbose=False)
