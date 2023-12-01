import importlib
import time
import unittest
import logging
import mqtt
import traceback
from ohmpi.config import HARDWARE_CONFIG
from ohmpi.ohmpi import OhmPi
from ohmpi.hardware_system import OhmPiHardware
from ohmpi.logging_setup import setup_loggers


def test_i2c_devices_on_bus(i2c_addr, bus):
    i2C_addresses_on_bus = [hex(k) for k in bus.scan()]
    if i2c_addr in i2C_addresses_on_bus:
        return True
    else:
        return False


class OhmPiTests(unittest.TestCase):
    """
    OhmPiTests class .
    """
    def __init__(self):
        # set loggers
        self.exec_logger, _, self.data_logger, _, self.soh_logger, _, _, msg = setup_loggers(mqtt=mqtt)
        print(msg)

        # specify loggers when instancing the hardware
        self._hw = OhmPiHardware(**{'exec_logger': self.exec_logger, 'data_logger': self.data_logger,
                                    'soh_logger': self.soh_logger})
        self.exec_logger.info('Hardware configured...')
        self.exec_logger.info('OhmPi tests ready to start...')

    def test_connections(self):

    def test_tx_connections(self):
        i2c_addresses = self._hw.rx.connection

    def test_rx(self):
        pass

    def test_pwr(self):
        pass

    def test_mux(self):
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