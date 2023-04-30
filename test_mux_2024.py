import time
from utils import change_config
import logging
change_config('config_mb_2023_mux_2024.py', verbose=False)
from OhmPi.hardware_components.mux_2024_rev_0_0 import Mux, MUX_CONFIG
from OhmPi.hardware_components import raspberry_pi as controller_module

stand_alone_mux = False
part_of_hardware_system = True
# Stand alone mux
if stand_alone_mux:
    MUX_CONFIG['controller'] = controller_module.Controller()
    MUX_CONFIG['id'] = 'mux_1'
    MUX_CONFIG['default_mux_cabling'] = {(i+8, j) : ('mux_1', i) for j in ['A', 'B', 'M', 'N'] for i in range(1,9)}
    mux = Mux(**MUX_CONFIG)
    mux.switch_one(elec=9, role='M', state='on')
    time.sleep(2)
    mux.switch_one(elec=9, role='M', state='off')
    mux.switch({'A': [9], 'B': [12], 'M': [10], 'N': [11]}, state='on')
    time.sleep(8)
    #mux.switch({'A': [1], 'B': [4], 'M': [2], 'N': [3]}, state='off')
    mux.reset()
    mux.test({'A': [9, 10, 11, 12, 13, 14, 15, 16], 'B': [9, 10, 11, 12, 13, 14, 15, 16],
              'M': [9, 10, 11, 12, 13, 14, 15, 16], 'N': [9, 10, 11, 12, 13, 14, 15, 16]}, activation_time=.1)

# mux as part of a OhmPiHardware system
if part_of_hardware_system:
    from OhmPi.hardware_system import OhmPiHardware
    print('Starting test of mux as part of a OhmPiHardware system.')
    k = OhmPiHardware()
    k.exec_logger.setLevel(logging.DEBUG)

    # Test mux switching
    k.reset_mux()
    k.switch_mux(electrodes=[1,4,2,3], roles=['A', 'B', 'M', 'N'], state='on')
    time.sleep(1.)
    k.switch_mux(electrodes=[1,4,2,3], roles=['A', 'B', 'M', 'N'], state='off')

change_config('config_default.py', verbose=False)