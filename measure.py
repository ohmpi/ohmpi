import importlib
from time import gmtime
import sys
import logging
from config import OHMPI_CONFIG
controller_module = importlib.import_module(f'{OHMPI_CONFIG["hardware"]["controller"]["model"]}')
tx_module = importlib.import_module(f'{OHMPI_CONFIG["hardware"]["tx"]["model"]}')
rx_module = importlib.import_module(f'{OHMPI_CONFIG["hardware"]["rx"]["model"]}')
mux_module = importlib.import_module(f'{OHMPI_CONFIG["hardware"]["mux"]["model"]}')
TX_CONFIG = tx_module.TX_CONFIG
RX_CONFIG = rx_module.RX_CONFIG

class OhmPiHardware():
    def __init__(self, **kwargs):
        self.tx = kwargs.pop('controller', tx_module.Controller())
        self.rx = kwargs.pop('tx', tx_module.Rx())
        self.tx = kwargs.pop('rx', tx_module.Tx())
        self.rx = kwargs.pop('mux', tx_module.Mux())
        self.exec_logger = kwargs.pop('exec_logger', None)
        self.data_logger = kwargs.pop('exec_logger', None)
        self.soh_logger = kwargs.pop('soh_logger', None)
        if self.exec_logger is None:
            self.exec_logger = logging.getLogger('exec_logger')
            log_format = '%(asctime)-15s | exec | %(levelname)s: %(message)s'
            exec_formatter = logging.Formatter(log_format)
            exec_formatter.converter = gmtime
            exec_formatter.datefmt = '%Y-%m-%d %H:%M:%S UTC'
            exec_handler = logging.StreamHandler(sys.stdout)
            exec_handler.setFormatter(exec_formatter)
            self.exec_logger.addHandler(exec_handler)
            self.exec_logger.setLevel('debug')
        if self.data_logger is None:
            self.data_logger = logging.getLogger('data_logger')
            log_format = '%(asctime)-15s | data | %(levelname)s: %(message)s'
            data_formatter = logging.Formatter(log_format)
            data_formatter.converter = gmtime
            data_formatter.datefmt = '%Y-%m-%d %H:%M:%S UTC'
            data_handler = logging.StreamHandler(sys.stdout)
            data_handler.setFormatter(data_formatter)
            self.data_logger.addHandler(data_handler)
            self.data_logger.setLevel('debug')
        if self.soh_logger is None:
            self.soh_logger = logging.getLogger('soh_logger')
            log_format = '%(asctime)-15s | soh | %(levelname)s: %(message)s'
            soh_formatter = logging.Formatter(log_format)
            soh_formatter.converter = gmtime
            soh_formatter.datefmt = '%Y-%m-%d %H:%M:%S UTC'
            soh_handler = logging.StreamHandler(sys.stdout)
            soh_handler.setFormatter(soh_formatter)
            self.soh_logger.addHandler(soh_handler)
            self.soh_logger.setLevel('debug')

    def _compute_tx_volt(self, best_tx_injtime=0.1, strategy='vmax', tx_volt=5):
        """Estimates best Tx voltage based on different strategies.
        At first a half-cycle is made for a short duration with a fixed
        known voltage. This gives us Iab and Rab. We also measure Vmn.
        A constant c = vmn/iab is computed (only depends on geometric
        factor and ground resistivity, that doesn't change during a
        quadrupole). Then depending on the strategy, we compute which
        vab to inject to reach the minimum/maximum Iab current or
        min/max Vmn.
        This function also compute the polarity on Vmn (on which pin
        of the ADS1115 we need to measure Vmn to get the positive value).

        Parameters
        ----------
        best_tx_injtime : float, optional
            Time in milliseconds for the half-cycle used to compute Rab.
        strategy : str, optional
            Either:
            - vmax : compute Vab to reach a maximum Iab and Vmn
            - constant : apply given Vab
        tx_volt : float, optional
            Voltage to apply for guessing the best voltage. 5 V applied
            by default. If strategy "constant" is chosen, constant voltage
            to applied is "tx_volt".

        Returns
        -------
        vab : float
            Proposed Vab according to the given strategy.
        polarity : int
            Either 1 or -1 to know on which pin of the ADS the Vmn is measured.
        """


        self.tx.polarity = 1
        self.tx.turn_on()
        if strategy == 'constant':
            vab = tx_volt
            self.tx.voltage = vab
            self.tx.voltage_pulse(length=best_tx_injtime)
            # set gains automatically
            self.tx.adc_gain_auto()
            self.rx.adc_gain_auto()
            I = self.tx.current  # measure current
            vmn = self.rx.voltage

        elif strategy == 'vmax':
            """
            # implement different strategies
            I = 0
            vmn = 0
            count = 0
            while I < TX_CONFIG['current_max'] or abs(vmn) < RX_CONFIG['?']:  # TODO: hardware related - place in config

                if count > 0:
                    # print('o', volt)
                    volt = volt + 2
                # print('>', volt)
                count = count + 1
                if volt > 50:
                    break

                # set voltage for test
                if count == 1:
                    self.DPS.write_register(0x09, 1)  # DPS5005 on
                    time.sleep(best_tx_injtime)  # inject for given tx time
                self.DPS.write_register(0x0000, volt, 2)
                # autogain
                self.ads_current = ads.ADS1115(self.i2c, gain=2 / 3, data_rate=860, address=self.ads_current_address)
                self.ads_voltage = ads.ADS1115(self.i2c, gain=2 / 3, data_rate=860, address=self.ads_voltage_address)
                gain_current = self._gain_auto(AnalogIn(self.ads_current, ads.P0))
                gain_voltage0 = self._gain_auto(AnalogIn(self.ads_voltage, ads.P0))
                gain_voltage2 = self._gain_auto(AnalogIn(self.ads_voltage, ads.P2))
                gain_voltage = np.min([gain_voltage0, gain_voltage2])  # TODO: separate gain for P0 and P2
                self.ads_current = ads.ADS1115(self.i2c, gain=gain_current, data_rate=860, address=self.ads_current_address)
                self.ads_voltage = ads.ADS1115(self.i2c, gain=gain_voltage, data_rate=860, address=self.ads_voltage_address)
                # we measure the voltage on both A0 and A2 to guess the polarity
                for i in range(10):
                    I = AnalogIn(self.ads_current, ads.P0).voltage * 1000. / 50 / self.r_shunt  # noqa measure current
                    U0 = AnalogIn(self.ads_voltage, ads.P0).voltage * 1000.  # noqa measure voltage
                    U2 = AnalogIn(self.ads_voltage, ads.P2).voltage * 1000.  # noqa
                    time.sleep(best_tx_injtime)

                # check polarity
                polarity = 1  # by default, we guessed it right
                vmn = U0
                if U0 < 0:  # we guessed it wrong, let's use a correction factor
                    polarity = -1
                    vmn = U2

            n = 0
            while (
                    abs(vmn) > voltage_max or I > current_max) and volt > 0:  # If starting voltage is too high, need to lower it down
                # print('we are out of range! so decreasing volt')
                volt = volt - 2
                self.DPS.write_register(0x0000, volt, 2)
                # self.DPS.write_register(0x09, 1)  # DPS5005 on
                I = AnalogIn(self.ads_current, ads.P0).voltage * 1000. / 50 / self.r_shunt
                U0 = AnalogIn(self.ads_voltage, ads.P0).voltage * 1000.
                U2 = AnalogIn(self.ads_voltage, ads.P2).voltage * 1000.
                polarity = 1  # by default, we guessed it right
                vmn = U0
                if U0 < 0:  # we guessed it wrong, let's use a correction factor
                    polarity = -1
                    vmn = U2
                n += 1
                if n > 25:
                    break

            factor_I = (current_max) / I
            factor_vmn = voltage_max / vmn
            factor = factor_I
            if factor_I > factor_vmn:
                factor = factor_vmn
            # print('factor', factor_I, factor_vmn)
            vab = factor * volt * 0.9
            if vab > tx_max:
                vab = tx_max
            print(factor_I, factor_vmn, 'factor!!')"""
            pass

        elif strategy == 'vmin':
            """# implement different strategy
            I = 20
            vmn = 400
            count = 0
            while I > 10 or abs(vmn) > 300:  # TODO: hardware related - place in config
                if count > 0:
                    volt = volt - 2
                print(volt, count)
                count = count + 1
                if volt > 50:
                    break

                # set voltage for test
                self.DPS.write_register(0x0000, volt, 2)
                if count == 1:
                    self.DPS.write_register(0x09, 1)  # DPS5005 on
                time.sleep(best_tx_injtime)  # inject for given tx time

                # autogain
                self.ads_current = ads.ADS1115(self.i2c, gain=2 / 3, data_rate=860, address=self.ads_current_address)
                self.ads_voltage = ads.ADS1115(self.i2c, gain=2 / 3, data_rate=860, address=self.ads_voltage_address)
                gain_current = self._gain_auto(AnalogIn(self.ads_current, ads.P0))
                gain_voltage0 = self._gain_auto(AnalogIn(self.ads_voltage, ads.P0))
                gain_voltage2 = self._gain_auto(AnalogIn(self.ads_voltage, ads.P2))
                gain_voltage = np.min([gain_voltage0, gain_voltage2])  # TODO: separate gain for P0 and P2
                self.ads_current = ads.ADS1115(self.i2c, gain=gain_current, data_rate=860, address=self.ads_current_address)
                self.ads_voltage = ads.ADS1115(self.i2c, gain=gain_voltage, data_rate=860, address=self.ads_voltage_address)
                # we measure the voltage on both A0 and A2 to guess the polarity
                I = AnalogIn(self.ads_current, ads.P0).voltage * 1000. / 50 / self.r_shunt  # noqa measure current
                U0 = AnalogIn(self.ads_voltage, ads.P0).voltage * 1000.  # noqa measure voltage
                U2 = AnalogIn(self.ads_voltage, ads.P2).voltage * 1000.  # noqa

                # check polarity
                polarity = 1  # by default, we guessed it right
                vmn = U0
                if U0 < 0:  # we guessed it wrong, let's use a correction factor
                    polarity = -1
                    vmn = U2

            n = 0
            while (
                    abs(vmn) < voltage_min or I < current_min) and volt > 0:  # If starting voltage is too high, need to lower it down
                # print('we are out of range! so increasing volt')
                volt = volt + 2
                print(volt)
                self.DPS.write_register(0x0000, volt, 2)
                # self.DPS.write_register(0x09, 1)  # DPS5005 on
                # time.sleep(best_tx_injtime)
                I = AnalogIn(self.ads_current, ads.P0).voltage * 1000. / 50 / self.r_shunt
                U0 = AnalogIn(self.ads_voltage, ads.P0).voltage * 1000.
                U2 = AnalogIn(self.ads_voltage, ads.P2).voltage * 1000.
                polarity = 1  # by default, we guessed it right
                vmn = U0
                if U0 < 0:  # we guessed it wrong, let's use a correction factor
                    polarity = -1
                    vmn = U2
                n += 1
                if n > 25:
                    break

            vab = volt"""
            pass

        self.tx.turn_off()
        self.tx.polarity = 0
        rab = (vab * 1000.) / I  # noqa

        self.exec_logger.debug(f'RAB = {rab:.2f} Ohms')

        return vab, rab