# import sys
# sys.path.extend(['/home/su530201/PycharmProjects/OhmPi'])
from ohmpi.hardware_components.dummy_tx import Tx
from ohmpi.hardware_components.dummy_rx import Rx
from ohmpi.logging_setup import create_stdout_logger

exec_logger = create_stdout_logger(name='exec')
soh_logger = create_stdout_logger(name='soh')

print('\nCreating TX...')
tx = Tx(exec_logger=exec_logger, soh_logger=soh_logger)
print('\nCreating RX...')
rx = Rx(exec_logger=exec_logger, soh_logger=soh_logger)
