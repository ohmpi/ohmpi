import time
from ohmpi.utils import change_config
from ohmpi.plots import plot_exec_log
import logging
change_config('../configs/config_mb_2023_2_mux_2024.py', verbose=False)
from ohmpi.hardware_components.mux_2024_rev_0_0 import Mux, MUX_CONFIG
from ohmpi.hardware_components import raspberry_pi_i2c as ctl_module
# from ohmpi.config import HARDWARE_CONFIG

stand_alone_mux = False
part_of_hardware_system = False
within_ohmpi = True
# Stand alone mux
if stand_alone_mux:
    MUX_CONFIG['ctl'] = ctl_module.Ctl()
    MUX_CONFIG['id'] = 'mux_1'
    MUX_CONFIG['cabling'] = {(i+8, j) : ('mux_1', i) for j in ['A', 'B', 'M', 'N'] for i in range(1,9)}
    mux = Mux(**MUX_CONFIG)
    mux.switch_one(elec=9, role='M', state='on')
    time.sleep(2)
    mux.switch_one(elec=9, role='M', state='off')
    mux.switch({'A': [9], 'B': [12], 'M': [10], 'N': [11]}, state='on')
    time.sleep(8)
    # mux.switch({'A': [1], 'B': [4], 'M': [2], 'N': [3]}, state='off')
    mux.reset()
    mux.test({'A': [9, 10, 11, 12, 13, 14, 15, 16], 'B': [9, 10, 11, 12, 13, 14, 15, 16],
              'M': [9, 10, 11, 12, 13, 14, 15, 16], 'N': [9, 10, 11, 12, 13, 14, 15, 16]}, activation_time=.1)

# mux as part of a OhmPiHardware system
if part_of_hardware_system:
    from ohmpi.hardware_system import OhmPiHardware
    print('Starting test of mux as part of a OhmPiHardware system.')

    k = OhmPiHardware()
    k.exec_logger.setLevel(logging.DEBUG)

    # Test mux switching
    k.reset_mux()
    k.switch_mux(electrodes=[1, 4, 2, 3], roles=['A', 'B', 'M', 'N'], state='on')
    time.sleep(1.)
    k.switch_mux(electrodes=[1, 4, 2, 3], roles=['A', 'B', 'M', 'N'], state='off')

if within_ohmpi:
    from ohmpi.ohmpi import OhmPi
    print('Starting test of mux within OhmPi.')
    k = OhmPi()
    k.reset_mux()
    k._hw.switch_mux([1, 4, 2, 3], state='on')
    k._hw.vab_square_wave(12,1)
    k._hw.switch_mux([1, 4, 2, 3], state='off')
    k._hw._plot_readings()
    plot_exec_log('../ohmpi/logs/exec.log')
change_config('../configs/config_default.py', verbose=False)