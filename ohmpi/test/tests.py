import json
from ohmpi.config import (OHMPI_CONFIG,EXEC_LOGGING_CONFIG, DATA_LOGGING_CONFIG, SOH_LOGGING_CONFIG, MQTT_LOGGING_CONFIG,
                          MQTT_CONTROL_CONFIG)
from os import path, mkdir, statvfs
from time import gmtime
import logging
from ohmpi.mqtt_handler import MQTTHandler
from ohmpi.compressed_sized_timed_rotating_handler import CompressedSizedTimedRotatingFileHandler
import sys
from termcolor import colored
import traceback
from ohmpi.hardware_system import OhmPiHardware
from ohmpi.logging_setup import setup_loggers
from ohmpi.config import HARDWARE_CONFIG

print('hardware_config_import',HARDWARE_CONFIG)

logging_suffix = ''
MQTT_LOGGING_CONFIG.update({'test_topic': f'ohmpi_{OHMPI_CONFIG["id"]}/test'})
MQTT_LOGGING_CONFIG.update({'test_logging_level': logging.DEBUG})

TEST_LOGGING_CONFIG = {
    'logging_level': logging.INFO,
    'logging_to_console': True,
    'log_file_logging_level': logging.DEBUG,
    'file_name': f'test{logging_suffix}.log',
    'max_bytes': 16777216,
    'backup_count': 1024,
    'when': 'd',
    'interval': 1
}


def test_i2c_devices_on_bus(i2c_addr, bus):
    i2c_addresses_on_bus = bus.scan()
    print(i2c_addresses_on_bus)
    if i2c_addr in i2c_addresses_on_bus:
        return True
    else:
        return False

def setup_test_logger(mqtt=True):
    msg = ''
    # Message logging setup
    log_path = path.join(path.dirname(__file__), 'logs')
    if not path.isdir(log_path):
        mkdir(log_path)
    test_log_filename = path.join(log_path, TEST_LOGGING_CONFIG['file_name'])

    test_logger = logging.getLogger('test_logger')

    # TEST logging setup
    # Set message logging format and level
    log_format = '%(asctime)-15s | %(process)d | %(levelname)s: %(message)s'
    logging_to_console = TEST_LOGGING_CONFIG['logging_to_console']
    test_handler = CompressedSizedTimedRotatingFileHandler(test_log_filename,
                                                           max_bytes=TEST_LOGGING_CONFIG['max_bytes'],
                                                           backup_count=TEST_LOGGING_CONFIG['backup_count'],
                                                           when=TEST_LOGGING_CONFIG['when'],
                                                           interval=TEST_LOGGING_CONFIG['interval'])
    test_formatter = logging.Formatter(log_format)
    test_formatter.converter = gmtime
    test_formatter.datefmt = '%Y-%m-%d %H:%M:%S UTC'
    test_handler.setFormatter(test_formatter)
    test_logger.addHandler(test_handler)
    test_logger.setLevel(TEST_LOGGING_CONFIG['log_file_logging_level'])

    if logging_to_console:
        console_test_handler = logging.StreamHandler(sys.stdout)
        console_test_handler.setLevel(TEST_LOGGING_CONFIG['logging_level'])
        console_test_handler.setFormatter(test_formatter)
        test_logger.addHandler(console_test_handler)

    if mqtt:
        mqtt_settings = MQTT_LOGGING_CONFIG.copy()
        mqtt_test_logging_level = mqtt_settings.pop('test_logging_level', logging.DEBUG)
        [mqtt_settings.pop(i, None) for i in ['client_id', 'exec_topic', 'data_topic', 'test_topic',
                                              'data_logging_level', 'exec_logging_level']]
        mqtt_settings.update({'topic': MQTT_LOGGING_CONFIG['test_topic']})
        # TODO: handle the case of MQTT broker down or temporarily unavailable
        try:
            mqtt_test_handler = MQTTHandler(**mqtt_settings)
            mqtt_test_handler.setLevel(mqtt_test_logging_level)
            mqtt_test_handler.setFormatter(test_formatter)
            test_logger.addHandler(mqtt_test_handler)
            msg += colored(f"\n\u2611 Publishes execution as {MQTT_LOGGING_CONFIG['test_topic']} topic on the "
                           f"{MQTT_LOGGING_CONFIG['hostname']} broker", 'blue')
        except Exception as e:
            msg += colored(f'\nWarning: Unable to connect to test topic on broker\n{e}', 'yellow')
            mqtt = False

    # try:
    #     init_logging( test_logger,
    #                  TEST_LOGGING_CONFIG['logging_level'], log_path, data_log_filename)
    # except Exception as err:
    #     msg += colored(f'\n\u26A0 ERROR: Could not initialize logging!\n{err}', 'red')

    return test_logger, test_log_filename, TEST_LOGGING_CONFIG['logging_level'], msg

