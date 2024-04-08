import json
from ohmpi.config import (EXEC_LOGGING_CONFIG, DATA_LOGGING_CONFIG, SOH_LOGGING_CONFIG, MQTT_LOGGING_CONFIG,
                          MQTT_CONTROL_CONFIG)
from os import path, mkdir, statvfs
from time import gmtime
import logging
from ohmpi.mqtt_handler import MQTTHandler
from ohmpi.compressed_sized_timed_rotating_handler import CompressedSizedTimedRotatingFileHandler
import sys
from termcolor import colored


def get_logging_levels():
    """Gets a list of the logging levels loaded"""
    return [logging.getLevelName(x) for x in range(1, 101) if not logging.getLevelName(x).startswith('Level')]


def add_logging_level(level_name, level_num, method_name=None):
    """
    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.

    `levelName` becomes an attribute of the `logging` module with the value
    `levelNum`. `methodName` becomes a convenience method for both `logging`
    itself and the class returned by `logging.getLoggerClass()` (usually just
    `logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
    used.

    To avoid accidental clobberings of existing attributes, this method will
    raise an `AttributeError` if the level name is already an attribute of the
    `logging` module or if the method name is already present

    comes from https://stackoverflow.com/questions/2183233

    Example
    -------
    >>> add_logging_level('TRACE', logging.DEBUG - 5)
    >>> logging.getLogger(__name__).setLevel("TRACE")
    >>> logging.getLogger(__name__).trace('that worked')  # noqa
    >>> logging.trace('so did this')  # noqa
    >>> logging.TRACE  # noqa

    """
    if not method_name:
        method_name = level_name.lower()

    if hasattr(logging, level_name):
        raise AttributeError('{} already defined in logging module'.format(level_name))
    if hasattr(logging, method_name):
        raise AttributeError('{} already defined in logging module'.format(method_name))
    if hasattr(logging.getLoggerClass(), method_name):
        raise AttributeError('{} already defined in logger class'.format(method_name))

    # This method was inspired by the answers to Stack Overflow post
    # http://stackoverflow.com/q/2183233/2988730, especially
    # http://stackoverflow.com/a/13638084/2988730
    def log_for_level(self, message, *args, **kwargs):
        if self.isEnabledFor(level_num):
            self._log(level_num, message, args, **kwargs)

    def log_to_root(message, *args, **kwargs):
        logging.log(level_num, message, *args, **kwargs)

    logging.addLevelName(level_num, level_name)
    setattr(logging, level_name, level_num)
    setattr(logging.getLoggerClass(), method_name, log_for_level)
    setattr(logging, method_name, log_to_root)


def create_stdout_logger(name):
    logger = logging.getLogger(f'{name}_logger')
    log_format = f'%(asctime)-15s | {name[:8]:8s} | %(levelname)s: %(message)s'
    formatter = logging.Formatter(log_format)
    formatter.converter = gmtime
    formatter.datefmt = '%Y-%m-%d %H:%M:%S UTC'
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    if 'EVENT' not in get_logging_levels():
        add_logging_level('EVENT', logging.DEBUG + 1)
    if 'TEST' not in get_logging_levels():
        add_logging_level('TEST', logging.DEBUG + 1)
    return logger


