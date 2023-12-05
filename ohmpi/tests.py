import json
import numpy as np
from ohmpi.config import (OHMPI_CONFIG,EXEC_LOGGING_CONFIG, DATA_LOGGING_CONFIG, SOH_LOGGING_CONFIG, MQTT_LOGGING_CONFIG,
                          MQTT_CONTROL_CONFIG)
from os import path, mkdir, statvfs
from time import gmtime
from termcolor import colored
import logging
from ohmpi.mqtt_handler import MQTTHandler
from ohmpi.compressed_sized_timed_rotating_handler import CompressedSizedTimedRotatingFileHandler
import sys
from termcolor import colored
import traceback
import copy
import time
from ohmpi.hardware_system import OhmPiHardware
from ohmpi.logging_setup import setup_loggers
from ohmpi.config import HARDWARE_CONFIG
from threading import Thread

# print('hardware_config_import',HARDWARE_CONFIG)

# logging_suffix = ''
# MQTT_LOGGING_CONFIG.update({'test_topic': f'ohmpi_{OHMPI_CONFIG["id"]}/test'})
# MQTT_LOGGING_CONFIG.update({'test_logging_level': logging.DEBUG})
#
# TEST_LOGGING_CONFIG = {
#     'logging_level': logging.INFO,
#     'logging_to_console': True,
#     'log_file_logging_level': logging.DEBUG,
#     'file_name': f'test{logging_suffix}.log',
#     'max_bytes': 16777216,
#     'backup_count': 1024,
#     'when': 'd',
#     'interval': 1
# }

def test_i2c_devices_on_bus(i2c_addr, bus):
    if bus.try_lock():
        i2c_addresses_on_bus = bus.scan()
        bus.unlock()
    if i2c_addr in i2c_addresses_on_bus:
        return True
    else:
        return False

# def setup_test_logger(mqtt=True):
#     msg = ''
#     # Message logging setup
#     log_path = path.join(path.dirname(__file__), 'logs')
#     if not path.isdir(log_path):
#         mkdir(log_path)
#     test_log_filename = path.join(log_path, TEST_LOGGING_CONFIG['file_name'])
#
#     test_logger = logging.getLogger('test_logger')
#
#     # TEST logging setup
#     # Set message logging format and level
#     log_format = '%(asctime)-15s | %(process)d | %(levelname)s: %(message)s'
#     logging_to_console = TEST_LOGGING_CONFIG['logging_to_console']
#     test_handler = CompressedSizedTimedRotatingFileHandler(test_log_filename,
#                                                            max_bytes=TEST_LOGGING_CONFIG['max_bytes'],
#                                                            backup_count=TEST_LOGGING_CONFIG['backup_count'],
#                                                            when=TEST_LOGGING_CONFIG['when'],
#                                                            interval=TEST_LOGGING_CONFIG['interval'])
#     test_formatter = logging.Formatter(log_format)
#     test_formatter.converter = gmtime
#     test_formatter.datefmt = '%Y-%m-%d %H:%M:%S UTC'
#     test_handler.setFormatter(test_formatter)
#     test_logger.addHandler(test_handler)
#     test_logger.setLevel(TEST_LOGGING_CONFIG['log_file_logging_level'])
#
#     if logging_to_console:
#         console_test_handler = logging.StreamHandler(sys.stdout)
#         console_test_handler.setLevel(TEST_LOGGING_CONFIG['logging_level'])
#         console_test_handler.setFormatter(test_formatter)
#         test_logger.addHandler(console_test_handler)
#
#     if mqtt:
#         mqtt_settings = MQTT_LOGGING_CONFIG.copy()
#         mqtt_test_logging_level = mqtt_settings.pop('test_logging_level', logging.DEBUG)
#         [mqtt_settings.pop(i, None) for i in ['client_id', 'exec_topic', 'data_topic', 'test_topic',
#                                               'data_logging_level', 'exec_logging_level']]
#         mqtt_settings.update({'topic': MQTT_LOGGING_CONFIG['test_topic']})
#         # TODO: handle the case of MQTT broker down or temporarily unavailable
#         try:
#             mqtt_test_handler = MQTTHandler(**mqtt_settings)
#             mqtt_test_handler.setLevel(mqtt_test_logging_level)
#             mqtt_test_handler.setFormatter(test_formatter)
#             test_logger.addHandler(mqtt_test_handler)
#             msg += colored(f"\n\u2611 Publishes execution as {MQTT_LOGGING_CONFIG['test_topic']} topic on the "
#                            f"{MQTT_LOGGING_CONFIG['hostname']} broker", 'blue')
#         except Exception as e:
#             msg += colored(f'\nWarning: Unable to connect to test topic on broker\n{e}', 'yellow')
#             mqtt = False
#
#     # try:
#     #     init_logging( test_logger,
#     #                  TEST_LOGGING_CONFIG['logging_level'], log_path, data_log_filename)
#     # except Exception as err:
#     #     msg += colored(f'\n\u26A0 ERROR: Could not initialize logging!\n{err}', 'red')
#
#     return test_logger, test_log_filename, TEST_LOGGING_CONFIG['logging_level'], msg


