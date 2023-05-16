import numpy as np
import logging
import matplotlib.pyplot as plt
from utils import change_config
change_config('config_mb_2023_mux_2024.py', verbose=False)
from OhmPi.hardware_system import OhmPiHardware

k = OhmPiHardware()
k.exec_logger.setLevel(logging.INFO)

# Test _vab_pulse:
print('Testing positive _vab_pulse')
k._vab_pulse(vab=12, length=1., sampling_rate=k.rx.sampling_rate, polarity=1)
r = k.readings[:,4]/k.readings[:,3]
print(f'Mean resistance: {np.mean(r):.3f} Ohms, Dev. {100*np.std(r)/np.mean(r):.1f} %')
print(f'sampling rate: {k.rx.sampling_rate:.1f} ms, mean sample spacing: {np.mean(np.diff(k.readings[:,0]))*1000.:.1f} ms')
print('\nTesting negative _vab_pulse')
k._vab_pulse(vab=12, length=1., sampling_rate=k.rx.sampling_rate, polarity=-1)
r = k.readings[:,4]/k.readings[:,3]
print(f'Mean resistance: {np.mean(r):.3f} Ohms, Dev. {100*np.std(r)/np.mean(r):.1f} %')
print(f'sampling rate: {k.rx.sampling_rate:.1f} ms, mean sample spacing: {np.mean(np.diff(k.readings[:,0]))*1000.:.1f} ms')

# Test vab_square_wave:
print('\n\nTesting vab_square_wave')
cycles=3
cycle_length = 1.
k.vab_square_wave(vab=12, cycle_length=cycle_length, sampling_rate=k.rx.sampling_rate, cycles=cycles)
r = k.readings[:,4]/k.readings[:,3]
print(f'Mean resistance: {np.mean(r):.3f} Ohms, Dev. {100*np.std(r)/np.mean(r):.1f} %')
print(f'sampling rate: {k.rx.sampling_rate:.1f} ms, mean sample spacing: {np.mean(np.diff(k.readings[:,0]))*1000.:.1f} ms')
print(f'length of array: {len(r)}, expected length: {cycle_length*cycles*1000./k.rx.sampling_rate}')

# Plot graphs
fig, ax = plt.subplots()
ax.plot(k.readings[:,0], k.readings[:,3], '-r', marker='.', label='iab')
ax.set_ylabel('Iab [mA]')
ax2 = ax.twinx()
ax2.plot(k.readings[:,0], k.readings[:,2]*k.readings[:,4], '-b', marker='.', label='vmn')
ax2.set_ylabel('Vmn [mV]')
fig.legend()
plt.show()

# Compute resistances corrected for SP
print(f'SP: {k.sp} mV')
r = ((k.readings[:,4]-k.readings[:,2]*k.sp)/k.readings[:,3])
print(f'Mean resistance with sp correction : {np.mean(r):.3f} Ohms, Dev. {100*np.std(r)/np.mean(r):.1f} %')
print('\nTesting with pulses')
r = [np.abs((k.pulses[i]['polarity']*k.pulses[i]['vmn']-k.sp)/k.pulses[i]['iab']) for i in k.pulses.keys()]
for i in range(len(r)):
    print(f'Mean resistance with sp correction for pulse{i}: {np.mean(r[i]):.3f} Ohms, Dev. {100*np.std(r[i])/np.mean(r[i]):.1f} %')

change_config('config_default.py', verbose=False)

