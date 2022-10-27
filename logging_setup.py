import json
from config import EXEC_LOGGING_CONFIG, DATA_LOGGING_CONFIG, MQTT_LOGGING_CONFIG, MQTT_CONTROL_CONFIG
from os import path, mkdir, statvfs
from time import gmtime
import logging
from mqtt_logger import MQTTHandler
from compressed_sized_timed_rotating_logger import CompressedSizedTimedRotatingFileHandler
import sys


def setup_loggers(mqtt=True):
    # Message logging setup
    log_path = path.join(path.dirname(__file__), 'logs')
    if not path.isdir(log_path):
        mkdir(log_path)
    exec_log_filename = path.join(log_path, EXEC_LOGGING_CONFIG['file_name'])
    exec_logger = logging.getLogger('exec_logger')

    # SOH logging setup
    # TODO: Add state of health logging here

    # Data logging setup
    base_path = path.dirname(__file__)
    data_path = path.join(base_path, 'data')
    if not path.isdir(data_path):
        mkdir(data_path)
    data_log_filename = path.join(data_path, DATA_LOGGING_CONFIG['file_name'])
    data_logger = logging.getLogger('data_logger')

    # Set message logging format and level
    log_format = '%(asctime)-15s | %(process)d | %(levelname)s: %(message)s'
    logging_to_console = EXEC_LOGGING_CONFIG['logging_to_console']
    exec_handler = CompressedSizedTimedRotatingFileHandler(exec_log_filename,
                                                           max_bytes=EXEC_LOGGING_CONFIG['max_bytes'],
                                                           backup_count=EXEC_LOGGING_CONFIG['backup_count'],
                                                           when=EXEC_LOGGING_CONFIG['when'],
                                                           interval=EXEC_LOGGING_CONFIG['interval'])
    exec_formatter = logging.Formatter(log_format)
    exec_formatter.converter = gmtime
    exec_formatter.datefmt = '%Y/%m/%d %H:%M:%S UTC'
    exec_handler.setFormatter(exec_formatter)
    exec_logger.addHandler(exec_handler)
    exec_logger.setLevel(EXEC_LOGGING_CONFIG['logging_level'])

    if logging_to_console:
        print(f'logging exec ? {logging_to_console}') # TODO: delete this line
        console_exec_handler = logging.StreamHandler(sys.stdout)
        console_exec_handler.setLevel(EXEC_LOGGING_CONFIG['logging_level'])
        console_exec_handler.setFormatter(exec_formatter)
        exec_logger.addHandler(console_exec_handler)

    if mqtt:
        mqtt_settings = MQTT_LOGGING_CONFIG.copy()
        [mqtt_settings.pop(i) for i in ['client_id', 'exec_topic', 'data_topic', 'soh_topic']]
        mqtt_settings.update({'topic':MQTT_LOGGING_CONFIG['exec_topic']})
        # TODO: handle the case of MQTT broker down or temporarily unavailable
        try:
            mqtt_exec_handler = MQTTHandler(**mqtt_settings)
            mqtt_exec_handler.setLevel(EXEC_LOGGING_CONFIG['logging_level'])
            mqtt_exec_handler.setFormatter(exec_formatter)
            exec_logger.addHandler(mqtt_exec_handler)
        except:
            mqtt = False

    # Set data logging format and level
    log_format = '%(asctime)-15s | %(process)d | %(levelname)s: %(message)s'
    logging_to_console = DATA_LOGGING_CONFIG['logging_to_console']

    data_handler = CompressedSizedTimedRotatingFileHandler(data_log_filename,
                                                           max_bytes=DATA_LOGGING_CONFIG['max_bytes'],
                                                           backup_count=DATA_LOGGING_CONFIG['backup_count'],
                                                           when=DATA_LOGGING_CONFIG['when'],
                                                           interval=DATA_LOGGING_CONFIG['interval'])
    data_formatter = logging.Formatter(log_format)
    data_formatter.converter = gmtime
    data_formatter.datefmt = '%Y/%m/%d %H:%M:%S UTC'
    data_handler.setFormatter(exec_formatter)
    data_logger.addHandler(data_handler)
    data_logger.setLevel(DATA_LOGGING_CONFIG['logging_level'])

    if logging_to_console:
        console_data_handler = logging.StreamHandler(sys.stdout)
        console_data_handler.setLevel(DATA_LOGGING_CONFIG['logging_level'])
        console_data_handler.setFormatter(exec_formatter)
        data_logger.addHandler(console_data_handler)

    if mqtt:
        mqtt_settings = MQTT_LOGGING_CONFIG.copy()
        [mqtt_settings.pop(i) for i in ['client_id', 'exec_topic', 'data_topic', 'soh_topic']]
        mqtt_settings.update({'topic': MQTT_LOGGING_CONFIG['data_topic']})
        mqtt_data_handler = MQTTHandler(**mqtt_settings)
        mqtt_data_handler.setLevel(DATA_LOGGING_CONFIG['logging_level'])
        mqtt_data_handler.setFormatter(data_formatter)
        data_logger.addHandler(mqtt_data_handler)

    try:
        init_logging(exec_logger, data_logger, EXEC_LOGGING_CONFIG['logging_level'], log_path, data_log_filename)
    except Exception as err:
        print(f'ERROR: Could not initialize logging!\n{err}')
    finally:
        return exec_logger, exec_log_filename, data_logger, data_log_filename, EXEC_LOGGING_CONFIG['logging_level']


def init_logging(exec_logger, data_logger, exec_logging_level, log_path, data_log_filename):
    """ This is the init sequence for the logging system """

    init_logging_status = True
    exec_logger.info('')
    exec_logger.info('****************************')
    exec_logger.info('*** NEW SESSION STARTING ***')
    exec_logger.info('****************************')
    exec_logger.info('')
    exec_logger.info('Logging level: %s' % exec_logging_level)
    try:
        st = statvfs('.')
        available_space = st.f_bavail * st.f_frsize / 1024 / 1024
        exec_logger.info(f'Remaining disk space : {available_space:.1f} MB')
    except Exception as e:
        exec_logger.debug('Unable to get remaining disk space: {e}')
    exec_logger.info('Saving data log to ' + data_log_filename)
    exec_logger.info('OhmPi settings:')
    # TODO Add OhmPi settings
    config_dict = {'execution logging configuration': json.dumps(EXEC_LOGGING_CONFIG, indent=4),
                   'data logging configuration': json.dumps(DATA_LOGGING_CONFIG, indent=4),
                   'mqtt logging configuration': json.dumps(MQTT_LOGGING_CONFIG, indent=4),
                   'mqtt control configuration': json.dumps(MQTT_CONTROL_CONFIG, indent=4)}
    for k, v in config_dict.items():
        exec_logger.info(f'{k}:\n{v}')
    exec_logger.info('')
    exec_logger.info(f'init_logging_status: {init_logging_status}')
    data_logger.info('Starting_session')
    return init_logging_status