def test_mb_accessibility(hw_nc, module_name, test_logger, devices=['mcp','ads']):
    """
    Test accessibility to I2C devices on a measurement module (currently only mcp or ads on RX or TX).
    Test is successful if the I2C addresses of all devices being tested are visible when performing a I2C bus scan.

    Parameters
    ----------
    hw_nc: ohmpi.OhmPiHardware
      OhmPiHardware object of which "connect" parameter is set to False
    module_name: str
      Name of module (TX or RX)
    test_logger: logging.Logger
      Logger to be used to record test outputs and results, e.g. soh_logger.TEST or test_logger.info
    devices: str or list
      name or list of names of devices to be tested (currently can only be mcp or ads)

    Returns
    -------
    bool
       True if test successful, False otherwise.
    """
    if module_name == "TX":
        module = hw_nc.tx
    elif module_name == 'RX':
        module = hw_nc.rx
    test_logger(
        f"{module_name}: *** Start {module_name} accessibility test on {module.specs['model']} board ***")
    if isinstance(devices, str):
        devices = [devices]
    test_result = [False] * len(devices)
    for i, device in enumerate(devices):
        if f'{device}_address' in module.specs:
            if test_i2c_devices_on_bus(module.specs[f'{device}_address'], module.connection):
                test_logger(colored(
                    f"{module_name}: {device} with address {hex(module.specs[f'{device}_address'])} accessible on I2C bus.", "green"))
                test_result[i] = True
            else:
                test_logger(colored(
                    f"{module_name}: {device} with address {hex(module.specs[f'{device}_address'])} NOT accessible on I2C bus.", "red"))
        else:
            test_logger(colored(
                f"{module_name}: {device} with address {hex(module.specs[f'{device}_address'])} not in {module_name} config.", "yellow"))
    return all(test_result)

def test_mb_connectivity(hw_nc, module_name, test_logger, devices=['mcp', 'ads']):
    """
        Test connectivity to I2C devices on a measurement module (currently only mcp or ads on RX or TX).
        Test is successful if the I2C addresses of all devices being tested are visible when performing a I2C bus scan.

        Parameters
        ----------
        hw_nc: ohmpi.OhmPiHardware
          OhmPiHardware object of which "connect" parameter is set to False
        module_name: str
          Name of module (TX or RX)
        test_logger: logging.Logger
          Logger to be used to record test outputs and results, e.g. soh_logger.TEST or test_logger.info
        devices: str or list
          name or list of names of devices to be tested (currently can only be mcp or ads)

        Returns
        -------
        bool
           True if test successful, False otherwise.
        """
    if module_name == "TX":
        module = hw_nc.tx
    elif module_name == 'RX':
        module = hw_nc.rx
    test_logger(
        f"{module_name}: *** Start {module_name} connectivity test on {module.specs['model']} board ***")
    if isinstance(devices, str):
        devices = [devices]
    test_result = [False] * len(devices)
    for i, device in enumerate(devices):
        if f'{device}_address' in module.specs:
            try:
                getattr(module, f'reset_{device}')
                test_logger(colored(
                    f"{module_name}: Connection established with {device} with address {hex(module.specs[f'{device}_address'])}.", "green"))
                test_result[i] = True
            except:
                traceback.print_exc()
                test_logger(colored(
                    f"{module_name}: Connection NOT established with {device} with address {hex(module.specs[f'{device}_address'])}.", "red"))
        else:
            test_logger(colored(
                f"{module_name}: {device} with address {hex(module.specs[f'{device}_address'])} NOT in {module_name} config.", "yellow"))
    return all(test_result)

