import io
import os
import shutil
import collections.abc
import numpy as np
from numbers import Number


def enforce_specs(kwargs, specs, key):

    kwargs.update({key: kwargs.pop(key, specs[key]['default'])})
    
    if isinstance(kwargs[key], Number):
        s = specs.copy()
        min_value = s[key].pop('min', -np.inf)
        s[key]['min'] = min_value
        max_value = s[key].pop('max', np.inf)
        s[key]['max'] = max_value
        if kwargs[key] < min_value:
            kwargs[key] = min_value
        elif kwargs[key] > max_value:
            kwargs[key] = max_value

    return kwargs


def update_dict(d, u):
    """Updates a dictionary by adding elements to collection items associated to existing keys

    Parameters
    ----------
    d: dict
        Dictionary that will be updated
    u: dict
        Dictionary that is used to update d

    Returns
    -------
    dict
        The updated dictionary
    """

    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = update_dict(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def get_platform():
    """Gets platform name and checks if it is a raspberry pi

    Returns
    -------
    str, bool
        name of the platform on which the code is running, boolean that is true if the platform is a raspberry pi"""

    platform = 'unknown'
    on_pi = False
    try:
        with io.open('/sys/firmware/devicetree/base/model', 'r') as f:
            platform = f.read().lower()
        if 'raspberry pi' in platform:
            on_pi = True
    except FileNotFoundError:
        pass
    return platform, on_pi


def change_config(config_file, verbose=True):
    pwd = os.path.dirname(os.path.abspath(__file__))
    try:
        shutil.copyfile(f'{pwd}/config.py', f'{pwd}/config_tmp.py')
        shutil.copyfile(f'{pwd}/{config_file}', f'{pwd}/config.py')
        if verbose:
            print(f'Changed to {pwd}/{config_file}:\n')
            with open(f'{pwd}/config.py', mode='r') as f:
                print(f.read())

    except Exception as error:
        print(f'Could not change config file to {pwd}/{config_file}:\n{error}')


def parse_log(log):
    msg_started = False
    msg_tmp = ''
    s = 0
    with open(log, "r") as file:
        time, process_id, msg, tag, session = [], [], [], [], []
        for i, line in enumerate(file):
            if len(line.split(" | ")) > 1:
                time.append(line.split(" | ")[0])
                process_id.append(line.split(" | ")[1])
                msg.append(":".join(line.split(" | ")[2].split(":")[1:]))
                tag.append(line.split(" | ")[2].split(":")[0])
                if tag[-1] == 'INFO':
                    if 'NEW SESSION' in msg[-1]:
                        s += 1
                session.append(s)
            elif "{" in line or msg_started:
                msg_tmp = msg_tmp + line
                # print(msg_tmp)
                msg_started = True
                if "}" in line:
                    msg[-1] = msg[-1] + msg_tmp
                    msg_tmp = ''
                    msg_started = False

    time = np.array(time)
    process_id = np.array(process_id)
    tag = np.array(tag)
    msg = np.array(msg)
    session = np.array(session)
    return time, process_id, tag, msg, session

def filter_log(filename, level=None, directory="logs", last=1):
    time, process_id, tag, msg, session = parse_log(os.path.join(directory, filename))
    time, process_id, tag, msg, session = time[tag == level], process_id[tag == level], \
            tag[tag == level], msg[tag == level], session[tag == level]

    time_filt, process_id_filt, tag_filt, msg_filt = time[session >= max(session)-last], process_id[session >= max(session)-last], \
            tag[session >= max(session)-last], msg[session >= max(session)-last]

    return time_filt, process_id_filt, tag_filt, msg_filt


def mux_2024_to_mux_2023_takeouts(elec_list):
    """ Updates cabling for mux v2024 so that takeouts are similar to takeouts from mux v2023.
    This is only useful when replacing mux v2023 installations or re-using old test circuits.

    Parameters
    ----------
    elec_list: list of electrodes or sequence

    """

    mapper = {1: 16, 2: 1, 3: 15, 4: 2, 5: 14, 6: 3, 7: 13, 8: 4, 9: 12, 10: 5, 11: 11,
              12: 6, 13: 10, 14: 7, 15: 9, 16: 8}

    return np.vectorize(mapper.get)(elec_list)


def mux_2023_to_mux_2024_takeouts(elec_list):
    """ Updates cabling for mux v2023 so that takeouts are similar to takeouts from mux v2024.
    This is only useful when replacing mux v2023 installations or re-using old test circuits.

    Parameters
    ----------
    elec_list: list of electrodes or sequence

    """

    mapper = {1: 2, 2: 4, 3: 6, 4: 8, 5: 10, 6: 12, 7: 14, 8: 16,
              9: 15, 10: 13, 11: 11, 12: 9, 13: 7, 14: 5, 15: 3, 16: 1, }

    return np.vectorize(mapper.get)(elec_list)


def generate_preset_configs(configs_to_generate=None):
    """ Generates preset configuration files

   Parameters
   ----------
   configs_to_generate: list, None default: None
        list of configuration names following the standard pattern
   """

    if configs_to_generate is None:
        configs_to_generate = ['config_mb_2023.py', 'config_mb_2023__4_mux_2023.py',
                               'config_mb_2023__1_mux_2024_4roles.py', 'config_mb_2023__2_mux_2024_4roles.py',
                               'config_mb_2023__3_mux_2024_4roles.py', 'config_mb_2023__4_mux_2024_4roles.py',
                               'config_mb_2023__2_mux_2024_2roles.py', 'config_mb_2023__4_mux_2024_2roles.py',
                               'config_mb_2024_0_2.py', 'config_mb_2024_0_2_dps5005.py',
                               'config_mb_2024_0_2__4_mux_2023.py', 'config_mb_2024_0_2__4_mux_2023_dps5005.py',
                               'config_mb_2024_0_2__1_mux_2024_4roles.py',
                               'config_mb_2024_0_2__1_mux_2024_4roles_dps5005.py',
                               'config_mb_2024_0_2__2_mux_2024_4roles.py',
                               'config_mb_2024_0_2__2_mux_2024_4roles_dps5005.py',
                               'config_mb_2024_0_2__2_mux_2024_2roles.py',
                               'config_mb_2024_0_2__2_mux_2024_2roles_dps5005.py',
                               'config_mb_2024_0_2__3_mux_2024_4roles.py',
                               'config_mb_2024_0_2__3_mux_2024_4roles_dps5005.py',
                               'config_mb_2024_0_2__4_mux_2024_4roles.py',
                               'config_mb_2024_0_2__4_mux_2024_4roles_dps5005.py',
                               'config_mb_2024_0_2__4_mux_2024_2roles.py',
                               'config_mb_2024_0_2__4_mux_2024_2roles_dps5005.py'
                               ]

    header = """import logging
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

# default properties of system components that will be
# overwritten by properties defined in each the board dict below.
# if bounds are defined in board specs, values out of specs will be bounded to remain in specs
# omitted properties in config will be set to board specs default values if they exist

HARDWARE_CONFIG = {
    'ctl': {'model': 'raspberry_pi'},
    'pwr': """

    r_shunt = 2.
    options = {'pwr': {'battery': """{'model': 'pwr_batt', 'voltage': 12., 'interface_name': 'none'},""",
                       'dps5005': """{'model': 'pwr_dps5005', 'voltage': 3., 'interface_name': 'modbus'},"""
                       },
               'mb': {'mb_2024_0_2': {'tx': """{'model': 'mb_2024_0_2',
                 'voltage_max': 50.,  # Maximum voltage supported by the TX board [V]
                 'current_max': 4.80/(50*r_shunt),  # Maximum voltage read by the current ADC on the TX board [A]
                 'r_shunt': r_shunt,  # Shunt resistance in Ohms
                 'interface_name': 'i2c',
                 'vmn_hardware_offset': 2500.
                }""",
                                      'rx': """{'model': 'mb_2024_0_2',
                 'latency': 0.010,  # latency in seconds in continuous mode
                 'sampling_rate': 200,  # number of samples per second
                 'interface_name': 'i2c',
                }"""},
                      'mb_2023': {'tx': """{'model': 'mb_2023_0_X',
                 'voltage_max': 50.,  # Maximum voltage supported by the TX board [V]
                 'current_max': 4.80/(50*r_shunt),  # Maximum voltage read by the current ADC on the TX board [A]
                 'r_shunt': r_shunt,  # Shunt resistance in Ohms
                 'interface_name': 'i2c'
                }""",
                                  'rx': """{'model': 'mb_2023_0_X',
                'coef_p2': 2.50,  # slope for conversion for ADS, measurement in V/V
                'sampling_rate': 200.,  # number of samples per second
                'interface_name': 'i2c',
                }"""}
                      },
               'mux': {'mux_2023':
                           ["""                 {'mux_A':
                         {'model': 'mux_2023_0_X',
                          'mux_tca_address': 0x70,
                          'roles': 'A',
                          'electrodes': range(1, 65),
                          },""",
                            """\n                 'mux_B':
                         {'model': 'mux_2023_0_X',
                          'mux_tca_address': 0x71,
                          'roles': 'B',
                          'electrodes': range(1, 65),
                          },""",
                            """\n                 'mux_M':
                         {'model': 'mux_2023_0_X',
                          'mux_tca_address': 0x72,
                          'roles': 'M',
                          'electrodes': range(1, 65),
                          },""",
                            """\n                 'mux_N':
                         {'model': 'mux_2023_0_X',
                          'mux_tca_address': 0x73,
                          'roles': 'N',
                          'electrodes': range(1, 65),
                          }"""],
                       'mux_2024_2roles':
                           ["""                 {'mux_01':
                         {'model': 'mux_2024_0_X',
                          'roles': ['A', 'B'],
                          'electrodes': range(1, 17),
                          'addr1': 'up',
                          'addr2': 'up',
                          'tca_address': None,
                          'tca_channel': 0,
                          },""",
                            """\n                 'mux_02':
                         {'model': 'mux_2024_0_X',
                          'roles': ['M', 'N'],
                          'electrodes': range(1, 17),
                          'addr1': 'down',
                          'addr2': 'up',
                          'tca_address': None,
                          'tca_channel': 0,
                          },""",
                            """\n                'mux_03':
                         {'model': 'mux_2024_0_X',
                          'roles': ['A', 'B'],
                          'electrodes': range(17, 33),
                          'addr1': 'up',
                          'addr2': 'down',
                          'tca_address': None,
                          'tca_channel': 0,},""",
                            """\n                'mux_04':
                         {'model': 'mux_2024_0_X',
                          'roles': ['M', 'N'],
                          'electrodes': range(17, 33),
                          'addr1': 'down',
                          'addr2': 'down',
                          'tca_address': None,
                          'tca_channel': 0,
                          }"""],
                       'mux_2024_4roles': [
                           """                {'mux_01':
                         {'model': 'mux_2024_0_X',
                          'electrodes': range(1, 9),
                          'roles': ['A', 'B', 'M', 'N'],
                          'addr1': 'up',
                          'addr2': 'up',
                          'tca_address': None,
                          'tca_channel': 0,},""",
                           """\n                 'mux_02':
                         {'model': 'mux_2024_0_X',
                          'electrodes': range(9, 17),
                          'roles': ['A', 'B', 'M', 'N'],
                          'addr1': 'down',
                          'addr2': 'up',
                          'tca_address': None,
                          'tca_channel': 0,},""",
                           """\n                 'mux_03':
                         {'model': 'mux_2024_0_X',
                          'electrodes': range(17, 25),
                          'roles': ['A', 'B', 'M', 'N'],
                          'addr1': 'up',
                          'addr2': 'down',
                          'tca_address': None,
                          'tca_channel': 0,},""",
                           """\n                'mux_04':
                         {'model': 'mux_2024_0_X',
                          'electrodes': range(25, 33),
                          'roles': ['A', 'B', 'M', 'N'],
                          'addr1': 'down',
                          'addr2': 'down',
                          'tca_address': None,
                          'tca_channel': 0,},"""]
                       }
               }
    mux_footer = {'mb_2023': """\n                 },
            'default': {'interface_name': 'i2c',
                             'voltage_max': 50.,
                             'current_max': 3.}
                }\n}\n""",
                  'mb_2024_0_2': """\n                 },
            'default': {'interface_name': 'i2c_ext',
                             'voltage_max': 50.,
                             'current_max': 3.}
                }\n}\n"""}

    footer = """# SET THE LOGGING LEVELS, MQTT BROKERS AND MQTT OPTIONS ACCORDING TO YOUR NEEDS
# Execution logging configuration
EXEC_LOGGING_CONFIG = {
    'logging_level': logging.INFO,
    'log_file_logging_level': logging.INFO,
    'logging_to_console': True,
    'file_name': f'exec{logging_suffix}.log',
    'max_bytes': 2097152,
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
    'log_file_logging_level': logging.INFO,
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
    'exec_logging_level': EXEC_LOGGING_CONFIG['logging_level'],
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
"""

    for mb, v_mb in options['mb'].items():
        for n in range(0, 5):
            for mux, v_mux in options['mux'].items():
                for pwr, v_pwr in options['pwr'].items():
                    config_filename = f'config_{mb}'
                    if n > 0:
                        config_filename += f'__{n}_{mux}'
                    if pwr != 'battery':
                        config_filename += f'_{pwr}'
                    config_filename += '.py'
                    if config_filename in configs_to_generate:
                        s = header
                        s += v_pwr
                        s += f"\n    'tx':  {v_mb['tx']},\n    'rx':  {v_mb['rx']},\n"
                        if n > 0:
                            s += """    'mux': {'boards':\n"""
                            for i in range(n):
                                print(n, i)
                                s += v_mux[i]
                            s += mux_footer[mb]
                        else:
                            s = s + """    'mux':  {'boards': {},
                 'default': {}
            }\n}""" + '\n'

                        s += footer
                        print(f'*** Preparing {config_filename} ***')
                        print(f'\n{s}')
                        config_filename = os.path.join(os.path.dirname(__file__), f'../configs/{config_filename}')
                        with open(f'{config_filename}', mode='wt') as config_file:
                            config_file.write(s)
                    else:
                        print(f'### skipping {config_filename} ###')
