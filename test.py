from ohmpi import OhmPi
import matplotlib.pyplot as plt
import numpy as np

k = OhmPi(idps=True)
k.rs_check()

x = []
for i in range(1):
    out = k.run_measurement(injection_duration=0.5, nb_stack=1, tx_volt=0, autogain=True, best_tx_injtime=0.2)
    x.append(out['R [ohm]'])


data = out['fulldata']
inan = ~np.isnan(data[:,0])

if True:
    plt.plot(data[inan,2], data[inan,0], '.-', label='current [mA]')
    plt.plot(data[inan,2], data[inan,1], '.-', label='voltage [mV]')
    plt.legend()
    plt.show()


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