def test_mb_connection(hw_nc, module_name, test_logger, devices=['mcp','ads']):
    """
    Test connection to I2C devices in RX module.
    Calls in test_rx_accessibility first and then if successful calls in test_rx_connectivity.
    Test is successful if I2C addresses of all I2C devices being tested are visible when performing a I2C bus scan.

    Parameters
    ----------
    hw_nc: ohmpi.OhmPiHardware
      OhmPiHardware object of which "connect" parameter is set to False
    module_name: str
      Name of module (TX or RX)
    test_logger: logging.Logger
      Logger to be used to record test outputs and results, e.g. soh_logger.TEST or test_logger.info
    devices: str or list
      name or list of names of devices to be tested (currently can only be mcp or ads)

    Returns
    -------
    bool
       True if test successful, False otherwise.
    """

    if module_name == "TX":
        module = hw_nc.tx
    elif module_name == 'RX':
        module = hw_nc.rx

    test_logger(" ")
    test_logger(
        f"****************************************************************")
    test_logger(
        f"*** Start {module_name} connection test on {module.specs['model']} board ***")
    test_logger(
        f"****************************************************************")
    test_logger(" ")
    if isinstance(devices, str):
        devices = [devices]
    test_result = [False] * len(devices)
    for i, device in enumerate(devices):
        if f'{device}_address' in module.specs:
            # accessibility_results, connectivity_results = False, False
            accessibility_results = test_mb_accessibility(hw_nc, module_name, test_logger, devices=device)
            if accessibility_results:
                test_logger(
                    f"{module_name}: Accessibility test successful. Will check if device respond...")
                connectivity_results = test_mb_connectivity(hw_nc, module_name, test_logger, devices=device)
                if connectivity_results:
                    test_result[i] = True
    test_logger("")
    if all(test_result):
        test_logger(colored(
            f"*** {module_name}: Connection test successful ***", "green"))
    else:
        test_logger(colored(
            f"*** {module_name}: Connection test NOT successful ***", "red"))
    return all(test_result)

def test_mux_accessibility(hw_nc, test_logger, mux_id=None):
    """
    Test accessibility to one or all MUX boards in config. Test is successful if the I2C addresses of all multiplexers
    or switches being tested are visible when performing a I2C bus scan.

    Parameters
    ----------
    hw_nc: ohmpi.OhmPiHardware
      OhmPiHardware object of which "connect" parameter is set to False
    test_logger: logging.Logger
      Logger to be used to record test outputs and results, e.g. soh_logger.TEST or test_logger.info
    mux_id: str or None (optional)
      MUX ID name from a MUX_CONFIG used to initiate the OhmPiHardware object. If set to None, test will be performed
      on all MUX_boards listed in the MUX_CONFIG of hw_nc

    Returns
    -------
    bool
       True if test successful, False otherwise.
    """

    mux_boards = hw_nc.mux_boards
    test_logger(
        f"{mux_id}: *** Start MUX accessibility test  ***")
    if mux_id is None:
        mux_ids = [k for k in mux_boards.keys()]
        test_logger("Testing all MUX boards in MUX config.")

    else:
        if isinstance(mux_id, str):
            mux_ids = [mux_id]
        else:
            mux_ids = mux_id

    test_result = [False] * len(mux_ids)
    for i, mux_id in enumerate(mux_ids):
        mux = mux_boards[mux_id]
        test_logger(
            f"{mux_id}: *** Accessibility test initiated for {mux_id} with version {mux.model} ***")

        mux.reset_i2c_ext_tca()
        if mux._i2c_ext_tca_address is not None :
            if test_i2c_devices_on_bus(mux._i2c_ext_tca_address, mux._connection):
                test_logger(colored(
                    f"{mux_id}: i2c extension device with address {hex(mux._i2c_ext_tca_address)} is accessible on I2C bus.", "green"))
            else:
                test_logger(colored(
                    f"{mux_id}: i2c extension device with address {hex(mux._i2c_ext_tca_address)} is NOT accessible on I2C bus.", "red"))
                continue

        if mux.model == 'mux_2024_0_X':
            for mcp_address in mux._mcp_addresses:
                mcp_address = int(mcp_address, 16)
                if mcp_address is not None:
                    if test_i2c_devices_on_bus(mcp_address, mux.connection):
                        test_logger(colored(
                            f"{mux_id}: device with address {hex(mcp_address)} is accessible on I2C bus.", "green"))
                        test_result[i] = True
                    else:
                        test_logger(colored(
                            f"{mux_id} with address {hex(mcp_address)} is NOT accessible on I2C bus.", "red"))

        elif mux.model == 'mux_2023_0_X':
            if f'mux_tca_address' in mux.specs:
                mux.reset_i2c_ext_tca()
                if test_i2c_devices_on_bus(mux.specs['mux_tca_address'], mux.connection):
                    test_logger(f"{mux_id}: TCA device with address {hex(mux.specs['mux_tca_address'])} is accessible on I2C bus.")
                    for c, channel in enumerate(mux._tca_channels):
                        if test_i2c_devices_on_bus(mux.mcp_addresses[c], channel):
                            test_logger(colored(
                                f"{mux_id}: MCP device with address {hex(mux.mcp_addresses[c])} on channel {channel} is accessible on I2C bus.", "green"))
                            test_result[i] = True
                        else:
                            test_logger(colored(
                                f"{mux_id}: MCP device address {hex(mux.mcp_addresses[c])} on channel {channel} is NOT accessible on I2C bus.", "red"))
                else:
                    test_logger(colored(
                        f"{mux_id}: TCA device with address {hex(mcp_address)} is NOT accessible on I2C bus.", "red"))
    return all(test_result)


