import importlib
import datetime
import time
import numpy as np
try:
    import matplotlib.pyplot as plt
except Exception:
    pass
from ohmpi.hardware_components.abstract_hardware_components import CtlAbstract
from ohmpi.logging_setup import create_stdout_logger
from ohmpi.utils import update_dict
from ohmpi.config import HARDWARE_CONFIG
from threading import Thread, Event, Barrier, BrokenBarrierError
import warnings

# plt.switch_backend('agg')  # for thread safe operations...

# Define the default controller, a distinct controller could be defined for each tx, rx or mux board
# when using a distinct controller, the specific controller definition must be included in the component configuration
ctl_module = importlib.import_module(f'ohmpi.hardware_components.{HARDWARE_CONFIG["ctl"]["model"]}')
pwr_module = importlib.import_module(f'ohmpi.hardware_components.{HARDWARE_CONFIG["pwr"]["model"]}')
tx_module = importlib.import_module(f'ohmpi.hardware_components.{HARDWARE_CONFIG["tx"]["model"]}')
rx_module = importlib.import_module(f'ohmpi.hardware_components.{HARDWARE_CONFIG["rx"]["model"]}')

MUX_DEFAULT = HARDWARE_CONFIG['mux']['default']
MUX_CONFIG = HARDWARE_CONFIG['mux']['boards']
for k, v in MUX_CONFIG.items():
    MUX_CONFIG[k].update({'id': k})
    for k2, v2 in MUX_DEFAULT.items():
        MUX_CONFIG[k].update({k2: MUX_CONFIG[k].pop(k2, v2)})

TX_CONFIG = HARDWARE_CONFIG['tx']
for k, v in tx_module.SPECS['tx'].items():
    try:
        TX_CONFIG.update({k: TX_CONFIG.pop(k, v['default'])})
    except Exception as e:
        print(f'Cannot set value {v} in TX_CONFIG[{k}]:\n{e}')

RX_CONFIG = HARDWARE_CONFIG['rx']
for k, v in rx_module.SPECS['rx'].items():
    try:
        RX_CONFIG.update({k: RX_CONFIG.pop(k, v['default'])})
    except Exception as e:
        print(f'Cannot set value {v} in RX_CONFIG[{k}]:\n{e}')

current_max = np.min([TX_CONFIG['current_max'],  HARDWARE_CONFIG['pwr'].pop('current_max', np.inf),
                      np.min(np.hstack((np.inf, [MUX_CONFIG[i].pop('current_max', np.inf) for i in MUX_CONFIG.keys()])))])
voltage_max = np.min([TX_CONFIG['voltage_max'],
                      np.min(np.hstack((np.inf, [MUX_CONFIG[i].pop('voltage_max', np.inf) for i in MUX_CONFIG.keys()])))])
voltage_min = RX_CONFIG['voltage_min']
# TODO: should replace voltage_max and voltage_min by vab_max and vmn_min...


def elapsed_seconds(start_time):
    lap = datetime.datetime.utcnow() - start_time
    return lap.total_seconds()


