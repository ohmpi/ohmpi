import os
import numpy as np
import time
os.chdir("/home/pi/OhmPi")
from ohmpi import OhmPi

### Define object from class OhmPi
k = OhmPi()

### Update settings if needed 
k.update_settings({"injection_duration":0.2})

### Set or load sequence
k.sequence = np.array([[1,2,3,4]])    # set numpy array of shape (n,4)
# k.load_sequence('sequences/ABMN.txt')    # load sequence from a local file

### Run contact resistance check
# k.rs_check()

### Run sequence
k.run_sequence()