def test_mux_connectivity(hw_nc, test_logger, mux_id=None):
    """
    Test connectivity to one or all MUX boards in config. Test is successful if all I2C multiplexers or switches
     being tested are responsive.

    Parameters
    ----------
    hw_nc: ohmpi.OhmPiHardware
        OhmPiHardware object of which "connect" parameter is set to False
    test_logger: logging.Logger
        Logger to be used to record test outputs and results, e.g. soh_logger.TEST or test_logger.info
    mux_id: str or None (optional)
        MUX ID name from a MUX_CONFIG used to initiate the OhmPiHardware object. If set to None, test will be performed
        on all MUX_boards listed in the MUX_CONFIG of hw_nc

    Returns
    -------
    bool
         True if test successful, False otherwise.
    """
    mux_boards = hw_nc.mux_boards
    test_logger(
        f"{mux_id}: *** Start MUX connectivity test  ***")
    if mux_id is None:
        mux_ids = [k for k in mux_boards.keys()]
        test_logger("Testing all MUX boards in MUX config.")

    else:
        if isinstance(mux_id, str):
            mux_ids = [mux_id]
        else:
            mux_ids = mux_id

    test_result = [False] * len(mux_ids)
    for i, mux_id in enumerate(mux_ids):
        mux = mux_boards[mux_id]
        test_logger(
            f"{mux_id}: *** Connectivity test initiated for {mux_id} with version {mux.model} ***")
        for m in range(len(mux._mcp)):
            try:
                mux.reset_i2c_ext_tca()
                mux.reset_one(which=m)
                mcp_address = int(mux._mcp_addresses[m], 16)
                test_logger(colored(
                    f"{mux_id}: Connection established with MCP device with address {hex(mcp_address)}", "green"))
                test_result[i] = True
            except:
                traceback.print_exc()
                test_logger(colored(
                    f"{mux_id}: Connection NOT established with MCP device with address {hex(mcp_address)}", "red"))
    return all(test_result)

def test_mux_connection(hw_nc, test_logger, mux_id=None):
    """
    Test connection to one or all MUX boards in config.
    Calls in test_MUX_accessibility first and then if successful calls in test_mux_connectivity.
    Test is successful if I2C addresses of all multiplexers or switches being tested are visible when performing
      a I2C bus scan.

    Parameters
    ----------
    hw_nc: ohmpi.OhmPiHardware
        OhmPiHardware object of which "connect" parameter is set to False
    test_logger: logging.Logger
        Logger to be used to record test outputs and results, e.g. soh_logger.TEST or test_logger.info
    mux_id: str or None (optional)
        MUX ID name from a MUX_CONFIG used to initiate the OhmPiHardware object. If set to None, test will be performed
        on all MUX_boards listed in the MUX_CONFIG of hw_nc

    Returns
    -------
    bool
         True if test successful, False otherwise.
    """
    mux_boards = hw_nc.mux_boards
    test_logger(" ")
    test_logger(
        f"****************************************************************")
    test_logger(
        f"*** Start MUX connection test ***")
    test_logger(
        f"****************************************************************")
    test_logger(" ")
    if mux_id is None:
        mux_ids = [k for k in mux_boards.keys()]
        test_logger("Testing all MUX boards in MUX config.")

    else:
        if isinstance(mux_id, str):
         mux_ids = [mux_id]
        else:
            mux_ids = mux_id

    test_result = [False] * len(mux_ids)
    for i, mux_id in enumerate(mux_ids):
        mux = mux_boards[mux_id]
        test_logger("")
        test_logger(
            f"{mux_id}: *** Connection test initiated for {mux_id} with version {mux.model} ***")
        accessibility_results, connectivity_results = False, False
        accessibility_results = test_mux_accessibility(hw_nc, test_logger, mux_id=mux_id)
        if accessibility_results:
            test_logger(
                f"{mux_id}: Accessibility test successful. Will check if device respond...")
            connectivity_results = test_mux_connectivity(hw_nc, test_logger, mux_id=mux_id)
            if connectivity_results:
                test_result[i] = True
    test_logger("")
    if all(test_result):
        test_logger(colored(
            f"*** MUX connection test successful ***", "green"))

    else:
        test_logger(colored(
            f"*** MUX connection test NOT successful ***", "red"))

    return all(test_result)


