import os
import numpy as np
import time
import matplotlib.pyplot as plt
os.chdir("/home/pi")
from ohmpi.ohmpi import OhmPi

### Define object from class OhmPi
k = OhmPi() #use_mux n'est plus necessaire ni idps car c'est inclus dans la config à varifier
print('update parameters')


### Update settings if needed 
k.update_settings({"injection_duration":1})
k.update_settings({"nb_stack":1})
k.update_settings({"nbr_electrode":64})
k.update_settings({"voltage_max":50})

#TODO: trouver les paramètres qu'il faut ajuster
# #k.test_mux()
# print('reset mux')
# k.reset_mux()
# ### Set or load sequence
# #k.sequence = np.array([[1,4,2,3]])    # set numpy array of shape (n,4)
# # k.set_sequence('1 2 3 4\n2 3 4 5')    # call function set_sequence and pass a string

# ### Run contact resistance check
#######k.rs_check(tx_volt=2)
# ### Run sequence
######k.run_sequence(tx_volt = 5, strategy = 'vmax', dutycycle=0.5, vab_max = 50.)
# # k.run_sequence_async()
# # time.sleep(2)
# # k.interrupt()
# k.reset_mux()
# k.switch_mux_on([1,16,5,11])
# # 
out = k.run_measurement(quad=[17,20,18,19], tx_volt = 20, strategy = 'constant', dutycycle=0.5, vab_max = 50.)
# 
#k.append_and_save('simple_measurement.csv', out)
### Plot de result
data = out['full_waveform']
inan = ~np.isnan(data[:,0])
fig, axs = plt.subplots(2, 1, sharex=True)
ax = axs[0]
ax.plot(data[inan,0],data[inan,1], 'r.-', label='current [mA]')
ax.set_ylabel('Current AB [mA]')
ax.grid(True)
ax = axs[1]
ax.plot(data[inan,0], data[inan,2], '.-', label='voltage [mV]')
ax.set_ylabel('Voltage MN [mV]')
ax.set_xlabel('Time [s]')
ax.legend()
plt.grid(True)
plt.show()
# plt.savefig('data.png')



