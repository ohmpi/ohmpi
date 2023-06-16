import io
import os
import shutil
import collections.abc
import numpy as np


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
    print(log)
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
                if tag[i] == 'INFO':
                    if 'NEW SESSION' in msg[i]:
                        s += 1
                session.append(s)
            elif "{" in line or msg_started:
                msg_tmp = msg_tmp + line
                print(msg_tmp)
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
