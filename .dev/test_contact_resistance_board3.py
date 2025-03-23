import os
import numpy as np
import time
os.chdir("/home/pi/OhmPi")
from ohmpi.ohmpi import OhmPi
#from ohmpi.tests import contact_resistance_test_board

#######################

strategy = 'constant'
min_agg = True
r_ground = 5
vab_min = None
vab_req = 5.
vab_max = 12.
iab_min = 0.0025
iab_req = 0.005
iab_max = None
vmn_min = 0.75
vmn_req = 2.
vmn_max = None
pab_min = 0.0125
pab_req = 0.0625
pab_max = None

#######################

# Define object from class OhmPi
k = OhmPi()
k.reset_mux()
# Set or load sequence
sequence = np.array([np.array([1,2,3,4])+k for k in range(29)]) # [[1,2,3,4],[2,3,4,5]...] but can actually make other combinations of AB to increase number of contact resistance tested
sequence = np.vstack([sequence,np.array([[30,31,2,1],[31,32,3,2]])])
#sequence = sequence[:2]
#k.sequence = contact_resistance_test_board(sequence) # checks if sequence contains potential shortcut quads (AB odd odd or even even)
k.sequence = sequence

if strategy == 'vmin':
    k.update_settings({'strategy': strategy, 'vmn_req': vmn_req})
    k.update_settings({'export_path':f'data/r{r_ground}_{strategy}_{vmn_req:.1f}.csv'})

elif strategy == 'vmax':
    k.update_settings({'strategy': strategy})
    k.update_settings({'export_path':f'data/r{r_ground}_{strategy}.csv'})
elif strategy == 'flex':
    k.update_settings({'strategy': strategy})
    k.update_settings({'vab_min': vab_min, 'vab_req': vab_req, 'vab_max': vab_max, 'iab_min': iab_min, 'iab_req': iab_req, 'iab_max': iab_max, 
                       'vmn_min': vmn_min, 'vmn_req': vmn_req, 'vmn_max': vmn_max, 'pab_min': pab_min, 'pab_req': pab_req, 'pab_max': pab_max, 'min_agg': min_agg}) 
    k.update_settings({'export_path':f'data/r{r_ground}_{strategy}_vab-{vab_min}-{vab_req}-{vab_max}_iab-{iab_min}-{iab_req}-{iab_max}_vmn-{vmn_min}-{vmn_req}-{vmn_max}_pab-{pab_min}-{pab_req}-{pab_max}_{min_agg}.csv'})

elif strategy == "constant":
    k.update_settings({'strategy': strategy})
    k.update_settings({'vab_min': vab_min, 'vab_req': vab_req, 'vab_max': vab_max}) 
    k.update_settings({'export_path':f'data/r{r_ground}_{strategy}_vab_req-{vab_req}-vab_max-{vab_max}.csv'})

print(f'Settings: {k.settings}')
# Run contact resistance check
#k.rs_check()
#print('TX',k._hw.tx.specs, 'PWR', k._hw.pwr.specs, 'RX', k._hw.rx.specs)
#print(k._hw.vab_min)
# Run sequence
#kwargs = {'vab_square_wave':{'append':False}}
k.run_sequence(nb_stack=2, injection_duration=.5, duty_cycle=1.,save_strategy_fw=True)
#k.plot_last_fw()
