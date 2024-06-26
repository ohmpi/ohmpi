import os
import numpy as np
import time
os.chdir("/home/pi/OhmPi")
from ohmpi.ohmpi import OhmPi
from ohmpi.tests import contact_resistance_test_board

# Define object from class OhmPi
k = OhmPi()

# Set or load sequence
sequence = np.array([np.array([1,2,3,4])+k for k in range(29)]) # [[1,2,3,4],[2,3,4,5]...] but can actually make other combinations of AB to increase number of contact resistance tested
sequence = np.vstack([sequence,np.array([[30,31,1,2],[31,32,2,3]])])
sequence = sequence[-4:]
k.sequence = contact_resistance_test_board(sequence) # checks if sequence contains potential shortcut quads (AB odd odd or even even)

# Run contact resistance check
k.rs_check()

# Run sequence
k.run_sequence(strategy='vmax',vab=2., vab_max=5, nb_stack=2, injection_duration=.5, duty_cycle=1.)