def test_pwr_connection(hw_nc, test_logger):
    tx = hw_nc.tx
    if tx.pwr.voltage_adjustable:
        try:
            pass
        except:
            traceback.print_exc()
    else:
        test_logger(colored('Pwr cannot be tested with this system configuration.', "yellow"))

def test_vmn_hardware_offset(hw, test_logger, deviation_threshold=10., return_deviation=False):
    """
    Test R shunt by comparing current measured by TX and current given by PWR module. Test can only be performed with
    power source havig pwr_voltage_adjustable set to False (i.e. currently pwr_dps5005 only)

    Parameters
    ----------
    hw: ohmpi.OhmPiHardware
    test_logger: logging.logger
      Logger to be used to record test outputs and results, e.g. soh_logger.TEST or test_logger.info
    deviation_threshold: float (default: 10)
      threshold in percent below which test is successful
    return_deviation: bool (default: False)
      if set to True, will return estimated deviation of VMN_hardware_offset compared to config

    Returns
    -------
    bool
     True if test successful, False otherwise.
    float
      Estimated R shunt deviation from config, if return_values is set to True
    """

    test_logger(" ")
    test_logger(
        f"****************************************************************")
    test_logger(
        f"*** Start Vmn hardware offset test ***")
    test_logger(
        f"****************************************************************")
    test_logger(" ")

    test_result = False
    quad = [1, 2]
    hw.rx._dg411_gain = .5
    vmns = np.zeros(20)
    roles = ['M', 'N']
    hw.switch_mux(quad, roles, state='on')

    for i in range(vmns.shape[0]):
        vmns[i] = (hw.rx.voltage * hw.rx._dg411_gain + hw.rx._bias) + hw.rx._vmn_hardware_offset
        time.sleep(.1)
    vmn = np.mean(vmns[-10:])
    vmn_std = np.std(vmns[-10:])
    hw.switch_mux(quad, roles, state='off')

    # tx_volt = 0.
    # injection_duration = .5
    # duty_cycle = .5 # or 0
    # nb_stack = 2
    # delay = injection_duration * 2/3
    # if self.switch_mux_on(quad,roles):
    #     hw.vab_square_wave(tx_volt, cycle_duration=injection_duration * 2 / duty_cycle, cycles=nb_stack,
    #                              duty_cycle=duty_cycle)
    # vmn = hw.last_vmn(delay=delay)
    # vmn_std = hw.last_vmn_dev(delay=delay)
    vmn_deviation_from_offset = abs(1 - vmn / hw.rx._vmn_hardware_offset) * 100
    if vmn_deviation_from_offset <= deviation_threshold:
        test_logger(colored(
            f"Test Vmn hardware offset: Vmn offset deviation from config = {vmn_deviation_from_offset: .2f} %", "green"))
        test_result = True
    else:
        test_logger(colored(
            f"Test Vmn hardware offset: WARNING... measured VMN offset = {vmn:.2f} %",
            "yellow"))
        test_logger(colored(
        f"Test Vmn hardware offset: WARNING... Vmn offset deviation from config = {vmn_deviation_from_offset:.2f} %", "yellow"))

    if return_deviation:
        return test_result, vmn_deviation_from_offset
    else:
        return test_result


