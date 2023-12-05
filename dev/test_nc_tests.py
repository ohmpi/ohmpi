from ohmpi.tests import *
import numpy as np
from ohmpi.config import (OHMPI_CONFIG,EXEC_LOGGING_CONFIG, DATA_LOGGING_CONFIG, SOH_LOGGING_CONFIG, MQTT_LOGGING_CONFIG,
                          MQTT_CONTROL_CONFIG)

from ohmpi.hardware_system import OhmPiHardware
from ohmpi.logging_setup import setup_loggers
from ohmpi.config import HARDWARE_CONFIG
import copy

# set loggers
mqtt = True
test_logger, _, _, _ = setup_test_logger(mqtt=mqtt)
exec_logger, _, data_logger, _, soh_logger, _, _, msg = setup_loggers(mqtt=mqtt)
print(msg)

# specify loggers when instancing the hardware
hw = OhmPiHardware(**{'exec_logger': exec_logger, 'data_logger': data_logger,
                           'soh_logger': soh_logger})
HARDWARE_CONFIG_nc = copy.deepcopy(HARDWARE_CONFIG)
print('config', HARDWARE_CONFIG_nc)
for k, v in HARDWARE_CONFIG_nc.items():
    if k == 'mux':
        HARDWARE_CONFIG_nc[k]['default'].update({'connect': False})
    else:
        HARDWARE_CONFIG_nc[k].update({'connect': False})

hw_nc = OhmPiHardware(**{'exec_logger': exec_logger, 'data_logger': data_logger,
                            'soh_logger': soh_logger}, hardware_config=HARDWARE_CONFIG_nc)


test_logger.info('OhmPi tests ready to start...')


test_mb_connection(hw_nc, "RX", test_logger.info)
test_mb_connection(hw_nc, "TX", test_logger.info)
test_mux_connection(hw_nc, test_logger.info)


test_vmn_hardware_offset(hw,test_logger.info)
test_dg411_gain_ratio(hw,test_logger.info)