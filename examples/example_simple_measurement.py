import os
import numpy as np
import time
os.chdir("/home/pi/OhmPi")
from ohmpi.ohmpi import OhmPi

# Define object from class OhmPi
k = OhmPi()

# Update settings if needed
k.update_settings({"injection_duration": 1.})
k.update_settings({"strategy": "constant"})
k.update_settings({"vab_req": 3.})
k.update_settings({"nb_stack": 2})

# Set or load sequence
quad = [1,4,2,3]    # set numpy array of shape (n,4)

# Run sequence
k.run_measurement(quad)
k.plot_last_fw()
