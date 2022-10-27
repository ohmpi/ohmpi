import logging

from paho.mqtt.client import MQTTv31

mqtt_broker = 'localhost'
# OhmPi configuration
OHMPI_CONFIG = {
    'id': '0001',  # Unique identifier of the OhmPi board (string)
    'R_shunt': 2,  # Shunt resistance in Ohms
    'Imax': 4800/50/2,  # Maximum current
    'coef_p2': 2.50,  # slope for current conversion for ADS.P2, measurement in V/V
    'coef_p3': 2.50,  # slope for current conversion for ADS.P3, measurement in V/V
    'offset_p2': 0,
    'offset_p3': 0,
    'integer': 2,  # Max value 10 # TODO: Explain what this is...
    'version': 2,
    'max_elec': 64,
    'board_address': {'A': 0x70, 'B': 0x71, 'M': 0x72, 'N': 0x73},  # def. {'A': 0x76, 'B': 0x71, 'M': 0x74, 'N': 0x70}
    'settings': 'ohmpi_settings.json'
}  # TODO: add a dictionary with INA models and associated gain values

CONTROL_CONFIG = {
    'tcp_port': 5555,
    'interface': 'http_interface.py' # 'mqtt_interface'
}
# Execution logging configuration
EXEC_LOGGING_CONFIG = {
    'logging_level': logging.DEBUG,
    'logging_to_console': True,
    'file_name': 'exec.log',
    'max_bytes': 262144,
    'backup_count': 30,
    'when': 'd',
    'interval': 1
}

# Data logging configuration
DATA_LOGGING_CONFIG = {
    'logging_level': logging.INFO,
    'logging_to_console': True,
    'file_name': 'data.log',
    'max_bytes': 16777216,
    'backup_count': 1024,
    'when': 'd',
    'interval': 1
}

# State of Health logging configuration
SOH_LOGGING_CONFIG = {
    'file_name': 'soh.log',
    'logging_to_console': True,
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
    'auth': { 'username': 'mqtt_user', 'password': 'mqtt_password' },
    'tls': None,
    'protocol': MQTTv31,
    'transport': 'tcp',
    'client_id': f'{OHMPI_CONFIG["id"]}',
    'exec_topic': f'ohmpi_{OHMPI_CONFIG["id"]}/exec',
    'data_topic': f'ohmpi_{OHMPI_CONFIG["id"]}/data',
    'soh_topic': f'ohmpi_{OHMPI_CONFIG["id"]}/soh'
}

# MQTT control configuration parameters
MQTT_CONTROL_CONFIG = {
    'hostname': mqtt_broker,
    'port': 1883,
    'qos': 2,
    'retain': False,
    'keepalive': 60,
    'will': None,
    'auth': { 'username': 'mqtt_user', 'password': 'mqtt_password' },
    'tls': None,
    'protocol': MQTTv31,
    'transport': 'tcp',
    'client_id': f'{OHMPI_CONFIG["id"]}',
    'ctrl_topic': f'ohmpi_{OHMPI_CONFIG["id"]}/ctrl'
}