def setup_loggers(mqtt=True):
    add_logging_level('EVENT', logging.DEBUG + 1)  # TODO : check if we should set the level to DEBUG...
    add_logging_level('TEST', logging.INFO + 1)  # TODO : check if we should set the level to DEBUG...

    msg = ''
    # Message logging setup
    log_path = path.join(path.dirname(__file__), 'logs')
    if not path.isdir(log_path):
        mkdir(log_path)
    exec_log_filename = path.join(log_path, EXEC_LOGGING_CONFIG['file_name'])
    soh_log_filename = path.join(log_path, SOH_LOGGING_CONFIG['file_name'])

    exec_logger = logging.getLogger('exec_logger')
    soh_logger = logging.getLogger('soh_logger')

    # SOH logging setup
    # Set message logging format and level
    log_format = '%(asctime)-15s | %(process)d | %(levelname)s: %(message)s'
    logging_to_console = SOH_LOGGING_CONFIG['logging_to_console']
    soh_handler = CompressedSizedTimedRotatingFileHandler(soh_log_filename,
                                                           max_bytes=SOH_LOGGING_CONFIG['max_bytes'],
                                                           backup_count=SOH_LOGGING_CONFIG['backup_count'],
                                                           when=SOH_LOGGING_CONFIG['when'],
                                                           interval=SOH_LOGGING_CONFIG['interval'])
    soh_formatter = logging.Formatter(log_format)
    soh_formatter.converter = gmtime
    soh_formatter.datefmt = '%Y-%m-%d %H:%M:%S UTC'
    soh_handler.setFormatter(soh_formatter)
    soh_logger.addHandler(soh_handler)
    soh_logger.setLevel(SOH_LOGGING_CONFIG['log_file_logging_level'])

    if logging_to_console:
        console_soh_handler = logging.StreamHandler(sys.stdout)
        console_soh_handler.setLevel(SOH_LOGGING_CONFIG['logging_level'])
        console_soh_handler.setFormatter(soh_formatter)
        soh_logger.addHandler(console_soh_handler)

    if mqtt:
        mqtt_settings = MQTT_LOGGING_CONFIG.copy()
        mqtt_soh_logging_level = mqtt_settings.pop('soh_logging_level', logging.DEBUG)
        [mqtt_settings.pop(i, None) for i in ['client_id', 'exec_topic', 'data_topic', 'soh_topic',
                                              'data_logging_level', 'exec_logging_level']]
        mqtt_settings.update({'topic': MQTT_LOGGING_CONFIG['soh_topic']})
        # TODO: handle the case of MQTT broker down or temporarily unavailable
        try:
            mqtt_soh_handler = MQTTHandler(**mqtt_settings)
            mqtt_soh_handler.setLevel(mqtt_soh_logging_level)
            mqtt_soh_handler.setFormatter(soh_formatter)
            soh_logger.addHandler(mqtt_soh_handler)
            msg += colored(f"\n\u2611 Publishes state of heath as {MQTT_LOGGING_CONFIG['soh_topic']} topic on the "
                           f"{MQTT_LOGGING_CONFIG['hostname']} broker", 'blue')
        except Exception as e:
            msg += colored(f'\nWarning: Unable to connect to soh topic on broker\n{e}', 'yellow')
            mqtt = False

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
    exec_formatter.datefmt = '%Y-%m-%d %H:%M:%S UTC'
    exec_handler.setFormatter(exec_formatter)
    exec_logger.addHandler(exec_handler)
    exec_logger.setLevel(EXEC_LOGGING_CONFIG['log_file_logging_level'])

    if logging_to_console:
        console_exec_handler = logging.StreamHandler(sys.stdout)
        console_exec_handler.setLevel(EXEC_LOGGING_CONFIG['logging_level'])
        console_exec_handler.setFormatter(exec_formatter)
        exec_logger.addHandler(console_exec_handler)

    if mqtt:
        mqtt_settings = MQTT_LOGGING_CONFIG.copy()
        mqtt_exec_logging_level = mqtt_settings.pop('exec_logging_level', logging.DEBUG)
        [mqtt_settings.pop(i) for i in ['client_id', 'exec_topic', 'data_topic', 'soh_topic', 'data_logging_level',
                                        'soh_logging_level']]
        mqtt_settings.update({'topic': MQTT_LOGGING_CONFIG['exec_topic']})
        # TODO: handle the case of MQTT broker down or temporarily unavailable
        try:
            mqtt_exec_handler = MQTTHandler(**mqtt_settings)
            mqtt_exec_handler.setLevel(mqtt_exec_logging_level)
            mqtt_exec_handler.setFormatter(exec_formatter)
            exec_logger.addHandler(mqtt_exec_handler)
            msg += colored(f"\n\u2611 Publishes execution as {MQTT_LOGGING_CONFIG['exec_topic']} topic on the "
                           f"{MQTT_LOGGING_CONFIG['hostname']} broker", 'blue')
        except Exception as e:
            msg += colored(f'\nWarning: Unable to connect to exec topic on broker\n{e}', 'yellow')
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
    data_formatter.datefmt = '%Y-%m-%d %H:%M:%S UTC'
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
        mqtt_data_logging_level = mqtt_settings.pop('data_logging_level', logging.INFO)
        [mqtt_settings.pop(i, None) for i in ['client_id', 'exec_topic', 'data_topic', 'soh_topic',
                                              'exec_logging_level', 'soh_logging_level']]
        mqtt_settings.update({'topic': MQTT_LOGGING_CONFIG['data_topic']})
        try:
            mqtt_data_handler = MQTTHandler(**mqtt_settings)
            mqtt_data_handler.setLevel(MQTT_LOGGING_CONFIG['data_logging_level'])
            mqtt_data_handler.setFormatter(data_formatter)
            data_logger.addHandler(mqtt_data_handler)
            msg += colored(f"\n\u2611 Publishes data as {MQTT_LOGGING_CONFIG['data_topic']} topic on the "
                           f"{MQTT_LOGGING_CONFIG['hostname']} broker", 'blue')
        except Exception as e:
            msg += colored(f'\nWarning: Unable to connect to data topic on broker\n{e}', 'yellow')
            mqtt = False

    try:
        init_logging(exec_logger, data_logger, soh_logger, EXEC_LOGGING_CONFIG['logging_level'],
                     SOH_LOGGING_CONFIG['logging_level'], log_path, data_log_filename)
    except Exception as err:
        msg += colored(f'\n\u26A0 ERROR: Could not initialize logging!\n{err}', 'red')
    finally:
        return exec_logger, exec_log_filename, data_logger, data_log_filename, soh_logger, soh_log_filename, \
            EXEC_LOGGING_CONFIG['logging_level'], msg


