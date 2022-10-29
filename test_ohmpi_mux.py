# test ohmpi and multiplexer on test resistances
from ohmpi import OhmPi
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os

# configure testing
idps = False
board_version = '22.10' # v2.0
use_mux = True
start_elec = 17  # start elec
nelec = 16  # max elec in the sequence for testing

# nelec electrodes Wenner sequence
a = np.arange(nelec-3) + start_elec
b = a + 3
m = a + 1
n = a + 2
seq = np.c_[a, b, m, n]

# testing measurement board only
k = OhmPi(idps=idps, use_mux=use_mux)
k.sequence = seq  # we need a sequence for possibly switching the mux
k.reset_mux()  # just for safety
if use_mux:
    k.switch_mux_on(seq[:, 0])
out1 = k.run_measurement(injection_duration=0.25, nb_stack=4, strategy='constant', tx_volt=12, autogain=True)
out2 = k.run_measurement(injection_duration=0.5, nb_stack=2, strategy='vmin', tx_volt=5, autogain=True)
out3 = k.run_measurement(injection_duration=1, nb_stack=1, strategy='vmax', tx_volt=5, autogain=True)
if use_mux:
    k.switch_mux_off(seq[:, 0])

# visual figure of the full wave form
fig, axs = plt.subplots(2, 1, sharex=True)
ax = axs[0]
labels = ['constant', 'vmin', 'vmax']
for i, out in enumerate([out1, out2, out3]):
  data = out['fulldata']
  inan = ~(np.isnan(out['fulldata']).any(1))
  ax.plot(data[inan,2], data[inan,0], '.-', label=labels[i])
ax.set_ylabel('Current AB [mA]')
ax.legend()
ax = axs[1]
for i, out in enumerate([out1, out2, out3]):
  data = out['fulldata']
  inan = ~(np.isnan(out['fulldata']).any(1))
  ax.plot(data[inan,2], data[inan,1], '.-', label=labels[i])
ax.set_ylabel('Voltage MN [mV]')
ax.set_xlabel('Time [s]')
fig.savefig('check-fullwave.jpg')


# test a sequence
if use_mux:
    # manually edit default settings
    k.settings['injection_duration'] = 1
    k.settings['nb_stack'] = 1
    #k.settings['nbr_meas'] = 1
    k.sequence = seq
    k.reset_mux()

    # set quadrupole manually
    k.switch_mux_on(seq[0, :])
    out = k.run_measurement(quad=[3, 3, 3, 3], nb_stack=1, tx_volt=12, strategy='constant', autogain=True)
    k.switch_mux_off(seq[0, :])
    print(out)

    # run rs_check() and save data
    k.rs_check()  # check all electrodes of the sequence

    # check values measured
    fname = sorted(os.listdir('data/'))[-1]
    print(fname)
    dfrs = pd.read_csv('data/' + fname)
    fig, ax = plt.subplots()
    ax.hist(dfrs['RS [kOhm]'])
    ax.set_xticks(np.arange(dfrs.shape[0]))
    ax.set_xticklabels(dfrs['A'].astype(str) + ' - ' +
                       dfrs['B'].astype(str), rotation=90)
    ax.set_ylabel('Contact resistances [kOhm]')
    fig.tight_layout()
    fig.savefig('check-rs.jpg')

    # run sequence synchronously and save data to file
    k.run_sequence(nb_stack=1, injection_duration=0.25)

    # check values measured
    fname = sorted(os.listdir('data/'))[-1]
    print(fname)
    df = pd.read_csv('data/' + fname)
    fig, ax = plt.subplots()
    ax.hist(df['R [ohm]'])
    ax.set_ylabel('Transfer resistance [Ohm]')
    ax.set_xticks(np.arange(df.shape[0]))
    ax.set_xticklabels(df['A'].astype(str) + ','
                       + df['B'].astype(str) + ','
                       + df['M'].astype(str) + ','
                       + df['N'].astype(str), rotation=90)
    fig.tight_layout()
    fig.savefig('check-r.jpg')

    # run sequence asynchronously and save data to file
    k.run_sequence_async(nb_stack=1, injection_duration=0.25)
    time.sleep(2)
    k.interrupt()  # will kill the asynchronous sequence running

    # run a series of asynchronous sequences
    k.run_multiple_sequences(nb_stack=1, injection_duration=0.25)
    time.sleep(2)
    k.interrupt()


# look at the noise frequency with FFT
if False:
    from numpy.fft import fft, ifft

    x = data[inan, 1][10:300]
    t = np.linspace(0, len(x)*4, len(x))
    sr = 1/0.004

    X = fft(x)
    N = len(X)
    n = np.arange(N)
    T = N/sr
    freq = n/T 

    plt.figure(figsize = (12, 6))
    plt.subplot(121)

    plt.stem(freq, np.abs(X), 'b', \
             markerfmt=" ", basefmt="-b")
    plt.xlabel('Freq (Hz)')
    plt.ylabel('FFT Amplitude |X(freq)|')
    #plt.xlim(0, 10)

    plt.subplot(122)
    plt.plot(t, ifft(X), 'r')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.tight_layout()
    plt.show()
