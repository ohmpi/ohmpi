from paho.mqtt.client import MQTTv31

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
    'board_address': {'A': 0x70, 'B': 0x71, 'M': 0x72, 'N': 0x73}  # def. {'A': 0x76, 'B': 0x71, 'M': 0x74, 'N': 0x70}
    #'board_address': {'A': 0x76, 'B': 0x71, 'M': 0x74, 'N': 0x70}  # def. {'A': 0x76, 'B': 0x71, 'M': 0x74, 'N': 0x70}
}

# Execution logging configuration
EXEC_LOGGING_CONFIG = {
    'debug_mode': True,
    'logging_to_console': False,
    'file_name': 'ohmpi_log',
    'max_bytes': 262144,
    'backup_count': 30,
    'when': 'd',
    'interval': 1
}

# Data logging configuration
DATA_LOGGING_CONFIG = {
    'file_name': 'data_log',
    'logging_to_console': False,
    'max_bytes': 16777216,
    'backup_count': 1024,
    'when': 'd',
    'interval': 1
}

# State of Health logging configuration
SOH_LOGGING_CONFIG = {
    'file_name': 'soh_log',
    'logging_to_console': True,
    'max_bytes': 16777216,
    'backup_count': 1024,
    'when': 'd',
    'interval': 1
}

# MQTT logging configuration parameters
MQTT_LOGGING_CONFIG = {
    'hostname': 'raspberrypi.local',
    'port': 1883,
    'qos': 0,
    'retain': False,
    'keepalive': 60,
    'will': None,
    'auth': None,
    'tls': None,
    'protocol': MQTTv31,
    'transport': 'tcp',
    'client_id': f'ohmpi_sn_{OHMPI_CONFIG["id"]}',
    'control_topic': f'ctrl_ohmpi_sn_{OHMPI_CONFIG["id"]}',
    'exec_topic': f'exec_ohmpi_sn_{OHMPI_CONFIG["id"]}',
    'data_topic': f'data_ohmpi_sn_{OHMPI_CONFIG["id"]}',
    'soh_topic': f'soh_ohmpi_sn_{OHMPI_CONFIG["id"]}'
}
