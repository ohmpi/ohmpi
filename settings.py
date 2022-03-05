# OhmPi configuration
OHMPI_CONFIG = {
    'id': '0001',  # Unique identifier of the OhmPi board (string)
    'R_shunt': 2,  # Shunt resistance in Ohms
    'Imax': 4800/50/2,  # Maximum current
    'coef_p2': 2.50,  # slope for current conversion for ADS.P2, measurement in V/V
    'coef_p3': 2.50,  # slope for current conversion for ADS.P3, measurement in V/V
    'offset_p2': 0,
    'offset_p3': 0,
    'integer': 2,  # Max value 10 WHAT IS THIS?
    'version': 2,
    'max_elec': 64,
    'board_address': {'A': 0x76, 'B': 0x71, 'M': 0x74, 'N': 0x70}  # def. {'A': 0x76, 'B': 0x71, 'M': 0x74, 'N': 0x70}
}

# local messages logging configuration
LOGGING_CONFIG = {
    'debug_mode': False,
    'logging_to_console': False,
    'file_name': 'ohmpi_log',
    'max_bytes': 262144,
    'backup_count': 30,
    'when': 'd',
    'interval': 1
}

# local data logging configuration
DATA_LOGGING_CONFIG = {
    'file_name': 'data_log',
    'max_bytes': 16777216,
    'backup_count': 1024,
    'when': 'd',
    'interval': 1
}

# MQTT configuration parameters
MQTT_CONFIG = {
    'mqtt_broker': 'mg3d-dev.umons.ac.be',
    'client_id': f'ohmpi_sn_{OHMPI_CONFIG["id"]}',
    'control_topic': f'cmd_ohmpi_sn_{OHMPI_CONFIG["id"]}',
    'measurements_topic': f'measurements_ohmpi_sn_{OHMPI_CONFIG["id"]}'
}
