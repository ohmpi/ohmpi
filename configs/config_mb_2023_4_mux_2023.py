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

HARDWARE_CONFIG = {
    'ctl': {'model': 'raspberry_pi'},
    'pwr': {'model': 'pwr_batt', 'voltage': 12., 'interface_name': 'none'},
    'tx':  {'model': 'mb_2023_0_X',
             'voltage_max': 12.,  # Maximum voltage supported by the TX board [V]
             'adc_voltage_max': 4800.,  # Maximum voltage read by the current ADC on the TX board [mA]
             'r_shunt': 2.,  # Shunt resistance in Ohms
             'interface_name': 'i2c',
            },
    'rx':  {'model': 'mb_2023_0_X',
            'coef_p2': 2.50,  # slope for conversion for ADS, measurement in V/V
            'sampling_rate': 50.,  # number of samples per second
            'interface_name': 'i2c',
            },
    'mux':  # default properties given in config are system properties that will be
            # overwritten by properties defined in each the board dict below.
            # if defined in board specs, values out of specs will be bounded to remain in specs
            # omitted properties in config will be set to board specs default values if they exist
            {'boards':
                {'mux_A':
                     {'model': 'mux_2023_0_X',
                      'mux_tca_address': 0x70,
                      'roles': {'A': 'X'},
                      'cabling': {(i, j): ('mux_A', i) for j in ['A'] for i in range(1, 65)},
                      'voltage_max': 12.},
                 'mux_B':
                     {'model': 'mux_2023_0_X',
                      'mux_tca_address': 0x71,
                      'roles': {'B': 'X'},
                      'cabling': {(i, j): ('mux_B', i) for j in ['B'] for i in range(1, 65)},
                      'voltage_max': 12.},
                 'mux_M':
                     {'model': 'mux_2023_0_X',
                      'mux_tca_address': 0x72,
                      'roles': {'M': 'X'},
                      'cabling': {(i, j): ('mux_M', i) for j in ['M'] for i in range(1, 65)},
                      'voltage_max': 12.},
                'mux_N':
                     {'model': 'mux_2023_0_X',
                      'mux_tca_address': 0x73,
                      'roles': {'N': 'X'},
                      'cabling': {(i, j): ('mux_N', i) for j in ['N'] for i in range(1, 65)},
                      'voltage_max': 12.},
                 },
             'default': {'interface_name': 'i2c',
                         'voltage_max': 12.,
                         'current_max': 3.}
             }
}

# SET THE LOGGING LEVELS, MQTT BROKERS AND MQTT OPTIONS ACCORDING TO YOUR NEEDS
# Execution logging configuration
EXEC_LOGGING_CONFIG = {
    'logging_level': logging.INFO,  # TODO: set logging level back to INFO
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
