import warnings
import os
import numpy as np
import time
import matplotlib.pyplot as plt
warnings.filterwarnings('ignore')
from ohmpi.ohmpi import OhmPi

### Define object from class OhmPi
k = OhmPi() 
print('update parameters')
### Update settings if needed 
k.update_settings({"injection_duration":0.250})
k.update_settings({"nb_stack":1})
k.update_settings({"nbr_electrode":64})
k.update_settings({"voltage_max":50})
#load sequence
k.load_sequence('sequences/ABMN.txt')
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


