
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')

import numpy as np
from ohmpi.utils import change_config
change_config('../configs/config_mb_2023.py', verbose=False)
import os

from ohmpi.ohmpi import OhmPi
k = OhmPi()
# single inversion
#k.run_inversion(['measurement_20220206T194552.csv'])

# batch inversion
xzv = k.run_inversion([
    'measurements_20231130T215031.csv'
], reg_mode=0)

# make a contour figure with the output
fig, axs = plt.subplots(len(xzv), 1, sharex=True, sharey=True, figsize=(10, 6))
axs = [axs] if len(xzv) == 1 else axs
for i, dic in enumerate(xzv):
    ax = axs[i]
    x, z = np.meshgrid(dic['x'], dic['z'])
    cax = ax.contourf(x, z, np.log10(dic['rho']))
    fig.colorbar(cax, ax=ax, label=r'$\log_{10}(\rho)$ [$\Omega$.m]')
plt.show(block=True)

# restore default config
change_config('../configs/config_default.py', verbose=False)
