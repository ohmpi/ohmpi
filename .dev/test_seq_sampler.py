import os
import numpy as np
import time
os.chdir("/home/pi/OhmPi")
from ohmpi.ohmpi import OhmPi
from ohmpi.utils import sequence_sampler

# Define object from class OhmPi
k = OhmPi()

# Update settings if needed
k.update_settings({"injection_duration": 1.})
k.update_settings({"strategy": "constant"})
k.update_settings({"tx_volt": 3.})
k.update_settings({"nb_stack": 2})

# Set or load sequence
k.create_sequence(32)    # set numpy array of shape (n,4)
# k.load_sequence('sequences/ABMN.txt')    # load sequence from a local file
print(sequence_sampler(k.sequence),n_samples=20)
vab = k.find_optimal_vab_for_sequence(n_samples=20)

# Run contact resistance check
k.rs_check()

# Run sequence
k.run_sequence()