def init_logging(exec_logger, data_logger, soh_logger, exec_logging_level, soh_logging_level, log_path, data_log_filename):  # noqa
    """ This is the init sequence for the logging system """

    init_logging_status = True
    exec_logger.info('')
    exec_logger.info('*****************************************')
    data_logger.info('*** DATALOGGER - NEW SESSION STARTING ***')
    exec_logger.info('*** EXECLOGGER - NEW SESSION STARTING ***')
    soh_logger.info('*** SOHLOGGER  - NEW SESSION STARTING ***')
    exec_logger.info('*****************************************')
    exec_logger.info('')

    exec_logger.debug(f'Execution logging level: {exec_logging_level}')
    exec_logger.debug(f'State of health logging level: {soh_logging_level}')
    try:
        st = statvfs('.')
        available_space = st.f_bavail * st.f_frsize / 1024 / 1024
        exec_logger.info(f'Remaining disk space : {available_space:.1f} MB')
    except Exception as e:  # noqa
        exec_logger.debug('Unable to get remaining disk space: {e}')
    exec_logger.info('Saving data log to ' + data_log_filename)
    config_dict = {'execution logging configuration': json.dumps(EXEC_LOGGING_CONFIG, indent=4),
                   'state of health logging configuration': json.dumps(SOH_LOGGING_CONFIG, indent=4),
                   'data logging configuration': json.dumps(DATA_LOGGING_CONFIG, indent=4),
                   'mqtt logging configuration': json.dumps(MQTT_LOGGING_CONFIG, indent=4),
                   'mqtt control configuration': json.dumps(MQTT_CONTROL_CONFIG, indent=4)}
    for k, v in config_dict.items():
        exec_logger.debug(f'{k}:\n{v}')
    exec_logger.debug('')
    if not init_logging_status:
        exec_logger.warning(f'Logging initialisation has encountered a problem.')
    data_logger.info('Starting_session')
    return init_logging_status