def test_r_shunt(hw, test_logger, deviation_threshold=10., return_deviation=False):
    """
    Test R shunt by comparing current measured by TX and current given by PWR module. Given the low resolution of the
     power module compared to the ADS resolution, the test is performed while shortcutting A and B at low voltage
     to ensure a higher current (current_max is temporarily set to 45 mA).
     If roles on the measurement board are connected to MUX boards, then the software creates a shortcut.
     If no MUX boards are connected, then roles A and B must be manually set in a closed circuit.
    Test can only be performed with power source having pwr_voltage_adjustable set to True (i.e. currently pwr_dps5005 only) and

    Parameters
    ----------
    hw: ohmpi.OhmPiHardware
    test_logger: logging.logger
      Logger to be used to record test outputs and results, e.g. soh_logger.TEST or test_logger.info
    deviation_threshold: float (default: 10)
      threshold in percent below which test is successful
    return_deviation: bool (default: False)
      if set to True, will return estimated R shunt deviation from config

    Returns
    -------
    bool
     True if test successful, False otherwise.
    float
      Estimated R shunt deviation from config, if return_values is set to True
    """

    test_logger(" ")
    test_logger(
        f"****************************************************************")
    test_logger(
        f"*** Start R shunt test ***")
    test_logger(
        f"****************************************************************")
    test_logger(" ")

    if hw.tx.pwr.voltage_adjustable:
        # check pwr is on, if not, let's turn it on
        switch_tx_pwr_off = False
        if hw.pwr_state == 'off':
            hw.pwr_state = 'on'
            switch_tx_pwr_off = True
        test_result = False
        if hw._cabling == {}:
            test_logger("!!! R Shunt test: No MUX board in config. Manual AB shortcut required !!!") #TODO: ask user to press button if AB are shortcut
        else:
            quad = [1, 1]  #TODO: change to first electrode in cabling
        roles = ['A','B']
        tx_volt = .5
        injection_duration = 2.

        if hw.tx.voltage != tx_volt:
            hw.tx.voltage = tx_volt

        hw.tx.pwr._voltage_max = 0.1
        hw.tx.pwr._current_max_tolerance = 0.
        hw.tx.pwr.current_max = 0.045  # mA

        # turn dps_pwr_on if needed
        switch_pwr_off = False
        if hw.pwr.pwr_state == 'off':
            hw.pwr.pwr_state = 'on'
            switch_pwr_off = True

        hw.switch_mux(quad, roles, state='on', bypass_ab_check=True)

        # hw._vab_pulse(duration=injection_duration, vab=tx_volt)
        time.sleep(.5)
        injection = Thread(target=hw._inject, kwargs={'injection_duration': injection_duration, 'polarity': 1})
        readings = Thread(target=hw._read_values, kwargs={'sampling_rate': hw.sampling_rate, 'append': False, 'test_r_shunt': True})
        readings.start()
        injection.start()
        readings.join()
        injection.join()
        hw.tx.polarity = 0

        iab = hw.readings[-3:, 3]
        vab = hw.tx.pwr.voltage
        # hw.tx.pwr._retrieve_current()
        iab_dps = hw._current [-3:]
        # print(iab, iab_dps, vab)

        # close mux path and put pin back to GND
        hw.switch_mux(quad, roles, state='off')

        iab_deviation = abs(1 - np.mean(iab) / np.mean(iab_dps)) * 100

        if iab_deviation <= deviation_threshold:
            test_logger(colored(
                f"Test r_shunt: R shunt deviation from config = {iab_deviation: .3f} %", "green"))
            test_result = True
        else:
            test_logger(colored(
                f"Test r_shunt: Warning... R shunt deviation from config = {iab_deviation: .3f} %", "yellow"))

        hw._current_max_tolerance = hw.tx.pwr.specs['current_max_tolerance'] #set back default value
        hw.tx.pwr._voltage_max = hw.tx.pwr.specs['voltage_max'] #set back to default value
        hw.tx.pwr.current_max = hw.tx.pwr.specs['current_max'] #set back to default value

        hw.status = 'idle'
        if switch_pwr_off:
            hw.pwr.pwr_state = 'off'

        # if power was off before measurement, let's turn if off
        if switch_tx_pwr_off:
            hw.pwr_state = 'off'
    else:
        test_logger('R shunt cannot be tested with this system configuration.')

    if return_deviation:
        return test_result, iab_deviation
    else:
        return test_result

