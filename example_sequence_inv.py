import warnings
import os
import numpy as np
import time
import matplotlib.pyplot as plt
warnings.filterwarnings('ignore')
os.chdir("/home/pi/OhmPi")
from ohmpi.ohmpi import OhmPi

### Define object from class OhmPi
k = OhmPi() #use_mux n'est plus necessaire ni idps car c'est inclus dans la config à varifier
print('update parameters')
### Update settings if needed 
k.update_settings({"injection_duration":0.250})
k.update_settings({"nb_stack":1})
k.update_settings({"nbr_electrode":64})
k.update_settings({"voltage_max":50})
#load sequence
k.load_sequence('ABMN.txt')
#Run contact resistance check
k.rs_check(tx_volt=2)
# ### Run sequence
#k.run_sequence(tx_volt =5. , strategy = 'vmax', dutycycle=0.95, vab_max = 50.,)
print('end')
#inversion
xzv = k.run_inversion(['/home/pi/OhmPi/data/measurements_20240127T085200.csv'], reg_mode=0, elec_spacing = 1.)
#plot
fig, axs = plt.subplots(len(xzv), 1, sharex=True, sharey=True, figsize=(10, 3))
axs = [axs] if len(xzv) == 1 else axs
 
for i, dic in enumerate(xzv):
    ax = axs[i]
    x, z = np.meshgrid(dic['x'], dic['z'])
    #cax = ax.contourf(x, z, np.log10(dic['rho']),cmap='jet')
    cax = ax.pcolormesh(x, z, np.log10(dic['rho']),cmap='jet')
    fig.colorbar(cax, ax=ax, label=r'$\log_{10}(\rho)$ [$\Omega$.m]')

a=np.zeros((16,2))
esp=0
for i in range(0,16):
    a[i,0]=esp
    esp=esp+0.03

ax.plot(a[:,0],a[:,1],'*r')

plt.show(block=True)



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
# out = k.run_measurement(quad=[1,4,2,3], tx_volt = 5, strategy = 'vmax', dutycycle=0.5, vab_max = 50.)
# 
# k.append_and_save('simple_measurement.csv', out)
### Plot de result
# data = out['full_waveform']
# inan = ~np.isnan(data[:,0])
# fig, axs = plt.subplots(2, 1, sharex=True)
# ax = axs[0]
# ax.plot(data[inan,0],data[inan,1], 'r.-', label='current [mA]')
# ax.set_ylabel('Current AB [mA]')
# ax.grid(True)
# ax = axs[1]
# ax.plot(data[inan,0], data[inan,2], '.-', label='voltage [mV]')
# ax.set_ylabel('Voltage MN [mV]')
# ax.set_xlabel('Time [s]')
# ax.legend()
# plt.grid(True)
# plt.show()
# plt.savefig('data.png')



