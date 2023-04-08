import importlib
from time import gmtime
import numpy as np
import sys
import logging
from config import OHMPI_CONFIG
controller_module = importlib.import_module(f'{OHMPI_CONFIG["hardware"]["controller"]["model"]}')
tx_module = importlib.import_module(f'{OHMPI_CONFIG["hardware"]["tx"]["model"]}')
rx_module = importlib.import_module(f'{OHMPI_CONFIG["hardware"]["rx"]["model"]}')
mux_module = importlib.import_module(f'{OHMPI_CONFIG["hardware"]["mux"]["model"]}')
TX_CONFIG = tx_module.TX_CONFIG
RX_CONFIG = rx_module.RX_CONFIG
MUX_CONFIG = mux_module.MUX_CONFIG

current_max = np.min([TX_CONFIG['current_max'], MUX_CONFIG['current_max']])
voltage_max = np.min([TX_CONFIG['voltage_max'], MUX_CONFIG['voltage_max']])
voltage_min = RX_CONFIG['voltage_min']

class OhmPiHardware:
    def __init__(self, **kwargs):
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
        self.controller = kwargs.pop('controller',
                                     controller_module.Controller({'exec_logger' : self.exec_logger,
                                                                   'data_logger': self.data_logger,
                                                                   'soh_logger': self.soh_logger}))
        self.rx = kwargs.pop('tx', tx_module.Rx({'exec_logger' : self.exec_logger,
                                                 'data_logger': self.data_logger,
                                                 'soh_logger': self.soh_logger}))
        self.tx = kwargs.pop('rx', tx_module.Tx({'exec_logger' : self.exec_logger,
                                                 'data_logger': self.data_logger,
                                                 'soh_logger': self.soh_logger}))
        self.mux = kwargs.pop('mux', mux_module.Mux({'exec_logger' : self.exec_logger,
                                                     'data_logger': self.data_logger,
                                                     'soh_logger': self.soh_logger}))
    def _vab_pulse(self, vab, length, polarity=None):
        """ Gets VMN and IAB from a single voltage pulse
        """
        if polarity is not None and polarity != self.tx.polarity:
            self.tx.polarity = polarity
        self.tx.voltage = vab
        self.tx.voltage_pulse(length=length)
        # set gains automatically
        self.tx.adc_gain_auto()
        self.rx.adc_gain_auto()
        iab = self.tx.current  # measure current
        vmn = self.rx.voltage
        return vmn, iab

    def _compute_tx_volt(self, best_tx_injtime=0.1, strategy='vmax', tx_volt=5,
                         vab_max=voltage_max, vmn_min=voltage_min):
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
            - vmax : compute Vab to reach a maximum Iab without exceeding vab_max
            - vmin : compute Vab to reach at least vmn_min
            - constant : apply given Vab
        tx_volt : float, optional
            Voltage to apply for guessing the best voltage. 5 V applied
            by default. If strategy "constant" is chosen, constant voltage
            to applied is "tx_volt".
        vab_max : float, optional
            Maximum injection voltage to apply to tx (used by all strategies)
        vmn_min : float, optional
            Minimum voltage target for rx (used by vmin strategy)

        Returns
        -------
        vab : float
            Proposed Vab according to the given strategy.
        polarity:
            Polarity of VMN relative to polarity of VAB
        rab : float
            Resistance between injection electrodes
        """

        vab_max = np.abs(vab_max)
        vmn_min = np.abs(vmn_min)
        vab = np.min(np.abs(tx_volt), vab_max)
        self.tx.polarity = 1
        self.tx.turn_on()
        vmn, iab = self._vab_pulse(vab=vab, length=best_tx_injtime)
        if strategy == 'vmax':
            # implement different strategies
            if vab < vab_max and iab < current_max :
                vab = vab * np.min([0.9 * vab_max / vab, 0.9 * current_max / iab])  # TODO: check if setting at 90% of max as a safety margin is OK
            self.tx.exec_logger.debug(f'vmax strategy: setting VAB to {vab} V.')
        elif strategy == 'vmin':
            if vab < vab_max and iab < current_max:
                vab = vab * np.min([0.9 * vab_max / vab, vmn_min / np.abs(vmn), 0.9 * current_max / iab])  # TODO: check if setting at 90% of max as a safety margin is OK
        elif strategy != 'constant':
            self.tx.exec_logger.warning(f'Unknown strategy {strategy} for setting VAB! Using {vab} V')
        else:
            self.tx.exec_logger.debug(f'Constant strategy for setting VAB, using {vab} V')
        self.tx.turn_off()
        self.tx.polarity = 0
        rab = (np.abs(vab) * 1000.) / iab
        self.exec_logger.debug(f'RAB = {rab:.2f} Ohms')
        if vmn < 0:
            polarity = -1  # TODO: check if we really need to return polarity
        else:
            polarity = 1
        return vab, polarity, rab