def test_dg411_gain_ratio(hw, test_logger, return_deviation=False, deviation_threshold=5):
    """
    Test DG411 gain ratio by comparing voltage measured by ADS from RX at rest when DG411 gain is set to 1 or to value
    of DG411_gain_ratio from config (0.5 by default).

    Parameters
    ----------
    hw: ohmpi.OhmPiHardware
    test_logger: logging.logger
      Logger to be used to record test outputs and results, e.g. soh_logger.TEST or test_logger.info
    deviation_threshold: float
      threshold in percent below which test is successful
    return_deviation: bool (default False)
      if set to True, will return estimated dg411 gain ratio deviation from config (value lower than 5% is acceptable)

    Returns
    -------
    bool
     True if test successful (i.e. if , False otherwise.
    float
      Estimated DG411 gain ratio deviation from config, if return_values is set to True
    """

    test_logger(" ")
    test_logger(
        f"****************************************************************")
    test_logger(
        f"*** Start DG411 gain ratio test ***")
    test_logger(
        f"****************************************************************")
    test_logger(" ")

    test_result = False

    hw.rx._dg411_gain = 1
    time.sleep(4)
    # voltages = np.zeros(10)
    # for i in range(voltages.shape[0]):
    #     hw.tx.pin_DG0 = True
    #     time.sleep(.1)
    #     voltages[i] = hw.rx.voltage
    #
    #     # voltages[i] = hw.rx.voltage

    voltage1 = hw.rx.voltage #np.mean(voltages[-5:])
    hw.rx._dg411_gain = 0.5
    # voltages = np.zeros(10)
    # for i in range(voltages.shape[0]):
    #     time.sleep(.1)
    #     # hw.tx.pin_DG0 = True
    #     voltages[i] = hw.rx.voltage
    #
    #     # voltages[i] = hw.rx.voltage
    #     hw.tx.pin_DG0 = False

    voltage2 = hw.rx.voltage #np.mean(voltages[-5:])

    voltage_gain_ratio = voltage1 / voltage2
    voltage_gain_ratio_deviation = abs(1 - hw.rx._dg411_gain_ratio / voltage_gain_ratio) * 100

    if voltage_gain_ratio_deviation <= deviation_threshold:
        test_result = True
        test_logger(colored(
            f"DG411 Test: Measured DG411 gain ratio = {voltage_gain_ratio: .1f}", "green"))
        test_logger(colored(
            f"DG411 Test: Warning... Deviation of DG411 gain ratio from config = {voltage_gain_ratio_deviation: .2f} %", "green"))
    else:
        test_logger(colored(
            f"DG411 Test: Measured DG411 gain ratio = {voltage_gain_ratio: .1f}", "yellow"))
        test_logger(colored(
        f"DG411 Test: Warning... Deviation of DG411 gain ratio from config = {voltage_gain_ratio_deviation: .2f} %", "yellow"))

    if return_deviation:
        return test_result, voltage_gain_ratio_deviation
    else:
        return test_result


def test_mqtt_broker(hw):
    pass

