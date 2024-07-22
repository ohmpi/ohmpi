import matplotlib
matplotlib.use('TkAgg')
import time
from ohmpi.ohmpi import OhmPi

k = OhmPi()

if True:
    # from resistor board find max voltage that can be tried out (manually)
    k._hw.pwr_state = 'on'  # if you start with 'on' like in run_sequence()
    # dps isn't turned off between run_measurment() so more likely to get decay issue
    out1 = k.run_measurement([1, 4, 2, 3], injection_duration=0.5, vab_req=30, strategy='constant', duty_cycle=0.5)
    out = k.run_measurement([1, 4, 2, 3], injection_duration=0.5, vab_req=5, strategy='constant', duty_cycle=0.5)
    k._hw._plot_readings(save_fig=False)

# cannot use run_measurement as it doesn't modify the dps voltage

# trying a test at the ohmpi hardware level
# there is an unwanted delay between each pulse (maybe due to tx.sync_wait() ?)
# k._hw.pwr_state = 'on'
# k.switch_mux_on([1, 4, 2, 3])
# print(k._hw.tx._activation_delay, k._hw.tx._release_delay,
#  k._hw.tx.latency, k._hw.rx.latency)
# k._hw._vab_pulse(0.1, duration=1, polarity=1, append=True)
# k._hw._vab_pulse(12, duration=1, polarity=1, append=True)
# k._hw._vab_pulse(12, duration=1, polarity=1, append=True)
# k._hw._vab_pulse(5, duration=1, polarity=1, append=True)
# k._hw._vab_pulse(0.1, duration=1, polarity=1, append=True)
# k._hw._vab_pulse(0.1, duration=1, polarity=0, append=True)
# k.switch_mux_off([1, 4, 2, 3])
# k._hw._plot_readings(save_fig=False)

# lower level
def read_values(t0=None):
    if t0 is None:
        t0 = time.time()
    _readings = []
    for i in range(1000):
        r = [time.time() - t0, k._hw._pulse, k._hw.tx.polarity, k._hw.tx.current, k._hw.rx.voltage]
        _readings.append(r)
        time.sleep(0.01)
    k._hw.readings = np.array(_readings)

from threading import Thread
import numpy as np
import matplotlib.pyplot as plt

# k._hw.pwr_state = 'on'  # give current to dph
# k.switch_mux_on([1, 4, 2, 3])
# readings = Thread(target=read_values)
# readings.start()
# time.sleep(1)
# k._hw.tx.voltage = 5  # instruction but still not on
# # TODO k._hw.tx.pwr_state = 'on' doesn't to anything... just a flag?
# k._hw.tx.pwr.pwr_state = 'on'  # dph sending current
# time.sleep(1)
# k._hw.tx.polarity = 1
# time.sleep(1)
# k._hw.tx.polarity = 0
# time.sleep(1)
# k._hw.tx.polarity = -1
# time.sleep(1)
# k._hw.tx.pwr.pwr_state = 'off'  # dph stops
# time.sleep(1)
# readings.join()
# k.switch_mux_off([1, 4, 2, 3])
# k._hw._plot_readings(save_fig=False)

# rise and fall on polarity 1 for different Vab
if False:
    vabs = [1, 5, 10, 15, 20, 25, 30]
    traces = {}
    k._hw.pwr_state = 'on'
    k.switch_mux_on([1, 4, 2, 3])
    for vab in vabs:
        print('trying vab', vab)
        readings = Thread(target=read_values)
        k._hw.tx.voltage = vab
        k._hw.tx.polarity = 1
        readings.start()
        k._hw.tx.pwr.pwr_state = 'on'
        time.sleep(1)
        #k._hw.tx.pwr.pwr_state = 'off'
        k._hw.tx.voltage = 0.01
        time.sleep(4)
        readings.join()
        traces['Vab=' + str(vab)] = {'data': k._hw.readings}
    k._hw.pwr_state = 'off'
    k.switch_mux_off([1, 4, 2, 3])


# consecutive injection from high to low vab
if False:
    traces = {}
    k._hw.pwr_state = 'on'
    k.switch_mux_on([1, 4, 2, 3])
    #for wait_time in [0, 0.2, 0.5, 2]:
    for wait_time in [0.5]:
        print('wait_time', wait_time)
        tdic = {}
        t0 = time.time()
        readings = Thread(target=read_values, args=(t0,))
        k._hw.tx.voltage = 30
        k._hw.tx.polarity = 1
        readings.start()
        tdic['start'] = time.time() - t0
        k._hw.tx.pwr.pwr_state = 'on'
        tdic['turn on 1'] = time.time() - t0
        time.sleep(1)
        k._hw.tx.polarity = 0
        tdic['polarity 0'] = time.time() - t0
        #k._hw.tx.voltage = 5  # in this case, decay start from slightly lower
        #tdic['vab set 2'] = time.time() - t0
        k._hw.tx.pwr.pwr_state = 'off'  # start discharging
        tdic['turn off 1'] = time.time() - t0
        for i in range(10):
            k._hw.tx.pwr._retrieve_voltage()
            print(k._hw.tx.pwr._voltage)
            time.sleep(0.1)
        time.sleep(wait_time)
        k._hw.tx.pwr.pwr_state = 'on'
        tdic['turn on 2'] = time.time() - t0
        k._hw.tx.voltage = 5
        tdic['vab set'] = time.time() - t0
        k._hw.tx.polarity = 1
        tdic['polarity 1 (2)'] = time.time() - t0
        time.sleep(3)  # if time here too short we don't reach target voltage
        #k._hw.tx.polarity = 0
        k._hw.tx.pwr.pwr_state = 'off'
        tdic['turn off 2'] = time.time() - t0
        readings.join()
        tdic['end time 2'] = time.time() - t0
        print(tdic)
        traces['wait ' + str(wait_time) + 's'] = {
            'data': k._hw.readings,
            'tdic': tdic
        }
    k._hw.pwr_state = 'off'
    k.switch_mux_off([1, 4, 2, 3])

if False:
    # figure
    fig, axs = plt.subplots(2, 1, figsize=(8, 4), sharex=True)
    axs[0].set_ylabel('Current [mA]')
    axs[1].set_ylabel('Voltage [mV]')
    for key in traces:
        tdic = traces[key]['tdic']
        trace = traces[key]['data']
        cax = axs[0].plot(trace[:, 0], trace[:, -2], '.-', label=key)
        color = cax[0].get_color()
        axs[1].plot(trace[:, 0], trace[:, -1], '.-', color=color)
        for a in tdic:
            axs[0].axvline(tdic[a], color=color)
            axs[1].axvline(tdic[a], color=color)
    axs[0].legend()
    axs[1].set_xlabel('Time [s]')
    plt.show()

# k._hw.tx.voltage = 5
# time.sleep(2)
# k._hw.tx.pwr.pwr_state = 'off'

# k._hw.pwr_state = 'off'
