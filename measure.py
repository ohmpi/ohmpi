import importlib
import time

import numpy as np
from OhmPi.logging_setup import create_stdout_logger
from OhmPi.config import HARDWARE_CONFIG
from threading import Thread, Event

controller_module = importlib.import_module(f'OhmPi.hardware.{HARDWARE_CONFIG["controller"]["model"]}')
tx_module = importlib.import_module(f'OhmPi.hardware.{HARDWARE_CONFIG["tx"]["model"]}')
rx_module = importlib.import_module(f'OhmPi.hardware.{HARDWARE_CONFIG["rx"]["model"]}')
mux_module = importlib.import_module(f'OhmPi.hardware.{HARDWARE_CONFIG["mux"]["model"]}')
TX_CONFIG = tx_module.TX_CONFIG
RX_CONFIG = rx_module.RX_CONFIG
MUX_CONFIG = mux_module.MUX_CONFIG

current_max = np.min([TX_CONFIG['current_max'], MUX_CONFIG['current_max']])
voltage_max = np.min([TX_CONFIG['voltage_max'], MUX_CONFIG['voltage_max']])
voltage_min = RX_CONFIG['voltage_min']

class OhmPiHardware:
    def __init__(self, **kwargs):
        self.exec_logger = kwargs.pop('exec_logger', None)
        if self.exec_logger is None:
            self.exec_logger = create_stdout_logger('exec')
        self.data_logger = kwargs.pop('exec_logger', None)
        if self.data_logger is None:
            self.data_logger = create_stdout_logger('data')
        self.soh_logger = kwargs.pop('soh_logger', None)
        if self.soh_logger is None:
            self.soh_logger = create_stdout_logger('soh')
        self.tx_sync = Event()
        self.controller = kwargs.pop('controller',
                                     controller_module.Controller(exec_logger=self.exec_logger,
                                                                   data_logger=self.data_logger,
                                                                   soh_logger= self.soh_logger))
        self.rx = kwargs.pop('rx', rx_module.Rx(exec_logger=self.exec_logger,
                                                 data_logger=self.data_logger,
                                                 soh_logger=self.soh_logger))
        self.tx = kwargs.pop('tx', tx_module.Tx(exec_logger=self.exec_logger,
                                                 data_logger=self.data_logger,
                                                 soh_logger=self.soh_logger))
        self.mux = kwargs.pop('mux', mux_module.Mux(exec_logger=self.exec_logger,
                                                    data_logger=self.data_logger,
                                                    soh_logger=self.soh_logger))


    def _vab_pulse(self, vab, length, sampling_rate=10., polarity=None):
        """ Gets VMN and IAB from a single voltage pulse
        """
        def inject(duration):
            self.tx_sync.set()
            self.tx.voltage_pulse(length=duration)
            self.tx_sync.clear()

        def read_values(sampling_rate):
            _readings = []
            self.tx_sync.wait()
            start_time = time.gmtime()
            while self.tx_sync.is_set():
                cur_time=start_time
                _readings.append([time.gmtime() - start_time, self.tx.current, self.rx.voltage])
                time.sleep(cur_time+sampling_rate/1000.-time.gmtime())
            return np.array(_readings)

        if sampling_rate is None:
            sampling_rate = RX_CONFIG['sampling_rate']
        if polarity is not None and polarity != self.tx.polarity:
            self.tx.polarity = polarity
        self.tx.voltage = vab
        injection = Thread(target=inject, kwargs={'length':length})
        readings = Thread(target=read_values)
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
        vab = np.min([np.abs(tx_volt), vab_max])
        self.tx.polarity = 1
        self.tx.turn_on()
        vmn, iab = self._vab_pulse(vab=vab, length=best_tx_injtime)
        # if np.abs(vmn) is too small (smaller than voltage_min), strategy is not constant and vab < vab_max ,
        # then we could call _compute_tx_volt with a tx_volt increased to np.min([vab_max, tx_volt*2.]) for example
        if strategy == 'vmax':
            # implement different strategies
            if vab < vab_max and iab < current_max :
                vab = vab * np.min([0.9 * vab_max / vab, 0.9 * current_max / iab])  # TODO: check if setting at 90% of max as a safety margin is OK
            self.tx.exec_logger.debug(f'vmax strategy: setting VAB to {vab} V.')
        elif strategy == 'vmin':
            if vab <= vab_max and iab < current_max:
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