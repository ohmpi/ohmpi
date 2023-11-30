import importlib
import time
import unittest
import logging
import datetime
import numpy as np
import traceback
from ohmpi.hardware_system import OhmPiHardware
from ohmpi.logging_setup import setup_loggers
from ohmpi.config import HARDWARE_CONFIG

for k, v in HARDWARE_CONFIG.items():
    if k == 'mux':
        HARDWARE_CONFIG[k]['default'].update({'connect': False})
    else:
        HARDWARE_CONFIG[k].update({'connect': False})

def test_i2c_devices_on_bus(i2c_addr, bus):
    i2c_addresses_on_bus = bus.scan()
    print(i2c_addresses_on_bus)
    if i2c_addr in i2c_addresses_on_bus:
        return True
    else:
        return False


class OhmPiTests(unittest.TestCase):
    """
    OhmPiTests class .
    """
    def __init__(self, settings=None, sequence=None, mqtt=True, config=None):
        # set loggers
        self.exec_logger, _, self.data_logger, _, self.soh_logger, _, _, msg = setup_loggers(mqtt=mqtt)
        print(msg)

        # specify loggers when instancing the hardware
        self._hw = OhmPiHardware(**{'exec_logger': self.exec_logger, 'data_logger': self.data_logger,
                                    'soh_logger': self.soh_logger}, hardware_config=HARDWARE_CONFIG)
        self.exec_logger.info('Hardware configured...')
        self.exec_logger.info('OhmPi tests ready to start...')

    def test_connections(self):
        pass

    def test_tx_connections(self, devices=['mcp','ads']):
        for device in devices:
            if f'{device}_address' in self._hw.tx.specs:
                if test_i2c_devices_on_bus(self._hw.tx.specs[f'{device}_address'], self._hw.tx.connection):
                    print(f"TX connections: MCP device with address {hex(self._hw.tx.specs[f'{device}_address'])} accessible on I2C bus.")
            else:
                self.fail()

    def test_rx_connections(self, devices=['mcp','ads']):
        for device in devices:
            if f'{device}_address' in self._hw.rx.specs:
                if test_i2c_devices_on_bus(self._hw.rx.specs[f'{device}_address'], self._hw.rx.connection):
                    print(f"RX connections: MCP device with address {hex(self._hw.tx.specs[f'{device}_address'])} accessible on I2C bus.")
            else:
                self.fail()

    def test_mux_connections(self, devices=['mcp', 'mux_tca']):
        for mux_id, mux in self._hw.mux_boards.items():
            if mux.model == 'mux_2024_0_X':
                print(mux.model)
                for mcp_address in mux._mcp_addresses:
                    print(mcp_address)
                    if mcp_address is not None:
                        if test_i2c_devices_on_bus(mcp_address, mux.connection):
                            print(
                                f"MUX connections: {mux_id} with address {hex(mcp_address)} accessible on I2C bus.")
                        else:
                            self.fail() #: {mux_id} with address {hex(mcp_address)} NOT accessible on I2C bus.")
            elif  mux.model == 'mux_2023_0_X':
                if f'mux_tca_address' in mux.specs:
                    if test_i2c_devices_on_bus(mux.specs['mux_tca_address'], mux.connection):
                        print(f"MUX connections: {mux_id} with address {hex(mux.specs['mux_tca_address'])} accessible on I2C bus.")

    def test_pwr(self):
        pass



    def test_i2c_mux_boards(self):
        try:
            pass
        except:
            traceback.print_exc()
            self.fail()

    def test_i2c_measurement_board(self):
        try:
            pass
        except:
            traceback.print_exc()
            self.fail()

    def test_pwr_connection(self):
        if self._hw.tx.pwr.voltage_adjustable:
            try:
                pass
            except:
                traceback.print_exc()
                self.fail()
        else:
            self.exec_logger.info('Pwr cannot be tested with this system configuration.')

    def test_vmn_hardware_offset(self):
        pass

    def test_r_shunt(self):
        if self._hw.tx.pwr.voltage_adjustable:
            pass
        else:
            self.exec_logger.info('r_shunt cannot be tested with this system configuration.')

    def test_mqtt_broker(self):
        pass

    def test_mux(self):
        self._hw.test_mux()


def main(self):
    import sys

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(OhmPiTests)
    runner = unittest.TextTestRunner(verbosity=4)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)


if __name__ == '__main__':
    main()