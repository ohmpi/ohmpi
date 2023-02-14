from ohmpi import OhmPi
import matplotlib.pyplot as plt
import numpy as np

a = np.arange(13) + 49
b = a + 3
m = a + 1
n = a + 2
seq = np.c_[a, b, m, n]

k = OhmPi(idps=False)
k.settings['injection_duration'] = 1
k.settings['nb_stack'] = 1
k.settings['nbr_meas'] = 1
k.sequence = seq
k.reset_mux()
# k.sequence = np.array([[1,4,2,3]])
k.run_sequence()
#k.measure(strategy='vmax')
#print('vab', k.compute_tx_volt(strategy='vmin'))
#k.rs_check()
#out = k.run_measurement(quad=[3, 3, 3, 3], nb_stack=1, tx_volt=12, strategy='constant', autogain=True)

#k.rs_check(tx_volt=12)

# x = []
#for i in range(3):
#    out = k.run_measurement(injection_duration=2, nb_stack=2, strategy='constant', tx_volt=5, autogain=False)
    #x.append(out['R [ohm]'])
    #k.append_and_save('out.csv', out)

data = out['fulldata']
inan = ~np.isnan(data[:,0])

if True:
    fig, axs = plt.subplots(2, 1, sharex=True)
    ax = axs[0]
    ax.plot(data[inan,2], data[inan,0], 'r.-', label='current [mA]')
    ax.set_ylabel('Current AB [mA]')
    ax = axs[1]
    ax.plot(data[inan,2], data[inan,1], '.-', label='voltage [mV]')
    ax.set_ylabel('Voltage MN [mV]')
    ax.set_xlabel('Time [s]')
    plt.show()
    
#     fig,ax=plt.subplots()
#     
#    
#     ax.plot(data[inan,2], data[inan,0],  label='current [mA]', marker="o")
#     ax2=ax.twinx()
#     ax2.plot(data[inan,2], data[inan,1],'r.-' , label='current [mV]')
#     ax2.set_ylabel('Voltage [mV]', color='r')
#     ymin=-50
#     ymax=50
#     ymin1=-4500
#     ymax1= 4500
#     ax.set_ylim([ymin,ymax])
#     ax2.set_ylim([ymin1,ymax1])
#     
#     plt.show()
    


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