class OhmPiTests():
    """
    OhmPiTests class .
    """
    def __init__(self, mqtt=True, config=None):
        # set loggers
        self.test_logger, _, _, _ = setup_test_logger(mqtt=mqtt)
        self.exec_logger, _, self.data_logger, _, self.soh_logger, _, _, msg = setup_loggers(mqtt=mqtt)
        print(msg)
        HARDWARE_CONFIG_nc = HARDWARE_CONFIG.copy()
        print("Hardware_config", HARDWARE_CONFIG)

        # specify loggers when instancing the hardware
        self._hw = OhmPiHardware(**{'exec_logger': self.exec_logger, 'data_logger': self.data_logger,
                                    'soh_logger': self.soh_logger}, hardware_config=HARDWARE_CONFIG)

        print('config',HARDWARE_CONFIG_nc)
        for k, v in HARDWARE_CONFIG_nc.items():
            if k == 'mux':
                HARDWARE_CONFIG_nc[k]['default'].update({'connect': False})
            else:
                HARDWARE_CONFIG_nc[k].update({'connect': False})

        self._hw_nc = OhmPiHardware(**{'exec_logger': self.exec_logger, 'data_logger': self.data_logger,
                                    'soh_logger': self.soh_logger}, hardware_config=HARDWARE_CONFIG_nc)


        self.test_logger.info('Hardware configured...')
        self.test_logger.info('OhmPi tests ready to start...')

    def test_connections(self):
        pass

    def test_tx_accessibility(self, devices=['mcp','ads']):
        tx = self._hw_nc.tx
        self.test_logger.info(
            f"\n### Start TX accessibility test on {tx.specs['model']} board ###")
        test_result = [False] * len(devices)
        for i, device in enumerate(devices):
            if f'{device}_address' in tx.specs:
                if test_i2c_devices_on_bus(tx.specs[f'{device}_address'], tx.connection):
                    self.test_logger.info(f"{device} with address {hex(tx.specs[f'{device}_address'])} accessible on I2C bus.")
                    test_result[i] = True
                else:
                    self.test_logger.info(
                        f"TX: {device} with address {hex(tx.specs[f'{device}_address'])} NOT accessible on I2C bus.")
            else:
                self.test_logger.info(
                    f"TX: {device} with address {hex(tx.specs[f'{device}_address'])} not in TX config.")
        return all(test_result)

    def test_tx_connectivity(self, devices=['mcp','ads']):
        tx = self._hw_nc.tx
        self.test_logger.info(
            f"\n### Start TX connectivity test on {tx.specs['model']} board ###")
        test_result = [False] * len(devices)
        for i, device in enumerate(devices):
            if f'{device}_address' in tx.specs:
                try:
                    getattr(f'tx.reset_{device}')
                    self.test_logger.info(f"TX: Connection established with {device} with address {hex(tx.specs[f'{device}_address'])}.")
                    test_result[i] = True
                except:
                    self.test_logger.info(
                        f"TX: Connection NOT established with {device} with address {hex(tx.specs[f'{device}_address'])}.")
            else:
                self.test_logger.info(
                    f"TX: {device} with address {hex(tx.specs[f'{device}_address'])} not in TX config.")
        return all(test_result)

    def test_tx_connection(self, devices=['mcp', 'ads']):
        tx = self._hw_nc.tx
        self.test_logger.info(
            f"\n### Start TX connection test on {tx.specs['model']} board ###")

        test_result = [False] * len(devices)
        for i, device in enumerate(devices):
            if f'{device}_address' in tx.specs:
                accessibility_results, connectivity_results = False, False
                accessibility_results = self.test_tx_accessibility(devices=device)
                if accessibility_results:
                    self.test_logger.info(
                        f"Accessibility test successful. Will check if device respond...")
                    connectivity_results = self.test_tx_connectivity(devices=device)
                    if connectivity_results:
                        self.test_logger.info(
                            f"\nTX Connection test successful for {device} with address {hex(tx.specs[f'{device}_address'])}.")
                        test_result[i] = True

        return all(test_result)

    def test_rx_accessibility(self, devices=['mcp','ads']):
        rx = self._hw_nc.rx
        self.test_logger.info(
            f"\n### Start RX accessibility test on {rx.specs['model']} board ###")
        test_result = [False] * len(devices)
        for i, device in enumerate(devices):
            if f'{device}_address' in rx.specs:
                if test_i2c_devices_on_bus(rx.specs[f'{device}_address'], rx.connection):
                    self.test_logger.info(
                        f"RX: {device} with address {hex(rx.specs[f'{device}_address'])} accessible on I2C bus.")
                    test_result[i] = True
                else:
                    self.test_logger.info(
                        f"RX: {device} with address {hex(rx.specs[f'{device}_address'])} NOT accessible on I2C bus.")
            else:
                self.test_logger.info(
                    f"RX: {device} with address {hex(rx.specs[f'{device}_address'])} not in RX config.")
        return all(test_result)

    def test_rx_connectivity(self, devices=['mcp', 'ads']):
        rx = self._hw_nc.rx
        self.test_logger.info(
            f"\n### Start RX connectivity test on {rx.specs['model']} board ###")
        test_result = [False] * len(devices)
        for i, device in enumerate(devices):
            if f'{device}_address' in rx.specs:
                try:
                    getattr(f'rx.reset_{device}')
                    self.test_logger.info(
                        f"RX: Connection established with {device} with address {hex(rx.specs[f'{device}_address'])}.")
                    test_result[i] = True
                except:
                    self.test_logger.info(
                        f"RX: Connection NOT established with {device} with address {hex(rx.specs[f'{device}_address'])}.")
            else:
                self.test_logger.info(
                    f"RX: {device} with address {hex(rx.specs[f'{device}_address'])} not in RX config.")
        return all(test_result)

    def test_rx_connection(self, devices=['mcp','ads']):
        rx = self._hw_nc.rx
        self.test_logger.info(
            f"\n### Start RX connection test on {rx.specs['model']} board ###")

        test_result = [False] * len(devices)
        for i, device in enumerate(devices):
            if f'{device}_address' in rx.specs:
                accessibility_results, connectivity_results = False, False
                accessibility_results = self.test_rx_accessibility(devices=device)
                if accessibility_results:
                    self.test_logger.info(
                        f"Accessibility test successful. Will check if device respond...")
                    connectivity_results = self.test_rx_connectivity(devices=device)
                    if connectivity_results:
                        self.test_logger.info(
                            f"\nRX connection test successful for {device} with address {hex(rx.specs[f'{device}_address'])}.")
                        test_result[i] = True

        return all(test_result)


    def test_mux_accessibility(self, mux_id=None):
        self.test_logger.info(
            f"\n### Start MUX accessibility test  ###")

        if mux_id is None:
            mux_ids = [k for k in self._hw_nc.mux_boards.keys()]
            self.test_logger("Testing all MUX boards in MUX config.")

        if isinstance(mux_id, str):
            mux_ids = [mux_id]
        else:
            mux_ids = mux_id
        test_result = [False] * len(mux_ids)
        for i, mux_id in enumerate(mux_ids):
            mux = self._hw_nc.mux_boards[mux_id]
            self.test_logger.info(
                f"\n### Accessibility test initiated for {mux_id} with version {mux.model} ###")
            if mux.model == 'mux_2024_0_X':
                print(mux.model)
                for mcp_address in mux._mcp_addresses:
                    print(mcp_address)
                    if mcp_address is not None:
                        if test_i2c_devices_on_bus(mcp_address, mux.connection):
                            self.test_logger.info(
                                f"{mux_id} with address {hex(mcp_address)} is accessible on I2C bus.")
                            test_result[i] = True
                        else:
                            self.test_logger.info(f"{mux_id} with address {hex(mcp_address)} is NOT accessible on I2C bus.")
            elif mux.model == 'mux_2023_0_X':
                if f'mux_tca_address' in mux.specs:
                    if test_i2c_devices_on_bus(mux.specs['mux_tca_address'], mux.connection):
                        self.test_logger.info(f"{mux_id} with address {hex(mux.specs['mux_tca_address'])} is accessible on I2C bus.")
                        test_result[i] = True
                    else:
                        self.test_logger.info(f"{mux_id} with address {hex(mcp_address)} is NOT accessible on I2C bus.")
        return all(test_result)


    def test_mux_connectivity(self, mux_id=None):
        self.test_logger.info(
            f"\n### Start MUX connectivity test  ###")

        if mux_id is None:
            mux_ids = [k for k in self._hw_nc.mux_boards.keys()]
            self.test_logger.info("Testing all MUX boards in MUX config.")

        if isinstance(mux_id, str):
            mux_ids = [mux_id]
        else:
            mux_ids = mux_id

        test_result = [False] * len(mux_ids)
        for i, mux_id in enumerate(mux_ids):
            mux = self._hw_nc.mux_boards[mux_id]
            self.test_logger.info(
                f"\n### Connectivity test initiated for {mux_id} with version {mux.model} ###")
            for i in range(len(mux._mcp)):
                try:
                    mux.reset_one(which=i)
                    self.test_logger.info(
                        f"Connection established with MCP {i} on {mux_id}.")
                except:
                    self.test_logger.info(
                        f"Connection NOT established with MCP {i} on {mux_id}.")
        return all(test_result)

    def test_mux_connection(self, mux_id=None):
        self.test_logger.info(
            f"\n### Start MUX connection test ###")

        if mux_id is None:
            mux_ids = [k for k in self._hw_nc.mux_boards.keys()]
            self.test_logger.info("Testing all MUX boards in MUX config.")

        if isinstance(mux_id, str):
            mux_ids = [mux_id]
        else:
            mux_ids = mux_id

        test_result = [False] * len(mux_ids)
        for i, mux_id in enumerate(mux_ids):
            self.test_logger.info(
                f"\n### Connection test initiated for {mux_id} with version {mux.model} ###")
            accessibility_results, connectivity_results = False, False
            accessibility_results = self.test_mux_accessibility(mux_id=mux_id)
            if accessibility_results:
                self.test_logger.info(
                    f"Accessibility test successful. Will check if device respond...")
                connectivity_results = self.test_mux_connectivity(mux_id=mux_id)
                if connectivity_results:
                    self.test_logger.info(
                        f"\nMUX connection test successful for {mux_id} with version {mux.model}.")
                    test_result[i] = True

        return all(test_result)


    def test_pwr_connection(self):
        if self._hw_nc.tx.pwr.voltage_adjustable:
            try:
                pass
            except:
                traceback.print_exc()
        else:
            self.test_logger.info('Pwr cannot be tested with this system configuration.')

    def test_vmn_hardware_offset(self):
        test_result = False
        quad = [0, 0]
        roles = ['M', 'N']
        tx_volt = 0.
        injection_duration = .5
        duty_cycle = .5 # or 0
        nb_stack = 2
        delay = injection_duration * 2/3
        if self.switch_mux_on(quad,roles):
            self._hw.vab_square_wave(tx_volt, cycle_duration=injection_duration * 2 / duty_cycle, cycles=nb_stack,
                                     duty_cycle=duty_cycle)
        Vmn = self._hw.last_vmn(delay=delay)
        Vmn_std = self._hw.last_vmn_dev(delay=delay)

        Vmn_deviation_from_offset = abs(1 - Vmn / self._hw.rx._vmn_hardware_offset) *100

        self.test_logger.info(f"Test Vmn hardware offset: Vmn offset deviation from config = {Vmn_deviation_from_offset: %.3f} %")
        if Vmn_deviation_from_offset <= 10.:
            test_result = True

        return test_result


    def test_r_shunt(self):
        if self._hw.tx.pwr.voltage_adjustable:
            test_result = False
            quad = [0, 0]
            roles = ['A','B']
            tx_volt = 5.
            injection_duration = .5
            duty_cycle = .5  # or 0
            nb_stack = 2
            delay = injection_duration * 2 / 3
            self._hw.switch_mux(quad, roles,status='on')
            self._hw._vab_pulse(duration=injection_duration, vab=tx_volt)
            iab = self._hw.readings[-1, 3]
            vab = self._hw.tx.pwr.voltage
            iab_dps = self._hw.tx.pwr.current
            print(iab, iab_dps)
            self.switch_mux_off(quad)

            Vmn = self._hw.last_vmn(delay=delay)
            Vmn_std = self._hw.last_vmn_dev(delay=delay)

            Iab_deviation = abs(1 - iab /iab_dps) * 100

            self.test_logger.info(
                f"Test r_shunt: R shunt deviation from config = {iab_deviation: %.3f} %")
            if iab_deviation <= 10.:
                test_result = True
            else:
                pass
        else:
            self.exec_logger.info('R shunt cannot be tested with this system configuration.')

    def test_mqtt_broker(self):
        pass

    def test_mux(self):
        self._hw.test_mux()