def test_mux_relays(hw, test_logger, mux_id=None, electrodes=None, roles=None, test_on=None):

    mux_boards = hw.mux_boards
    test_logger(" ")
    test_logger(
        f"****************************************************************")
    test_logger(
        f"*** Start MUX relays test ***")
    test_logger(
        f"****************************************************************")
    test_logger(" ")
    if mux_id is None:
        test_logger("Testing all MUX boards in MUX config.")
        list_of_muxes = [i for i in hw.mux_boards.keys()]
        list_of_muxes.sort()
    else:
        list_of_muxes = [mux_id]
    electrodes_in_config = []
    for mux_id in list_of_muxes:
        electrodes_in_config.append([c[0] for c in hw.mux_boards[mux_id].cabling.keys()])
    electrodes_in_config = np.unique(np.concatenate(np.array(electrodes_in_config)))
    if electrodes is None:
        electrodes = electrodes_in_config
    else:
        electrodes = electrodes[np.in1d(electrodes,electrodes_in_config)]
    electrodes = np.sort(electrodes)

    if roles is None:
        roles = []
        for mux_id in list_of_muxes:
            roles.append([c[1] for c in hw.mux_boards[mux_id].cabling.keys()])
        roles = np.concatenate(np.array(roles))
    roles = np.unique(np.sort(np.array(roles)))
    print(electrodes, roles, list_of_muxes)

    if hw._cabling == {}:
        test_logger(colored(
            "!!! MUX relays test: No MUX board in config !!! Abort..."), "yellow")  # TODO: ask user to press button if AB are shortcut
        return
    # roles = ['A', 'B']
    if ('A' in roles and 'B' in roles and test_on != 'MN') or test_on == 'AB':
        if roles.shape[0] > 2:
            test_roles = ['A', 'B']
        else:
            test_roles = roles  # This allows to test relays of other roles which are manually connected to AB connectors of measurement board

        if hw.tx.pwr.voltage_adjustable:
            switch_tx_pwr_off = False
            if hw.pwr_state == 'off':
                hw.pwr_state = 'on'
                switch_tx_pwr_off = True

            for electrode in electrodes:
                # check pwr is on, if not, let's turn it on


                test_result = False

                quad = [electrode] * len(test_roles)
                tx_volt = .5  # in V
                injection_duration = 5. * (1. / hw.sampling_rate) # 5 samples

                hw.switch_mux(quad, test_roles, state='on', bypass_ab_check=True, bypass_check=True)
                hw.tx.pwr._voltage_max = 0.2
                hw.tx.pwr._current_max_tolerance = 0.
                hw.tx.pwr.current_max = 0.010  # in A

                if hw.tx.voltage != tx_volt:
                    hw.tx.voltage = tx_volt
                # turn dps_pwr_on if needed
                switch_pwr_off = False
                if hw.pwr.pwr_state == 'off':
                    hw.pwr.pwr_state = 'on'
                    switch_pwr_off = True

                time.sleep(.2)
                injection = Thread(target=hw._inject, kwargs={'injection_duration': injection_duration, 'polarity': 1})
                readings = Thread(target=hw._read_values, kwargs={'sampling_rate': hw.sampling_rate, 'append': False})
                readings.start()
                injection.start()
                readings.join()
                injection.join()
                hw.tx.polarity = 0

                iab = np.mean(hw.readings[-3:, 3])

                # close mux path and put pin back to GND
                hw.switch_mux(quad, test_roles, state='off')
                print(iab)
                if iab > 5.: # at least 5 mA means shortcut is done
                    test_logger(colored(
                         f"Test MUX relays AB - Electrode {electrode}: Relay {' and Relay '.join(str(r) for r in test_roles)} successfully switching", "green"))
                    test_result = True
                else:
                    test_logger(colored(
                         f"Test MUX relays AB - Electrode {electrode}: WARNING... Relay {' and Relay '.join(str(r) for r in test_roles)} not switching properly", "yellow"))
                    test_logger(colored(
                        f"Test MUX relays AB - Electrode {electrode}: WARNING... Single roles A and B need to be manually checked while manually shortcutting A and B", "yellow"))
                    test_logger(colored(
                        "Then call e.g.: test__mux_relays(roles=['A'], test_on='AB')", "yellow"))

                hw._current_max_tolerance = hw.tx.pwr.specs['current_max_tolerance'] #set back default value
                hw.tx.pwr._voltage_max = hw.tx.pwr.specs['voltage_max'] #set back to default value
                hw.tx.pwr.current_max = hw.tx.pwr.specs['current_max'] #set back to default value
                time.sleep(.2)

                hw.status = 'idle'

                if switch_pwr_off:
                    hw.pwr.pwr_state = 'off'

            # if power was off before measurement, let's turn if off
            if switch_tx_pwr_off:
                hw.pwr_state = 'off'
        else:
            test_logger(colored(
                'WARNING... MUX AB cannot be tested with this system configuration since power is not adjustable', 'yellow'))
            test_logger(colored(
                'WARNING... Please connect roles AB to AB connectors on measurmeent board', 'yellow'))
            test_logger(colored(
                "Then call e.g.: test__mux_relays(roles=['A', 'B'], test_on='MN')", "yellow"))

    if ('M' in roles and 'N' in roles and test_on != 'AB') or test_on == 'MN':
        for electrode in electrodes:
            if roles.shape[0] > 2:
                test_roles = ['M', 'N']
            else:
                test_roles = roles  # This allows to test relays of other roles which are manually connected to MN connectors of measurement board

            quad = [electrode] * len(test_roles)
            hw.switch_mux(quad, test_roles, state='on', bypass_ab_check=True, bypass_check=True)
            vmns = np.zeros(10)
            for i in range(vmns.shape[0]):
                vmns[i] = hw.rx.voltage
                time.sleep(.1)
            vmn = np.mean(vmns[-5:])
            vmn_std = np.std(vmns[-5:])
            hw.switch_mux(quad, test_roles, state='off')
            test_logger(
                f"Test MUX relays MN - Electrode {electrode}: Vmn at rest = {vmn:.2f} mV")
            if abs(vmn) < 100:
                test_logger(colored(
                     f"Test MUX relays MN - Electrode {electrode}: Relay {' and Relay '.join(str(r) for r in test_roles)} successfully switching", "green"))
                test_result = True
            else:
                test_logger(colored(
                     f"Test MUX relays MN - Electrode {electrode}: WARNING... Relay  {' and Relay '.join(str(r) for r in test_roles)} not switching properly", "yellow"))
                test_logger(colored(
                    f"Test MUX relays MN - Electrode {electrode}: WARNING... Single roles M and N need to be manually checked while manually shortcutting M and N", "yellow"))
                test_logger(colored(
                    f"Then call e.g.: test_mux_relays(roles=['M'], test_on='MN')", "yellow"))

def test_polarity_relays():
    pass

def test_tx_battery_voltage(hw, test_logger, threshold=11.8):
    # if hw.tx.pwr.voltage_adjustable:
    test_result = False
    if hw.tx.pwr.voltage_adjustable:
        switch_tx_pwr_off = False
        if hw.pwr_state == 'off':
            hw.pwr_state = 'on'
            switch_tx_pwr_off = True

    battery_voltage = hw.tx.pwr.battery_voltage()
    if battery_voltage > threshold:
        test_logger(colored(f"Test TX Battery voltage = {battery_voltage:.2f}", "green"))
        test_result = True
    else:
        test_logger(colored(f"Test TX Battery voltage = {battery_voltage:.2f}", "green"))

    if switch_tx_pwr_off:
        hw.pwr_state = 'off'
    return test_result