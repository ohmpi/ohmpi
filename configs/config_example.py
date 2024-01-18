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
    'pwr': {'model': 'pwr_batt', 'voltage': 12., 'interface_name': 'none'},
    'tx':  {'model': 'mb_2024_0_2',
             'voltage_max': 50.,  # Maximum voltage supported by the TX board [V]
             'current_max': 4.80/(50*r_shunt),  # Maximum current read by the current ADC on the TX board [A]
             'r_shunt': r_shunt,  # Shunt resistance in Ohms
             'interface_name': 'i2c'
            },
    'rx':  {'model': 'mb_2024_0_2',
             'latency': 0.010,  # latency in seconds in continuous mode
             'sampling_rate': 50,  # number of samples per second
             'interface_name': 'i2c'
            },
    'mux': {'boards':
                {'mux_00':
                     {'model': 'mux_2024_0_X',
                      'electrodes': range(1, 17),
                      'roles': ['A', 'B', 'M', 'N'],
                      'tca_address': None,
                      'tca_channel': 0,
                      'addr1': 'down',
                      'addr2': 'down',
                      },
                'mux_01':
                    {'model': 'mux_2023_0_X',
                     'electrodes': range(17, 65 + 16),
                     'roles': 'A',
                     'mux_tca_address': 0x71
                     }
                 },
             'default': {'interface_name': 'i2c_ext',
                         'voltage_max': 50.,
                         'current_max': 3.}
            }
    }

'''
    Dictionary configuring the hardware system. This is where the five modules are declared and assembled together.
  
    Parameters
    ----------
    'ctl': dict
           Describing the controller unit with the following keys:
            * 'model': string
                       name of python module in ohmpi.hardware_components defining of the controller.
                       Currently only 'raspberry_pi'.
    'pwr': dict
           Describing the power module with the following keys:
            * 'model' (string): Name of python module in ohmpi.hardware_components defining the power component. 
                                Currently only 'pwr_batt' or 'pwr_dps5005'.
            * 'voltage' (float): Default voltage in V
            * 'interface_name' (string): Name of the interface. 'none', 'modbus'
    'tx': dict
          Describing the TX module with the following keys:
            * 'model' (string): Name of python module in ohmpi.hardware_components defining the TX component.
                                'mb_2024_0_2', mb_2023_0_X'
            * 'voltage_max' (float): Maximum voltage supported by the TX board [V]
            * 'current_max' (float): Maximum current read by the current ADC on the TX board [A]
            * 'r_shunt' (float): Value of sunt resistor in Ohm.
            * 'interface_name' (string): Name of the interface. 'none', 'modbus'
    'rx': dict
          Describing the RX module with the following keys:
            * 'model' (string): Name of python module in ohmpi.hardware_components defining the RX component. 
                                'pwr_batt', 'pwr_dps5005"
            * 'latency' (float): Latency in seconds in continuous mode (related to ADS)
            * 'sampling_rate' (int): Number of samples per second
            * 'interface_name' (string): Name of the interface. 'none', 'modbus'
    'mux': dict
          Describing the MUX boards with the following keys:
            * 'boards' (dict): Dictionary of dictionaries describing the MUX boards composing the MUX component. Each key is a MUX_ID of a single mux board, e.g. 'MUX_01', containing the following dictionary:
                                * 'model' (string): name of python module in ohmpi.hardware_components defining the type of the MUX board.
                                                  'mux_2023_0_X', 'mux_2024_0_X'
                                * 'electrodes' (list, np.array): List of electrodes addressed by the MUX board, e.g. range(1, 65) 
                                * 'roles' (list, string or dict): Defining the roles addressed by the MUX board
                                * 'mux_tca_address' (string): I2C address of the MUX entry. Used by 'mux_2023_0_X' only.
                                * 'addr1' (string): Jumper of MCP1 ('up', 'down'). used by 'mux_2024_0_X' only. 
                                * 'addr2' (string): Jumper of MCP2 ('up', 'down'). used by 'mux_2024_0_X' only. 
                                * 'interface_name' (string): name of interface. 
                                                           Currently only 'i2c' or 'i2c_ext'
            * 'default' (dict): Default values of all MUX boards. Helps not to define same options for each single MUX boards.
    
'''


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
    'log_file_logging_level': logging.DEBUG,
    'logging_to_console': True,
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
