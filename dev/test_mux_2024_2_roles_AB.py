import time
from ohmpi.utils import change_config
import logging
change_config('../configs/config_mb_2023_mux_2024_2_roles_AB.py', verbose=False)
from ohmpi.hardware_components.mux_2024_rev_0_0 import Mux, MUX_CONFIG
from ohmpi.hardware_components import raspberry_pi_i2c as ctl_module
# from ohmpi.config import HARDWARE_CONFIG

stand_alone_mux = True  # Testing hardware component alone
part_of_hardware_system = False  # Testing hardware component as a part of the hardware system
within_ohmpi = False  # Testing hardware component as a part of the hardware system through the ohmpi object
update_mux_config = False
# Stand alone mux
if stand_alone_mux:
    MUX_CONFIG['ctl'] = ctl_module.Ctl()
    MUX_CONFIG['id'] = 'mux_1'
    MUX_CONFIG['cabling'] = {(i, j): ('mux_1', i) for j in ['A', 'B'] for i in range(1,17)}
    MUX_CONFIG['roles'] = {'A': 'X', 'B': 'Y'}
    MUX_CONFIG['mcp_0'] = '0x26'
    MUX_CONFIG['mcp_1'] = '0x27'

    mux = Mux(**MUX_CONFIG)
    mux.switch_one(elec=2, role='A', state='on')
    time.sleep(2)
    mux.switch_one(elec=2, role='A', state='off')
    mux.switch({'A': [2], 'B': [3]}, state='on')
    time.sleep(8)
    # mux.switch({'A': [1], 'B': [4], 'M': [2], 'N': [3]}, state='off')
    mux.reset()
    mux.test({'A': [i for i in range(1, 17)], 'B': [i for i in range(1, 17)]}, activation_time=.1)
    mux.reset()

# mux as part of a OhmPiHardware system
if part_of_hardware_system:
    from ohmpi.hardware_system import OhmPiHardware
    print('Starting test of mux as part of a OhmPiHardware system.')

    h = OhmPiHardware()
    h.exec_logger.setLevel(logging.DEBUG)

    # Test mux switching
    h.reset_mux()
    h.switch_mux(electrodes=[1, 4], roles=['A', 'B'], state='on')
    time.sleep(1.)
    h.switch_mux(electrodes=[1, 4], roles=['A', 'B'], state='off')

if within_ohmpi:
    from ohmpi.ohmpi import OhmPi
    print('Starting test of mux within OhmPi.')
    k = OhmPi()
    k.switch_mux_on([1, 4, 2, 3])
    time.sleep(1.)
    k.reset_mux()

change_config('../configs/config_default.py', verbose=False)
