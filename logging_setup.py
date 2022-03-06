from settings import LOGGING_CONFIG, DATA_LOGGING_CONFIG, MQTT_LOGGING_CONFIG
from os import path, mkdir, statvfs
from time import gmtime
import logging
from mqtt_logger import MQTTHandler
from compressed_sized_timed_rotating_logger import CompressedSizedTimedRotatingFileHandler


def setup_loggers(mqtt=True):
    # Message logging setup
    log_path = path.join(path.dirname(__file__), 'logs')
    if not path.isdir(log_path):
        mkdir(log_path)
    msg_log_filename = path.join(log_path, 'msg_log')
    msg_logger = logging.getLogger('msg_logger')

    # SOH logging setup
    # TODO: Add state of health logging here

    # Data logging setup
    base_path = path.dirname(__file__)
    data_path = path.join(base_path, 'data')
    if not path.isdir(data_path):
        mkdir(data_path)
    data_log_filename = path.join(data_path, 'data_log')
    data_logger = logging.getLogger('data_logger')

    # Debug and logging
    debug = LOGGING_CONFIG['debug_mode']
    if debug:
        logging_level = logging.DEBUG
    else:
        logging_level = logging.INFO

    # Set message logging format and level
    log_format = '%(asctime)-15s | %(process)d | %(levelname)s: %(message)s'
    logging_to_console = LOGGING_CONFIG['logging_to_console']
    msg_handler = CompressedSizedTimedRotatingFileHandler(msg_log_filename, max_bytes=LOGGING_CONFIG['max_bytes'],
                                                          backup_count=LOGGING_CONFIG['backup_count'],
                                                          when=LOGGING_CONFIG['when'],
                                                          interval=LOGGING_CONFIG['interval'])
    msg_formatter = logging.Formatter(log_format)
    msg_formatter.converter = gmtime
    msg_formatter.datefmt = '%Y/%m/%d %H:%M:%S UTC'
    msg_handler.setFormatter(msg_formatter)
    msg_logger.addHandler(msg_handler)
    msg_logger.setLevel(logging_level)

    if logging_to_console:
        msg_logger.addHandler(logging.StreamHandler())
    if mqtt:
        mqtt_msg_handler = MQTTHandler(MQTT_LOGGING_CONFIG['hostname'], MQTT_LOGGING_CONFIG['topic'])
        mqtt_msg_handler.setLevel(logging_level)
        mqtt_msg_handler.setFormatter(msg_formatter)
        msg_logger.addHandler(mqtt_msg_handler)

    # Set data logging level and handler
    data_logger.setLevel(logging.INFO)
    data_handler = CompressedSizedTimedRotatingFileHandler(data_log_filename,
                                                           max_bytes=DATA_LOGGING_CONFIG['max_bytes'],
                                                           backup_count=DATA_LOGGING_CONFIG['backup_count'],
                                                           when=DATA_LOGGING_CONFIG['when'],
                                                           interval=DATA_LOGGING_CONFIG['interval'])
    data_logger.addHandler(data_handler)

    if not init_logging(msg_logger, logging_level, log_path, data_log_filename):
        print('ERROR: Could not initialize logging!')
    return msg_logger, msg_log_filename, data_logger, data_log_filename, logging_level


def init_logging(msg_logger, logging_level, log_path, data_log_filename):
    """ This is the init sequence for the logging system """

    init_logging_status = True
    msg_logger.info('')
    msg_logger.info('****************************')
    msg_logger.info('*** NEW SESSION STARTING ***')
    msg_logger.info('****************************')
    msg_logger.info('')
    msg_logger.info('Logging level: %s' % logging_level)
    try:
        st = statvfs('.')
        available_space = st.f_bavail * st.f_frsize / 1024 / 1024
        msg_logger.info(f'Remaining disk space : {available_space:.1f} MB')
    except Exception as e:
        msg_logger.debug('Unable to get remaining disk space: {e}')
    msg_logger.info('Saving data log to ' + data_log_filename)
    msg_logger.info('OhmPi settings:')
    # TODO Add OhmPi settings
    msg_logger.info('')
    msg_logger.info(f'init_logging_status: {init_logging_status}')
    return init_logging_status