class OhmPiHardware:
    def __init__(self, **kwargs):
        # OhmPiHardware initialization
        self.exec_logger = kwargs.pop('exec_logger', create_stdout_logger('exec_hw'))
        self.exec_logger.event(f'OhmPiHardware\tinit\tbegin\t{datetime.datetime.utcnow()}')
        self.data_logger = kwargs.pop('exec_logger', create_stdout_logger('data_hw'))
        self.soh_logger = kwargs.pop('soh_logger', create_stdout_logger('soh_hw'))
        self.tx_sync = Event()

        # Main Controller initialization
        HARDWARE_CONFIG['ctl'].pop('model')
        HARDWARE_CONFIG['ctl'].update({'exec_logger': self.exec_logger, 'data_logger': self.data_logger,
                                       'soh_logger': self.soh_logger})
        self.ctl = kwargs.pop('ctl', ctl_module.Ctl(**HARDWARE_CONFIG['ctl']))
        # use controller as defined in kwargs if present otherwise use controller as defined in config.
        if isinstance(self.ctl, dict):
            ctl_mod = self.ctl.pop('model', self.ctl)
            if isinstance(ctl_mod, str):
                ctl_mod = importlib.import_module(f'ohmpi.hardware_components.{ctl_mod}')
            self.ctl = ctl_mod.Ctl(**self.ctl)

        # Initialize RX
        HARDWARE_CONFIG['rx'].pop('model')
        HARDWARE_CONFIG['rx'].update(**HARDWARE_CONFIG['rx'])  # TODO: delete me ?
        HARDWARE_CONFIG['rx'].update({'ctl': HARDWARE_CONFIG['rx'].pop('ctl', self.ctl)})
        if isinstance(HARDWARE_CONFIG['rx']['ctl'], dict):
            ctl_mod = HARDWARE_CONFIG['rx']['ctl'].pop('model', self.ctl)
            if isinstance(ctl_mod, str):
                ctl_mod = importlib.import_module(f'ohmpi.hardware_components.{ctl_mod}')
            HARDWARE_CONFIG['rx']['ctl'] = ctl_mod.Ctl(**HARDWARE_CONFIG['rx']['ctl'])
        HARDWARE_CONFIG['rx'].update({'connection':
                                          HARDWARE_CONFIG['rx'].pop('connection',
                                                                    HARDWARE_CONFIG['rx']['ctl'].interfaces[
                                                                                  HARDWARE_CONFIG['rx'].pop(
                                                                                      'interface_name', 'i2c')])})
        HARDWARE_CONFIG['rx'].update({'exec_logger': self.exec_logger, 'data_logger': self.data_logger,
                                       'soh_logger': self.soh_logger})
        HARDWARE_CONFIG['tx'].pop('ctl', None)
        self.rx = kwargs.pop('rx', rx_module.Rx(**HARDWARE_CONFIG['rx']))

        # Initialize power source
        HARDWARE_CONFIG['pwr'].pop('model')
        HARDWARE_CONFIG['pwr'].update(**HARDWARE_CONFIG['pwr'])  # NOTE: Explain why this is needed or delete me
        HARDWARE_CONFIG['pwr'].update({'ctl': HARDWARE_CONFIG['pwr'].pop('ctl', self.ctl)})
        HARDWARE_CONFIG['pwr'].update({'current_max': current_max})
        if isinstance(HARDWARE_CONFIG['pwr']['ctl'], dict):
            ctl_mod = HARDWARE_CONFIG['pwr']['ctl'].pop('model', self.ctl)
            if isinstance(ctl_mod, str):
                ctl_mod = importlib.import_module(f'ohmpi.hardware_components.{ctl_mod}')
            HARDWARE_CONFIG['pwr']['ctl'] = ctl_mod.Ctl(**HARDWARE_CONFIG['pwr']['ctl'])
        #if 'interface_name' in HARDWARE_CONFIG['pwr']:
        HARDWARE_CONFIG['pwr'].update({
            'connection': HARDWARE_CONFIG['pwr'].pop(
                'connection', HARDWARE_CONFIG['pwr']['ctl'].interfaces[
                    HARDWARE_CONFIG['pwr'].pop('interface_name', None)])})

        HARDWARE_CONFIG['pwr'].update({'exec_logger': self.exec_logger, 'data_logger': self.data_logger,
                                      'soh_logger': self.soh_logger})
        self.pwr = kwargs.pop('pwr', pwr_module.Pwr(**HARDWARE_CONFIG['pwr']))

        # Initialize TX
        HARDWARE_CONFIG['tx'].pop('model')
        HARDWARE_CONFIG['tx'].update(**HARDWARE_CONFIG['tx'])
        HARDWARE_CONFIG['tx'].update({'tx_sync': self.tx_sync})
        HARDWARE_CONFIG['tx'].update({'ctl': HARDWARE_CONFIG['tx'].pop('ctl', self.ctl)})
        if isinstance(HARDWARE_CONFIG['tx']['ctl'], dict):
            ctl_mod = HARDWARE_CONFIG['tx']['ctl'].pop('model', self.ctl)
            if isinstance(ctl_mod, str):
                ctl_mod = importlib.import_module(f'ohmpi.hardware_components.{ctl_mod}')
            HARDWARE_CONFIG['tx']['ctl'] = ctl_mod.Ctl(**HARDWARE_CONFIG['tx']['ctl'])
        HARDWARE_CONFIG['tx'].update({'connection': HARDWARE_CONFIG['tx'].pop('connection',
                                                                              HARDWARE_CONFIG['tx']['ctl'].interfaces[
                                                                                  HARDWARE_CONFIG['tx'].pop(
                                                                                      'interface_name', 'i2c')])})
        HARDWARE_CONFIG['tx'].pop('ctl', None)
        HARDWARE_CONFIG['tx'].update({'exec_logger': self.exec_logger, 'data_logger': self.data_logger,
                                      'soh_logger': self.soh_logger})
        self.tx = kwargs.pop('tx', tx_module.Tx(**HARDWARE_CONFIG['tx']))
        if isinstance(self.tx, dict):
            self.tx = tx_module.Tx(**self.tx)
        self.tx.pwr = self.pwr
        self.tx.pwr._current_max = current_max

        # Initialize Muxes
        self._cabling = kwargs.pop('cabling', {})
        self.mux_boards = {}
        for mux_id, mux_config in MUX_CONFIG.items():
            mux_config.update({'exec_logger': self.exec_logger, 'data_logger': self.data_logger,
                               'soh_logger': self.soh_logger})
            mux_config.update(**MUX_CONFIG[mux_id])
            mux_config.update({'ctl': mux_config.pop('ctl', self.ctl)})

            mux_module = importlib.import_module(f'ohmpi.hardware_components.{mux_config["model"]}')
            if isinstance(mux_config['ctl'], dict):
                mux_ctl_module = importlib.import_module(f'ohmpi.hardware_components.{mux_config["ctl"]["model"]}')
                mux_config['ctl'] = mux_ctl_module.Ctl(**mux_config['ctl'])  # (**self.ctl)
            assert issubclass(type(mux_config['ctl']), CtlAbstract)
            mux_config.update({'connection': mux_config.pop('connection', mux_config['ctl'].interfaces[mux_config.pop('interface_name', 'i2c')])})
            mux_config['id'] = mux_id

            self.mux_boards[mux_id] = mux_module.Mux(**mux_config)

        self.mux_barrier = Barrier(len(self.mux_boards) + 1)
        self._cabling = {}
        for mux_id, mux in self.mux_boards.items():
            mux.barrier = self.mux_barrier
            for k, v in mux.cabling.items():
                update_dict(self._cabling, {k: (mux_id, k[0])})   #TODO: in theory k[0] is not needed in values

        # Complete OhmPiHardware initialization
        self.readings = np.array([])  # time series of acquired data
        self._start_time = None  # time of the beginning of a readings acquisition
        self._pulse = 0  # pulse number
        self.exec_logger.event(f'OhmPiHardware\tinit\tend\t{datetime.datetime.utcnow()}')
        self._pwr_state = 'off'

    @property
    def pwr_state(self):
        return self._pwr_state

    @pwr_state.setter
    def pwr_state(self, state):
        if state == 'on':
            self.tx.pwr_state = 'on'
            self._pwr_state = 'on'
        elif state == 'off':
            self.tx.pwr_state = 'off'
            self._pwr_state = 'off'

    def _clear_values(self):
        self.readings = np.array([])
        self._start_time = None
        self._pulse = 0

    def _gain_auto(self, polarities=(1, -1), vab=5., switch_pwr_off=False):  # TODO: improve _gain_auto
        self.exec_logger.event(f'OhmPiHardware\ttx_rx_gain_auto\tbegin\t{datetime.datetime.utcnow()}')
        current, voltage = 0., 0.
        if self.tx.pwr.voltage_adjustable:
            self.tx.voltage = vab
        if self.tx.pwr.pwr_state == 'off':
            self.tx.pwr.pwr_state = 'on'
            switch_pwr_off = True
        tx_gains = []
        rx_gains = []
        for pol in polarities:
            # self.tx.polarity = pol
            # set gains automatically
            injection = Thread(target=self._inject, kwargs={'injection_duration': 0.2, 'polarity': pol})
            # readings = Thread(target=self._read_values)
            get_tx_gain = Thread(target=self.tx.gain_auto)
            get_rx_gain = Thread(target=self.rx.gain_auto)
            injection.start()
            self.tx_sync.wait()
            get_tx_gain.start()  # TODO: add a barrier to synchronize?
            get_rx_gain.start()
            get_tx_gain.join()
            get_rx_gain.join()
            injection.join()
            tx_gains.append(self.tx.gain)
            rx_gains.append(self.rx.gain)

            # v = self.readings[:, 2] != 0
            # current = max(current, np.mean(self.readings[v, 3]))
            # voltage = max(voltage, np.abs(np.mean(self.readings[v, 2] * self.readings[v, 4])))
            self.tx.polarity = 0
        self.tx.gain = min(tx_gains)
        self.rx.gain = min(rx_gains)
        # self.rx.gain_auto(voltage)
        if switch_pwr_off:
            self.tx.pwr.pwr_state = 'off'
        self.exec_logger.event(f'OhmPiHardware\ttx_rx_gain_auto\tend\t{datetime.datetime.utcnow()}')

    def _inject(self, polarity=1, injection_duration=None):  # TODO: deal with voltage or current pulse
        self.exec_logger.event(f'OhmPiHardware\tinject\tbegin\t{datetime.datetime.utcnow()}')
        self.tx.voltage_pulse(length=injection_duration, polarity=polarity)
        self.exec_logger.event(f'OhmPiHardware\tinject\tend\t{datetime.datetime.utcnow()}')

    def _set_mux_barrier(self):
        self.mux_barrier = Barrier(len(self.mux_boards) + 1)
        for mux in self.mux_boards:
            mux.barrier = self.mux_barrier

    @property
    def pulses(self):  # TODO: is this obsolete? I don't think so...
        pulses = {}
        for i in np.unique(self.readings[:, 1]):
            r = self.readings[self.readings[:, 1] == i, :]
            assert np.all(np.isclose(r[:, 2], r[0, 2]))  # Polarity cannot change within a pulse
            # TODO: check how to generalize in case of multi-channel RX
            pulses.update({i: {'polarity': int(r[0, 2]), 'iab': r[:, 3], 'vmn': r[:, 4]}})
        return pulses

    def _read_values(self, sampling_rate=None, append=False):  # noqa
        """
        Reads vmn and iab values on ADS1115 and generates full waveform dataset consisting of
        [time, pulse nr, polarity, vmn, iab]
        Parameters
        ----------
        sampling_rate: float,None , optional
        append: bool Default: False
        """
        self.exec_logger.event(f'OhmPiHardware\tread_values\tbegin\t{datetime.datetime.utcnow()}')
        if not append:
            self._clear_values()
            _readings = []
        else:
            _readings = self.readings.tolist()
        if sampling_rate is None:
            sampling_rate = self.rx.sampling_rate
        sample = 0
        lap = datetime.datetime.utcnow()  # just in case tx_sync is not set immediately after passing wait
        self.tx_sync.wait()  #
        if not append or self._start_time is None:
            self._start_time = datetime.datetime.utcnow()
            # TODO: Check if replacing the following two options by a reset_buffer method of TX would be OK
            time.sleep(np.max([self.rx.latency, self.tx.latency])) # if continuous mode
            # _ = self.rx.voltage # if not continuous mode

        while self.tx_sync.is_set():
            lap = datetime.datetime.utcnow()
            r = [elapsed_seconds(self._start_time), self._pulse, self.tx.polarity, self.tx.current, self.rx.voltage]
            if self.tx_sync.is_set():
                sample += 1
                _readings.append(r)
                sleep_time = self._start_time + datetime.timedelta(seconds=sample / sampling_rate) - lap
                if sleep_time.total_seconds() < 0.:
                    # TODO: count how many samples were skipped to make a stat that could be used to qualify pulses
                    sample += int(sampling_rate * np.abs(sleep_time.total_seconds())) + 1
                    sleep_time = self._start_time + datetime.timedelta(seconds=sample / sampling_rate) - lap
                time.sleep(np.max([0., sleep_time.total_seconds()]))

        self.exec_logger.debug(f'pulse {self._pulse}: elapsed time {(lap-self._start_time).total_seconds()} s')
        self.exec_logger.debug(f'pulse {self._pulse}: total samples {len(_readings)}')
        self.readings = np.array(_readings)
        self._pulse += 1
        self.exec_logger.event(f'OhmPiHardware\tread_values\tend\t{datetime.datetime.utcnow()}')

    def last_resistance(self, delay=0.):
        v = np.where((self.readings[:, 0] >= delay) & (self.readings[:, 2] != 0))[0]
        if len(v) > 1:
            # return np.mean(np.abs(self.readings[v, 4] - self.sp) / self.readings[v, 3])
            return np.mean(self.readings[v, 2] * (self.readings[v, 4] - self.sp) / self.readings[v, 3])
        else:
            return np.nan

    def last_dev(self, delay=0.):
        v = np.where((self.readings[:, 0] >= delay) & (self.readings[:, 2] != 0))[0]
        if len(v) > 1:
            return 100. * np.std(self.readings[v, 2] * (self.readings[v, 4] - self.sp) / self.readings[v, 3]) / self.last_resistance(delay=delay)
        else:
            return np.nan

    def last_vmn(self, delay=0.):
        v = np.where((self.readings[:, 0] >= delay) & (self.readings[:, 2] != 0))[0]
        if len(v) > 1:
            return np.mean(self.readings[v, 2] * (self.readings[v, 4] - self.sp))
        else:
            return np.nan

    def last_vmn_dev(self, delay=0.):  # TODO: should compute std per stack because this does not account for SP...
        v = np.where((self.readings[:, 0] >= delay) & (self.readings[:, 2] != 0))[0]
        if len(v) > 1:
            return 100. * np.std(self.readings[v, 2] * (self.readings[v, 4] - self.sp)) / self.last_vmn(delay=delay)
        else:
            return np.nan

    def last_iab(self, delay=0.):
        v = np.where((self.readings[:, 0] >= delay) & (self.readings[:, 2] != 0))[0]
        if len(v) > 1:
            return np.mean(self.readings[v, 3])
        else:
            return np.nan

    def last_iab_dev(self, delay=0.):
        v = np.where((self.readings[:, 0] >= delay) & (self.readings[:, 2] != 0))[0]
        if len(v) > 1:
            return 100. * np.std(self.readings[v, 3]) / self.last_iab(delay=delay)
        else:
            return np.nan

    @property
    def sp(self):  # TODO: allow for different strategies for computing sp (i.e. when sp drift is not linear)
        if self.readings.shape == (0,) or len(self.readings[self.readings[:, 2] == 1, :]) < 1 or \
                len(self.readings[self.readings[:, 2] == -1, :]) < 1:
            self.exec_logger.warning('Unable to compute sp: readings should at least contain one positive and one '
                                     'negative pulse')
            return 0.
        else:
            n_pulses = int(np.max(self.readings[:, 1]))
            polarity = np.array([np.median(self.readings[self.readings[:, 1] == i, 2]) for i in range(n_pulses + 1)])
            mean_vmn = []
            mean_iab = []
            for i in range(n_pulses + 1):
                mean_vmn.append(np.mean(self.readings[self.readings[:, 1] == i, 4]))
                mean_iab.append(np.mean(self.readings[self.readings[:, 1] == i, 3]))
            mean_vmn = np.array(mean_vmn)
            mean_iab = np.array(mean_iab)
            sp = np.mean(mean_vmn[np.ix_(polarity == 1)] + mean_vmn[np.ix_(polarity == -1)]) / 2
            return sp

    def _find_vab(self, vab, iab, vmn, p_max, vab_max, iab_max, vmn_max, vmn_min):
        iab_mean = np.mean(iab)
        iab_std = np.std(iab)
        vmn_mean = np.mean(vmn)
        vmn_std = np.std(vmn)
        # print(f'iab: ({iab_mean:.5f}, {iab_std:5f}), vmn: ({vmn_mean:.4f}, {vmn_std:.4f})')
        # bounds on iab
        iab_upper_bound = iab_mean + 2 * iab_std
        iab_lower_bound = np.max([0.00001, iab_mean - 2 * iab_std])
        # bounds on vmn
        vmn_upper_bound = vmn_mean + 2 * vmn_std
        vmn_lower_bound = np.max([0.000001, vmn_mean - 2 * vmn_std])
        # bounds on rab
        rab_lower_bound = np.max([0.1, np.abs(vab / iab_upper_bound)])
        rab_upper_bound = np.max([0.1, np.abs(vab / iab_lower_bound)])
        # bounds on r
        r_lower_bound = np.max([0.1, np.abs(vmn_lower_bound / iab_upper_bound)])
        r_upper_bound = np.max([0.1, np.abs(vmn_upper_bound / iab_lower_bound)])
        # conditions for vab update
        cond_vmn_max = rab_lower_bound / r_upper_bound * vmn_max
        cond_vmn_min = rab_upper_bound / r_lower_bound * vmn_min
        cond_p_max = np.sqrt(p_max * rab_lower_bound)
        cond_iab_max = rab_lower_bound * iab_max
        # print(f'Rab: [{rab_lower_bound:.1f}, {rab_upper_bound:.1f}], R: [{r_lower_bound:.1f},{r_upper_bound:.1f}]')
        print(f'[vab_max: {vab_max:.1f}, vmn_max: {cond_vmn_max:.1f}, vmn_min: {cond_vmn_min:.1f}, p_max: {cond_p_max:.1f}, iab_max: {cond_iab_max:.1f}]')
        new_vab = np.min([vab_max, cond_vmn_max, cond_p_max, cond_iab_max])
        if new_vab == vab_max:
            print(f'Vab {new_vab} bounded by Vab max')
        elif new_vab == cond_p_max:
            print(f'Vab {vab } bounded by P max')
        elif new_vab == cond_iab_max:
            print(f'Vab {vab} bounded by Iab max')
        elif new_vab == cond_vmn_max:
            print(f'Vab {vab} bounded by Vmn max')
        else:
            print(f'Vab {vab} bounded by Vmn min')

        return new_vab

    def compute_tx_volt(self, pulse_duration=0.1, strategy='vmax', tx_volt=5., vab_max=None,
                        iab_max=None, vmn_max=None, vmn_min=voltage_min, polarities=(1, -1), delay=0.05,
                        p_max=None, diff_vab_lim=2.5, n_steps=4):
        # TODO: Optimise how to pass iab_max, vab_max, vmn_min
        # TODO: Update docstring
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
        pulse_duration : float, optional
            Time in seconds for the pulse used to compute Rab.
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
        tx_volt = np.abs(tx_volt)
        vab_opt = tx_volt
        if self.tx.pwr.voltage_adjustable:
            if vmn_max is None:
                vmn_max = self.rx._voltage_max / 1000.
            if iab_max is None:
                iab_max = current_max
            if vab_max is None:
                vab_max = voltage_max
            # print(f'Vmn max: {vmn_max}')
            if p_max is None:
                p_max = vab_max * iab_max

            vab_max = np.abs(vab_max)
            vmn_min = np.abs(vmn_min)
            # tx_volt = np.abs(tx_volt)
            # Set gain at min
            self.rx.reset_gain()
            # vab_opt = tx_volt
            if tx_volt >= vab_max:
                strategy = 'constant'
            vab = np.min([np.abs(tx_volt), vab_max])
            if strategy == 'constant':
                vab_max = vab
                vab = vab * .9
                strategy = 'vmax'

            k = 0
            vab_list = np.zeros(n_steps + 1) * np.nan
            vab_list[k] = vab
            # self.tx.turn_on()
            switch_pwr_off, switch_tx_pwr_off = False, False  # TODO: check if these should be moved in kwargs
            if self.pwr_state == 'off':
                self.pwr_state = 'on'
                switch_tx_pwr_off = True
            self.tx.voltage = vab
            if self.tx.pwr.pwr_state == 'off':
                self.tx.pwr.pwr_state = 'on'
                switch_pwr_off = True
            if 1. / self.rx.sampling_rate > pulse_duration:
                sampling_rate = 1. / pulse_duration  # TODO: check this...
            else:
                sampling_rate = self.rx.sampling_rate
            current, voltage = 0., 0.
            diff_vab = np.inf
            if strategy == 'vmax' or strategy == 'vmin':
                while (k < n_steps) and (diff_vab > diff_vab_lim) and (vab_list[k] < vab_max):
                    if strategy == 'vmax':
                        vmn_min = vmn_max
                    vabs = []
                    self._vab_pulses(vab_list[k], sampling_rate=self.rx.sampling_rate, durations=[0.2, 0.2], polarities=[1, -1])
                    for pulse in range(2):
                        v = np.where((self.readings[:, 0] > delay) & (self.readings[:, 2] != 0) & (self.readings[:, 1]==pulse))[0]  # NOTE : discard data aquired in the first x ms
                        iab = self.readings[v, 3]/1000.
                        vmn = np.abs(self.readings[v, 4]/1000. * self.readings[v, 2])
                        new_vab = self._find_vab(vab_list[k], iab, vmn, p_max, vab_max, iab_max, vmn_max, vmn_min)
                        diff_vab = np.abs(new_vab - vab_list[k])
                        vabs.append(new_vab)
                        # print(f'new_vab: {new_vab}, diff_vab: {diff_vab}\n')
                        if diff_vab < diff_vab_lim:
                            print('stopped on vab increase too small')
                    k = k + 1
                    vab_list[k] = np.min(vabs)
                    time.sleep(0.5)
                    if self.tx.pwr.voltage_adjustable:
                        self.tx.voltage = vab_list[k]
                if k > n_steps:
                    print('stopped on maximum number of steps reached')
                vab_opt = vab_list[k]
                # print(f'Selected Vab: {vab_opt:.2f}')
                # if switch_pwr_off:
                #     self.tx.pwr.pwr_state = 'off'


        # if strategy == 'vmax':
        #     # implement different strategies
        #     if vab < vab_max and iab < current_max:
        #         vab = vab * np.min([0.9 * vab_max / vab, 0.9 * current_max / iab])  # TODO: check if setting at 90% of max as a safety margin is OK
        #     self.tx.exec_logger.debug(f'vmax strategy: setting VAB to {vab} V.')
        # elif strategy == 'vmin':
        #     if vab <= vab_max and iab < current_max:
        #         vab = vab * np.min([0.9 * vab_max / vab, vmn_min / np.abs(vmn), 0.9 * current_max / iab])  # TODO: check if setting at 90% of max as a safety margin is OK
        # elif strategy != 'constant':
        #     self.tx.exec_logger.warning(f'Unknown strategy {strategy} for setting VAB! Using {vab} V')
        # else:
        #     self.tx.exec_logger.debug(f'Constant strategy for setting VAB, using {vab} V')
        # # self.tx.turn_off()
        # if switch_pwr_off:
        #     self.tx.pwr.pwr_state = 'off'
        # if switch_tx_pwr_off:
        #     self.tx.pwr_state = 'off'
        # rab = (np.abs(vab) * 1000.) / iab
        # self.exec_logger.debug(f'RAB = {rab:.2f} Ohms')
        # if vmn < 0:
        #     polarity = -1  # TODO: check if we really need to return polarity
        # else:
        #     polarity = 1
        return vab_opt

    def _plot_readings(self, save_fig=False):
        # Plot graphs
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        fig, ax = plt.subplots(nrows=5, sharex=True)
        ax[0].plot(self.readings[:, 0], self.readings[:, 3], '-r', marker='.', label='iab')
        ax[0].set_ylabel('Iab [mA]')
        ax[1].plot(self.readings[:, 0], self.readings[:, 4] - self.sp , '-b', marker='.', label='vmn')
        ax[1].set_ylabel('Vmn [mV]')
        ax[2].plot(self.readings[:, 0], self.readings[:, 2], '-g', marker='.', label='polarity')
        ax[2].set_ylabel('polarity [-]')
        v = self.readings[:, 2] != 0
        ax[3].plot(self.readings[v, 0], (self.readings[v, 2] * (self.readings[v, 4] - self.sp)) / self.readings[v, 3],
                   '-m', marker='.', label='R [ohm]')
        ax[3].set_ylabel('R [ohm]')
        ax[4].plot(self.readings[v, 0], np.ones_like(self.readings[v, 0]) * self.sp, '-k', marker='.', label='SP [mV]')
        ax[4].set_ylabel('SP [mV]')
        # fig.legend()
        if save_fig:
            fig.savefig(f'figures/test.png')
        else:
            plt.show()
        warnings.resetwarnings()

    def calibrate_rx_bias(self):
        self.rx.bias += (np.mean(self.readings[self.readings[:, 2] == 1, 4])
                          + np.mean(self.readings[self.readings[:, 2] == -1, 4])) / 2.

    def vab_square_wave(self, vab, cycle_duration, sampling_rate=None, cycles=3, polarity=1, duty_cycle=1.,
                        append=False):
        """
        Performs a Vab injection following a square wave and records full waveform data. Calls in function Vab_pulses.

        Parameters
        ----------
        vab: float,
            Injection voltage [V]
        cycle_duration: float
            Duration of one cycle within the square wave (in seconds)
        sampling_rate: float, None Default None
            Sampling rate for Rx readings
        cycles: integer, Default: 3
            Number of cycles
        polarity: 1, 0 , -1
            Starting polarity
        duty_cycle: float (0 to 1)
            Duty cycle of injection wave
        append: bool, Default: False
        """
        self.exec_logger.event(f'OhmPiHardware\tvab_square_wave\tbegin\t{datetime.datetime.utcnow()}')
        switch_pwr_off, switch_tx_pwr_off = False, False
        # switches tx pwr on if needed (relays switching dps on and off)
        if self.pwr_state == 'off':
            self.pwr_state = 'on'
            switch_tx_pwr_off = True
        # if self.tx.pwr.pwr_state == 'off':
        #     self.tx.pwr.pwr_state = 'on'
        #     switch_pwr_off = True

        self._gain_auto(vab=vab)
        assert 0. <= duty_cycle <= 1.
        if duty_cycle < 1.:
            durations = [cycle_duration/2 * duty_cycle, cycle_duration/2 * (1.-duty_cycle)] * 2 * cycles
            pol = [-int(polarity * np.heaviside(i % 2, -1.)) for i in range(2 * cycles)]
            # pol = [-int(self.tx.polarity * np.heaviside(i % 2, -1.)) for i in range(2 * cycles)]
            polarities = [0] * (len(pol) * 2)
            polarities[0::2] = pol
        else:
            durations = [cycle_duration / 2] * 2 * cycles
            polarities = None
        self._vab_pulses(vab, durations, sampling_rate, polarities=polarities,  append=append)
        self.exec_logger.event(f'OhmPiHardware\tvab_square_wave\tend\t{datetime.datetime.utcnow()}')
        if switch_pwr_off:
            self.tx.pwr.pwr_state = 'off'
        if switch_tx_pwr_off:
            self.pwr_state = 'off'

    def _vab_pulse(self, vab=None, duration=1., sampling_rate=None, polarity=1, append=False):
        """ Gets VMN and IAB from a single voltage pulse
        """
        #self.tx.polarity = polarity
        if sampling_rate is None:
            sampling_rate = RX_CONFIG['sampling_rate']
        if self.tx.pwr.voltage_adjustable:
            if self.tx.voltage != vab:
                self.tx.voltage = vab
        else:
            vab = self.tx.voltage

        # switches dps pwr on if needed
        switch_pwr_off = False
        if self.tx.pwr.pwr_state == 'off':
            self.tx.pwr.pwr_state = 'on'
            switch_pwr_off = True
        # reads current and voltage during the pulse
        injection = Thread(target=self._inject, kwargs={'injection_duration': duration, 'polarity': polarity})
        readings = Thread(target=self._read_values, kwargs={'sampling_rate': sampling_rate, 'append': append})
        readings.start()
        injection.start()
        readings.join()
        injection.join()
        self.tx.polarity = 0   #TODO: is this necessary?
        if switch_pwr_off:
            self.tx.pwr.pwr_state = 'off'
    def _vab_pulses(self, vab, durations, sampling_rate, polarities=None, append=False):
        switch_pwr_off, switch_tx_pwr_off = False, False

        # switches tx pwr on if needed (relays switching dps on and off)
        if self.pwr_state == 'off':
            self.pwr_state = 'on'
            switch_pwr_off = True
        n_pulses = len(durations)
        self.exec_logger.debug(f'n_pulses: {n_pulses}')
        if self.tx.pwr.voltage_adjustable:
            self.tx.voltage = vab
        else:
            vab = self.tx.voltage

        # switches dps pwr on if needed
        if self.tx.pwr.pwr_state == 'off':
            self.tx.pwr.pwr_state = 'on'
            switch_pwr_off = True

        if sampling_rate is None:
            sampling_rate = RX_CONFIG['sampling_rate']
        if polarities is not None:
            assert len(polarities) == n_pulses
        else:
            polarities = [-int(self.tx.polarity * np.heaviside(i % 2, -1.)) for i in range(n_pulses)]
        if not append:
            self._clear_values()
        for i in range(n_pulses):
            self._vab_pulse(vab=vab, duration=durations[i], sampling_rate=sampling_rate, polarity=polarities[i],
                            append=True)
        if switch_pwr_off:
            self.tx.pwr.pwr_state = 'off'
        if switch_tx_pwr_off:
            self.pwr_state = 'off'
    
    def switch_mux(self, electrodes, roles=None, state='off', **kwargs):
        """Switches on multiplexer relays for given quadrupole.

        Parameters
        ----------
        electrodes : list
            List of integers representing the electrode ids.
        roles : list, optional
            List of roles of electrodes, optional
        state : str, optional
            Either 'on' or 'off'.
        """
        self.exec_logger.event(f'OhmPiHardware\tswitch_mux\tbegin\t{datetime.datetime.utcnow()}')
        status = True
        if roles is None:
            roles = ['A', 'B', 'M', 'N']
        if len(electrodes) == len(roles):
            # TODO: Check that we don't set incompatible roles to the same electrode
            elec_dict = {i: [] for i in roles}
            mux_workers = []
            for idx, elec in enumerate(electrodes):
                elec_dict[roles[idx]].append(elec)
                try:
                    mux = self._cabling[(elec, roles[idx])][0]
                    if mux not in mux_workers:
                        mux_workers.append(mux)
                except KeyError:
                    self.exec_logger.debug(f'Unable to switch {state} ({elec}, {roles[idx]})'
                                           f': not in cabling and will be ignored...')
                    status = False
            if status:
                mux_workers = list(set(mux_workers))
                b = Barrier(len(mux_workers)+1)
                self.mux_barrier = b
                for idx, mux in enumerate(mux_workers):
                    # Create a new thread to perform some work
                    self.mux_boards[mux].barrier = b
                    kwargs.update({'elec_dict': elec_dict, 'state': state})
                    mux_workers[idx] = Thread(target=self.mux_boards[mux].switch, kwargs=kwargs)  # TODO: handle minimum delay between two relays activation (to avoid lagging during test_mux at high speed)
                    mux_workers[idx].start()
                try:
                    self.mux_barrier.wait()
                    for mux_worker in mux_workers:
                        mux_worker.join()
                except BrokenBarrierError:
                    self.exec_logger.warning('Switching aborted')
                    status = False
        else:
            self.exec_logger.error(
                f'Unable to switch {state} electrodes: number of electrodes and number of roles do not match!')
            status = False
        self.exec_logger.event(f'OhmPiHardware\tswitch_mux\tend\t{datetime.datetime.utcnow()}')
        return status

    def test_mux(self, channel=None, activation_time=1.0): #TODO: add test in reverse order on each mux board
        """Interactive method to test the multiplexer.

        Parameters
        ----------
        channel : tuple, optional
            (electrode_nr, role) to test.
        activation_time : float, optional
            Time in seconds during which the relays are activated.
        """
        self.reset_mux()

        if channel is not None:
            try:
                electrodes = [int(channel[0])]
                roles = [channel[1]]
            except Exception as e:
                self.exec_logger.error(f'Unable to parse channel: {e}')
                return
            self.switch_mux(electrodes, roles, state='on')
            time.sleep(activation_time)
            self.switch_mux(electrodes, roles, state='off')
        else:
            list_of_muxes = [i for i in self.mux_boards.keys()]
            list_of_muxes.sort()
            for m_id in list_of_muxes:
                for c in self.mux_boards[m_id].cabling.keys():
                    self.exec_logger.info(f'Testing electrode {c[0]} with role {c[1]}.')
                    self.switch_mux(electrodes=[c[0]], roles=[c[1]], state='on')
                    time.sleep(activation_time)
                    self.switch_mux(electrodes=[c[0]], roles=[c[1]], state='off')
            # for c in self._cabling.keys():
            #     self.exec_logger.info(f'Testing electrode {c[0]} with role {c[1]}.')
            #     self.switch_mux(electrodes=[c[0]], roles=[c[1]], state='on')
            #     time.sleep(activation_time)
            #     self.switch_mux(electrodes=[c[0]], roles=[c[1]], state='off')
        self.exec_logger.info('Test finished.')

    def reset_mux(self):
        """Switches off all multiplexer relays.
        """

        self.exec_logger.debug('Resetting all mux boards ...')
        self.exec_logger.event(f'OhmPiHardware\treset_mux\tbegin\t{datetime.datetime.utcnow()}')
        for mux_id, mux in self.mux_boards.items():  # noqa
            self.exec_logger.debug(f'Resetting {mux_id}.')
            mux.reset()
        self.exec_logger.event(f'OhmPiHardware\treset_mux\tend\t{datetime.datetime.utcnow()}')
