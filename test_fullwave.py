import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

fnames = sorted(os.listdir('data'))
df = pd.read_csv('out.csv', engine='python')
df

ct = df.columns[df.columns.str.match('t\d+')]
ci = df.columns[df.columns.str.match('i\d+')]
cu = df.columns[df.columns.str.match('u\d+')]

fig, axs = plt.subplots(2, 1, sharex=True)
for i in range(df.shape[0]):
    print(i)
    data = np.c_[df.loc[i, ct], df.loc[i, ci], df.loc[i, cu]].astype(float)
    inan = ~(np.isnan(data).any(1))
    label = ', '.join(df.loc[i, ['A', 'B', 'M', 'N']].astype(str).to_list())
    ax = axs[0]
    ax.plot(data[inan,0], data[inan,1], '.-', label=label)
    ax.set_ylabel('Current AB [mA]')
    ax.legend()
    ax = axs[1]
    ax.plot(data[inan,0], data[inan,2], '.-', label=label)
    ax.set_ylabel('Voltage MN [mV]')
    ax.set_xlabel('Time [s]')
plt.show()
