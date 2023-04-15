# import sys
# sys.path.extend(['/home/su530201/PycharmProjects/ohmpi_reversaal/OhmPi'])
from OhmPi.hardware.ohmpi_card_3_15 import Tx
from OhmPi.hardware.ohmpi_card_3_15 import Rx
from OhmPi.logging_setup import create_stdout_logger
import numpy as np

exec_logger = create_stdout_logger(name='exec')
soh_logger = create_stdout_logger(name='soh')

print('\nCreating TX...')
tx = Tx(exec_logger= exec_logger, soh_logger= soh_logger)
print('\nCreating RX...')
rx = Rx(exec_logger= exec_logger, soh_logger= soh_logger)

print(f'TX current: {tx.current:.3f} mA')
print(f'RX voltage: {rx.voltage:.3f} mV')

tx.polarity = 1
tx.inject(state='on')
tx.adc_gain_auto()
rx.adc_gain_auto()
r = []
for i in range(30):
    r.append(rx.voltage/tx.current)
    print(f'Resistance: {r[-1]:.3f}')
r = np.array(r)
print(f'Mean resistance: {np.mean(r):.3f} Ohms')
print(f'Resistance std: {np.std(r):.3f} Ohms')
print(f'Dev. {100. * np.std(r)/np.mean(r):.1} %')
