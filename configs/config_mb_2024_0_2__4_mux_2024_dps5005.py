import logging
from ohmpi.utils import get_platform
from paho.mqtt.client import MQTTv31  # noqa

_, on_pi = get_platform()
# DEFINE THE ID OF YOUR OhmPi
ohmpi_id = '0001' if on_pi else 'XXXX'
# DEFINE YOUR MQTT BROKER (DEFAULT: 'localhost')
mqtt_broker = 'localhost' if on_pi else 'NAME_YOUR_BROKER_WHEN_IN_SIMULATION_MODE_HERE'
# DEFINE THE SUFFIX TO ADD TO YOUR LOGS FILES
logging_suffix = ''

# OhmPi configuration
OHMPI_CONFIG = {
    'id': ohmpi_id,  # Unique identifier of the OhmPi board (string)
    'settings': 'ohmpi_settings.json',  # INSERT YOUR FAVORITE SETTINGS FILE HERE
}
r_shunt = 2.
HARDWARE_CONFIG = {
    'ctl': {'model': 'raspberry_pi'},
    'pwr': {'model': 'pwr_dps5005', 'voltage': 3., 'interface_name': 'modbus'},
    'tx':  {'model': 'mb_2024_0_2',
             'voltage_max': 50.,  # Maximum voltage supported by the TX board [V]
             'current_max': 4.8/(50*r_shunt)/5,  # Maximum voltage read by the current ADC on the TX board [A]
             'r_shunt': r_shunt,  # Shunt resistance in Ohms
             'interface_name': 'i2c',
             'vmn_hardware_offset': 2501.
            },
    'rx':  {'model': 'mb_2024_0_2',
             'coef_p2': 1.00,  # slope for conversion for ADS, measurement in V/V
             'latency': 0.010,  # latency in seconds in continuous mode
             'sampling_rate': 50,  # number of samples per second
             'interface_name': 'i2c'
            },
    'mux': {'boards':
                {'mux_02':
                     {'model': 'mux_2024_0_X',
                      'tca_address': None,
                      'tca_channel': 0,
                      'addr2': 'up',
                      'addr1': 'up',
                      # 'mcp_0': '0x26',
                      # 'mcp_1': '0x27',
                      'roles': {'A': 'X', 'B': 'Y', 'M': 'XX', 'N': 'YY'},
                      'cabling': {(i+8, j): ('mux_02', i) for j in ['A', 'B', 'M', 'N'] for i in range(1, 9)},
                      'voltage_max': 50.},
                'mux_03':
                     {'model': 'mux_2024_0_X',
                      'tca_address': None,
                      'tca_channel': 0,
                      'addr2': 'down',
                      'addr1': 'up',
                      # 'mcp_0': '0x26',
                      # 'mcp_1': '0x27',
                      'roles': {'A': 'X', 'B': 'Y', 'M': 'XX', 'N': 'YY'},
                      'cabling': {(i+24, j): ('mux_03', i) for j in ['A', 'B', 'M', 'N'] for i in range(1, 9)},
                      'voltage_max': 50.},
                 'mux_05':
                     {'model': 'mux_2024_0_X',
                      'tca_address': None,
                      'tca_channel': 0,
                      'addr2': 'up',
                      'addr1': 'down',
                      'roles': {'A': 'X', 'B': 'Y', 'M': 'XX', 'N': 'YY'},
                      'cabling': {(i+0, j): ('mux_05', i) for j in ['A', 'B', 'M', 'N'] for i in range(1, 9)},
                      'voltage_max': 50.},
                'mux_06':
                     {'model': 'mux_2024_0_X',
                      'tca_address': None,
                      'tca_channel': 0,
                      'addr2': 'down',
                      'addr1': 'down',
                      'roles': {'A': 'X', 'B': 'Y', 'M': 'XX', 'N': 'YY'},
                      'cabling': {(i+16, j): ('mux_06', i) for j in ['A', 'B', 'M', 'N'] for i in range(1, 9)},
                      'voltage_max': 50.},
                 },
             'default': {'interface_name': 'i2c_ext',
                         'voltage_max': 100.,
                         'current_max': 3.
                         }
            }
    }

# SET THE LOGGING LEVELS, MQTT BROKERS AND MQTT OPTIONS ACCORDING TO YOUR NEEDS
# Execution logging configuration
EXEC_LOGGING_CONFIG = {
    'logging_level': logging.INFO,
    'log_file_logging_level': logging.DEBUG,
    'logging_to_console': True,
    'file_name': f'exec{logging_suffix}.log',
    'max_bytes': 262144,
    'backup_count': 30,
    'when': 'd',
    'interval': 1
}

# Data logging configuration
DATA_LOGGING_CONFIG = {
    'logging_level': logging.INFO,
    'logging_to_console': True,
    'file_name': f'data{logging_suffix}.log',
    'max_bytes': 16777216,
    'backup_count': 1024,
    'when': 'd',
    'interval': 1
}

# State of Health logging configuration (For a future release)
SOH_LOGGING_CONFIG = {
    'logging_level': logging.INFO,
    'logging_to_console': True,
    'log_file_logging_level': logging.DEBUG,
    'file_name': f'soh{logging_suffix}.log',
    'max_bytes': 16777216,
    'backup_count': 1024,
    'when': 'd',
    'interval': 1
}

# MQTT logging configuration parameters
MQTT_LOGGING_CONFIG = {
    'hostname': mqtt_broker,
    'port': 1883,
    'qos': 2,
    'retain': False,
    'keepalive': 60,
    'will': None,
    'auth': {'username': 'mqtt_user', 'password': 'mqtt_password'},
    'tls': None,
    'protocol': MQTTv31,
    'transport': 'tcp',
    'client_id': f'{OHMPI_CONFIG["id"]}',
    'exec_topic': f'ohmpi_{OHMPI_CONFIG["id"]}/exec',
    'exec_logging_level': logging.DEBUG,
    'data_topic': f'ohmpi_{OHMPI_CONFIG["id"]}/data',
    'data_logging_level': DATA_LOGGING_CONFIG['logging_level'],
    'soh_topic': f'ohmpi_{OHMPI_CONFIG["id"]}/soh',
    'soh_logging_level': SOH_LOGGING_CONFIG['logging_level']
}

# MQTT control configuration parameters
MQTT_CONTROL_CONFIG = {
    'hostname': mqtt_broker,
    'port': 1883,
    'qos': 2,
    'retain': False,
    'keepalive': 60,
    'will': None,
    'auth': {'username': 'mqtt_user', 'password': 'mqtt_password'},
    'tls': None,
    'protocol': MQTTv31,
    'transport': 'tcp',
    'client_id': f'{OHMPI_CONFIG["id"]}',
    'ctrl_topic': f'ohmpi_{OHMPI_CONFIG["id"]}/ctrl'
}
