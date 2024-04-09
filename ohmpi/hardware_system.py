import importlib
import datetime
import time
import numpy as np
import sys
import os

try:
    import matplotlib.pyplot as plt
except Exception:  # noqa
    pass
from ohmpi.hardware_components.abstract_hardware_components import CtlAbstract
from ohmpi.logging_setup import create_stdout_logger
from ohmpi.utils import update_dict
try:
    from ohmpi.config import HARDWARE_CONFIG as HC
except ModuleNotFoundError:
    print('The system configuration file is missing or broken. If you have not yet defined your system configuration, '
          'you can create a configuration file by using the python setup_config script. '
          'To run this script, type the following command in the terminal from the directory where you '
          'installed ohmpi : \npython3 setup_config.py\n'
          'If you deleted your config.py file by mistake, you should find a backup in configs/config_backup.py')
    sys.exit(-1)
from threading import Thread, Event, Barrier, BrokenBarrierError
import warnings


# plt.switch_backend('agg')  # for thread safe operations...


def elapsed_seconds(start_time):
    lap = datetime.datetime.utcnow() - start_time
    return lap.total_seconds()


class OhmPiHardware:
    """OhmPiHardware class.
        """

    def __init__(self, **kwargs):
        # OhmPiHardware initialization
        self.exec_logger = kwargs.pop('exec_logger', create_stdout_logger('exec_hw'))
        self.exec_logger.event(f'OhmPiHardware\tinit\tbegin\t{datetime.datetime.utcnow()}')
        self.data_logger = kwargs.pop('exec_logger', create_stdout_logger('data_hw'))
        self.soh_logger = kwargs.pop('soh_logger', create_stdout_logger('soh_hw'))
        self.tx_sync = Event()
        self.hardware_config = kwargs.pop('hardware_config', HC)
        HARDWARE_CONFIG = self.hardware_config
        self.exec_logger.debug(f'Hardware config: {HARDWARE_CONFIG}')
        # Define the default controller, a distinct controller could be defined for each tx, rx or mux board
        # when using a distinct controller, the specific controller definition must be included in the component
        # configuration
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

        self.iab_max = np.min([TX_CONFIG['current_max'], HARDWARE_CONFIG['pwr'].pop('current_max', np.inf),
                               np.min(np.hstack(
                                       (np.inf,
                                        [MUX_CONFIG[i].pop('current_max', np.inf) for i in MUX_CONFIG.keys()])))])
        self.vab_max = np.min([TX_CONFIG['voltage_max'],
                               np.min(np.hstack(
                                       (np.inf,
                                        [MUX_CONFIG[i].pop('voltage_max', np.inf) for i in MUX_CONFIG.keys()])))])

        self.vmn_min = RX_CONFIG['voltage_min']
        # TODO: should replace voltage_max and voltage_min by vab_max and vmn_min...
        self.sampling_rate = RX_CONFIG['sampling_rate']

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

        # Initialize power source
        HARDWARE_CONFIG['pwr'].pop('model')
        HARDWARE_CONFIG['pwr'].update(**HARDWARE_CONFIG['pwr'])  # NOTE: Explain why this is needed or delete me
        HARDWARE_CONFIG['pwr'].update({'ctl': HARDWARE_CONFIG['pwr'].pop('ctl', self.ctl)})
        HARDWARE_CONFIG['pwr'].update({'current_max': self.iab_max})
        if isinstance(HARDWARE_CONFIG['pwr']['ctl'], dict):
            ctl_mod = HARDWARE_CONFIG['pwr']['ctl'].pop('model', self.ctl)
            if isinstance(ctl_mod, str):
                ctl_mod = importlib.import_module(f'ohmpi.hardware_components.{ctl_mod}')
            HARDWARE_CONFIG['pwr']['ctl'] = ctl_mod.Ctl(**HARDWARE_CONFIG['pwr']['ctl'])

        HARDWARE_CONFIG['pwr'].update({
            'interface_name': HARDWARE_CONFIG['pwr'].pop('interface_name', None)})

        HARDWARE_CONFIG['pwr'].update({
            'connection': HARDWARE_CONFIG['pwr'].pop(
                'connection', HARDWARE_CONFIG['pwr']['ctl'].interfaces[
                    HARDWARE_CONFIG['pwr']['interface_name']])})

        HARDWARE_CONFIG['pwr'].update({'exec_logger': self.exec_logger, 'data_logger': self.data_logger,
                                       'soh_logger': self.soh_logger})

        # if self.tx.specs['connect']:
        #     self.pwr_state = "on"
        self.pwr = kwargs.pop('pwr', pwr_module.Pwr(**HARDWARE_CONFIG['pwr']))
        # if self.tx.specs['connect']:
        #     self.pwr_state = 'off'

        # Join tX and pwr
        self.tx.pwr = self.pwr
        if not self.tx.pwr.voltage_adjustable:
            self.tx.pwr._pwr_latency = 0
        if self.tx.specs['connect']:
            self.tx.polarity = 0
        self.tx.pwr._current_max = self.iab_max

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
            mux_config.update({'connection': mux_config.pop('connection', mux_config['ctl'].interfaces[
                mux_config.pop('interface_name', 'i2c')])})
            mux_config['id'] = mux_id

            self.mux_boards[mux_id] = mux_module.Mux(**mux_config)

        self.mux_barrier = Barrier(len(self.mux_boards) + 1)
        self._cabling = {}
        for mux_id, mux in self.mux_boards.items():
            mux.barrier = self.mux_barrier
            for k, v in mux.cabling.items():
                update_dict(self._cabling, {k: (mux_id, k[0])})  # TODO: in theory k[0] is not needed in values
        # Complete OhmPiHardware initialization
        self.readings = np.array([])  # time series of acquired data
        self.sp = None  # init SP
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

    def _read_values(self, sampling_rate=None, append=False, test_r_shunt=False):  # noqa
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
        # if test_r_shunt:
        _current = []
        if sampling_rate is None:
            sampling_rate = self.rx.sampling_rate
        sample = 0
        lap = datetime.datetime.utcnow()  # just in case tx_sync is not set immediately after passing wait
        self.tx_sync.wait()  #
        if not append or self._start_time is None:
            self._start_time = datetime.datetime.utcnow()
            # TODO: Check if replacing the following two options by a reset_buffer method of TX would be OK
            time.sleep(np.max([self.rx.latency, self.tx.latency]))  # if continuous mode
            # _ = self.rx.voltage # if not continuous mode

        while self.tx_sync.is_set():
            lap = datetime.datetime.utcnow()
            r = [elapsed_seconds(self._start_time), self._pulse, self.tx.polarity, self.tx.current, self.rx.voltage]
            if self.tx_sync.is_set():
                sample += 1
                _readings.append(r)
                if test_r_shunt:
                    self.tx.pwr._retrieve_current()
                    _current.append(self.tx.pwr.current)
                sleep_time = self._start_time + datetime.timedelta(seconds=sample / sampling_rate) - lap
                if sleep_time.total_seconds() < 0.:
                    # TODO: count how many samples were skipped to make a stat that could be used to qualify pulses
                    sample += int(sampling_rate * np.abs(sleep_time.total_seconds())) + 1
                    sleep_time = self._start_time + datetime.timedelta(seconds=sample / sampling_rate) - lap
                time.sleep(np.max([0., sleep_time.total_seconds()]))

        self.exec_logger.debug(f'pulse {self._pulse}: elapsed time {(lap - self._start_time).total_seconds()} s')
        self.exec_logger.debug(f'pulse {self._pulse}: total samples {len(_readings)}')
        self.readings = np.array(_readings)
        if test_r_shunt:
            self._current = np.array(_current)
        self._pulse += 1
        self.exec_logger.event(f'OhmPiHardware\tread_values\tend\t{datetime.datetime.utcnow()}')

    def select_samples(self, delay=0.):
        x = []
        for pulse in np.unique(self.readings[:, 1]):
            v = np.where((self.readings[:, 1] == pulse))[0]
            if len(v) > 0:  # to avoid pulse not recorded due to Raspberry Pi lag...
                t_start_pulse = min(self.readings[v, 0])
                x.append(np.where((self.readings[:, 0] >= t_start_pulse + delay) & (self.readings[:, 2] != 0) & (
                        self.readings[:, 1] == pulse))[0])
        x = np.concatenate(np.array(x, dtype='object'))
        x = x.astype('int32')
        return x

    def last_resistance(self, delay=0.):
        v = self.select_samples(delay)
        if self.sp is None:
            self.last_sp(delay=delay)
        if len(v) > 1:
            # return np.mean(np.abs(self.readings[v, 4] - self.sp) / self.readings[v, 3])
            return np.mean(self.readings[v, 2] * (self.readings[v, 4] - self.sp) / self.readings[v, 3])
        else:
            return np.nan

    def last_dev(self, delay=0.):
        v = self.select_samples(delay)
        if self.sp is None:
            self.last_sp(delay=delay)
        if len(v) > 1:
            return 100. * np.std(
                self.readings[v, 2] * (self.readings[v, 4] - self.sp) / self.readings[v, 3]) / self.last_resistance(
                delay=delay)
        else:
            return np.nan

    def last_vmn(self, delay=0.):
        v = self.select_samples(delay)
        if self.sp is None:
            self.last_sp(delay=delay)
        if len(v) > 1:
            return np.mean(self.readings[v, 2] * (self.readings[v, 4] - self.sp))
        else:
            return np.nan

    def last_vmn_dev(self, delay=0.):  # TODO: should compute std per stack because this does not account for SP...
        v = self.select_samples(delay)
        if self.sp is None:
            self.last_sp(delay=delay)
        if len(v) > 1:
            return 100. * np.std(self.readings[v, 2] * (self.readings[v, 4] - self.sp)) / self.last_vmn(delay=delay)
        else:
            return np.nan

    def last_iab(self, delay=0.):
        v = self.select_samples(delay)
        if len(v) > 1:
            return np.mean(self.readings[v, 3])
        else:
            return np.nan

    def last_iab_dev(self, delay=0.):
        v = self.select_samples(delay)
        if len(v) > 1:
            return 100. * np.std(self.readings[v, 3]) / self.last_iab(delay=delay)
        else:
            return np.nan

    def last_sp(self,
                delay=0.):  # TODO: allow for different strategies for computing sp (i.e. when sp drift is not linear)
        v = self.select_samples(delay)
        if self.readings.shape == (0,) or len(self.readings[self.readings[:, 2] == 1, :]) < 1 or \
                len(self.readings[self.readings[:, 2] == -1, :]) < 1:
            self.exec_logger.warning('Unable to compute sp: readings should at least contain one positive and one '
                                     'negative pulse')
            return 0.
        else:
            n_pulses = np.unique(self.readings[v, 1])
            polarity = np.array([np.median(self.readings[v][self.readings[v, 1] == i, 2]) for i in n_pulses])
            mean_vmn = []
            for pulse in n_pulses:
                mean_vmn.append(np.mean(self.readings[v][self.readings[v, 1] == pulse, 4]))
            mean_vmn = np.array(mean_vmn)
            self.sp = np.mean(mean_vmn[np.ix_(polarity == 1)] + mean_vmn[np.ix_(polarity == -1)]) / 2
            # return sp

    def _find_vab(self, vab, iab, vmn, p_max, vab_max, vab_min, iab_max, vmn_max, vmn_req):
        """ Finds the best injection voltage

        Parameters
        ----------
        vab: float
            vab in use
        iab: np.ndarray, list
            series of current measured during the pulses
        vmn: np.ndarray, list

        p_max: float

        vab_max: float

        vab_min: float

        iab_max: float

        vmn_max: float

        vmn_req: float

        Returns
        -------
        float
            improved value for vab

        """
        print('Searching for the best Vab...')
        iab_mean = np.mean(iab)
        iab_std = np.std(iab)
        vmn_mean = np.mean(vmn)
        vmn_std = np.std(vmn)
        # print(f'iab: ({iab_mean:.5f}, {iab_std:5f}), vmn: ({vmn_mean:.4f}, {vmn_std:.4f})')
        # bounds on iab
        iab_upper_bound = iab_mean + 2 * iab_std  # why no absolute upper bound?
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
        cond_vmn_req = rab_upper_bound / r_lower_bound * vmn_req
        cond_p_max = np.sqrt(p_max * rab_lower_bound)
        cond_iab_max = rab_lower_bound * iab_max
        self.exec_logger.debug(f'Rab: [{rab_lower_bound:.1f}, {rab_upper_bound:.1f}], R: [{r_lower_bound:.1f},{r_upper_bound:.1f}]')
        self.exec_logger.debug(f'*** [{5 * rab_lower_bound / r_upper_bound:.1f}, {5 * rab_lower_bound / r_lower_bound:.1f}] V ***')
        self.exec_logger.debug(
            f'[vab_max: {vab_max:.1f} V, vmn_max: {cond_vmn_max:.1f} V, vmn_req: {cond_vmn_req:.1f} V, '
            f'p_max: {cond_p_max:.1f} V, iab_max: {cond_iab_max:.1f} V]')
        new_vab = np.max([np.min([vab_max, cond_vmn_max, cond_p_max, cond_iab_max, cond_vmn_req]), vab_min])
        if new_vab == vab_max:
            self.exec_logger.debug(f'Vab {new_vab} bounded by Vab max')
        elif new_vab == cond_p_max:
            self.exec_logger.debug(f'Vab {vab} bounded by P max')
        elif new_vab == cond_iab_max:
            self.exec_logger.debug(f'Vab {vab} bounded by Iab max')
        elif new_vab == cond_vmn_max:
            self.exec_logger.debug(f'Vab {vab} bounded by Vmn max')
        elif new_vab == vab_min:
            self.exec_logger.debug(f'Vab {vab} bounded by Vab min')
        else:
            self.exec_logger.debug(f'Vab {vab} bounded by Vmn min')
        r = new_vab / vab
        self.exec_logger.debug(f'iab: [{iab_lower_bound * r:.4f}, {iab_upper_bound * r:.4f}] A,',
              f'vmn : [{vmn_lower_bound * r:.3f}, {vmn_upper_bound * r:.3f}] V,',
              f'p : [{vmn_lower_bound * iab_lower_bound * r ** 2:.2f}, {vmn_upper_bound * iab_upper_bound * r ** 2:.2f}] W, ',
              f'Rab : [{rab_lower_bound}, {rab_upper_bound}] Ohms, R : [{r_lower_bound}, {r_upper_bound}] Ohms\n',
              f'-> Selecting {new_vab:.2f} V.')
        return new_vab

    def compute_vab(self, pulse_duration=0.1, strategy='vmax', vab=5., vab_max=None, vab_min=None,
                    iab_max=None, vmn_max=None, vmn_min=None, polarities=(1, -1), delay=0.05,
                    p_max=None, diff_vab_lim=2.5, n_steps=4, filename=None, quad_id=0):
        """ Estimates best Vab voltage based on different strategies.
        In "vmax" and "vmin" strategies, we iteratively increase/decrease the vab while
        checking vmn < vmn_max, vmn > vmn_min and iab < iab_max. We do a maximum of n_steps
        and when the difference between the two steps is below diff_vab_lim or we
        reached the maximum number of steps, we return the vab found.

        Parameters
        ----------
        pulse_duration : float, optional
            Time in seconds for the pulse used to compute optimal Vab.
        strategy : str, optional
            Either:
            - vmax : compute Vab to reach a maximum Iab without exceeding vab_max or p_max
            - vmin : compute Vab to reach at least vmn_min
            - constant : apply given Vab, if vab > vab_max then strategy is changed to vmax
            - full_constant : apply given Vab, no checking with vmax (at your own risk!)
        vab : float, optional
            Voltage to apply for guessing the best voltage. 5 V applied
            by default. If strategy "constant" is chosen, constant voltage
            to applied is "vab".
        vab_max : float, optional
            Maximum injection voltage to apply to tx (used by all strategies).
        vmn_max : float, optional
            Maximum voltage target for rx (used by vmax strategy).
        vmn_min : float, optional
            Minimum voltage target for rx (used by vmin strategy).
        polarities : list of int, optional
            Polarity of the AB injection used to compute optimal Vab.
            Default is one positive, then one negative.
        p_max : float, optional
            Maximum power that the device can support/sustain.
        diff_vab_lim : float, optional
            Minimal change in vab between steps for continuing the search for
            optimal vab. If change between two steps is below the diff_vab_lim,
            we have found the optimal vab.
        n_steps : int, optional
            Number of steps to try to find optimal vab. Each step last at least
            injection_duration*len(polarities) seconds.

        Returns
        -------
        vab : float
            Proposed Vab according to the given strategy.
            :param vmn_min:
            :param vmn_max:
            :param iab_max:
        """

        # TODO: Optimise how to pass iab_max, vab_max, vmn_min
        # TODO: Update docstring
        # TODO: replace vmn_min and vmn_max by vmn_requested

        vab_opt = np.abs(vab)
        polarities = list(polarities)
        if not self.tx.pwr.voltage_adjustable:
            vab_opt = self.tx.pwr.voltage
        else:
            if strategy == 'full_constant':
                return vab
            if vmn_max is None:
                vmn_max = self.rx._voltage_max / 1000.
            if iab_max is None:
                iab_max = self.iab_max
            if vmn_min is None:
                vmn_min = self.vmn_min
            if vab_max is None:
                vab_max = self.vab_max
            if vab_min is None:
                vab_min = vmn_max
            # print(f'Vmn max: {vmn_max}')
            if p_max is None:
                p_max = vab_max * iab_max

            vab_max = np.abs(vab_max)
            vmn_min = np.abs(vmn_min)

            # Set gain at min
            self.rx.reset_gain()  # NOTE : is it the minimum because we are not measuring ?

            if vab >= vab_max:
                strategy = 'constant'
            vab = np.min([np.abs(vab), vab_max])
            if strategy == 'constant':
                vab_max = vab
                vab = vab * .9
                strategy = 'vmax'

            k = 0
            vab_list = np.zeros(n_steps + 1) * np.nan
            vab_list[k] = vab

            if self.pwr_state == 'off':
                self.pwr_state = 'on'

            # Switches on measuring LED
            self.tx.measuring = 'on'

            self.tx.voltage = vab
            if self.tx.pwr.pwr_state == 'off':
                self.tx.pwr.pwr_state = 'on'

            if 1. / self.rx.sampling_rate > pulse_duration:
                sampling_rate = 1. / pulse_duration  # TODO: check this...
            else:
                sampling_rate = self.rx.sampling_rate
            current, voltage = 0., 0.
            diff_vab = np.inf
            if strategy == 'vmax' or strategy == 'vmin':
                while (k < n_steps) and (diff_vab > diff_vab_lim) and (vab_list[k] < vab_max):
                    self.exec_logger.event(
                        f'OhmPiHardware\t_compute_vab_sleep\tbegin\t{datetime.datetime.utcnow()}')
                    time.sleep(0.2)  # TODO: replace this by discharging DPS on resistor with relay on GPIO5
                                     # (at least for strategy vmin,
                                     # but might be useful in vmax when last vab too high...)
                    self.exec_logger.event(
                        f'OhmPiHardware\t_compute_vab_sleep\tend\t{datetime.datetime.utcnow()}')
                    if strategy == 'vmax':
                        vmn_min = vmn_max
                    vabs = []
                    self._vab_pulses(vab_list[k], sampling_rate=self.rx.sampling_rate,
                                     durations=[pulse_duration, pulse_duration], polarities=polarities)
                    for pulse in range(len(polarities)):
                        # v = np.where((self.readings[:, 0] > delay) & (self.readings[:, 2] != 0) & (
                        #             self.readings[:, 1] == pulse))[0]  # NOTE : discard data acquired in the first x ms
                        v = self.select_samples(delay=delay)
                        iab = self.readings[v, 3] / 1000.
                        vmn = np.abs(self.readings[v, 4] / 1000. * self.readings[v, 2])
                        new_vab = self._find_vab(vab_list[k], iab, vmn, p_max, vab_max, vab_min, iab_max, vmn_max, vmn_min)
                        diff_vab = np.abs(new_vab - vab_list[k])
                        vabs.append(new_vab)
                        # print(f'new_vab: {new_vab}, diff_vab: {diff_vab}\n')
                        if diff_vab < diff_vab_lim:
                            self.exec_logger.debug('Compute_vab stopped on vab increase too small')
                    if filename is not None:
                        os.makedirs(filename[:-4], exist_ok=True)
                        readings = np.hstack((self.readings,np.ones((self.readings.shape[0], 1)) * vab_list[k]))
                        np.save(os.path.join(filename[:-4], f'quad{quad_id}_step{k}.npy'), readings)
                    k = k + 1
                    vab_list[k] = np.min(vabs)
                    if self.tx.pwr.voltage_adjustable:
                        self.tx.voltage = vab_list[k]
                if k > n_steps:
                    self.exec_logger.debug('Compute_vab stopped on maximum number of steps reached')
                vab_opt = vab_list[k]

        return vab_opt

    def discharge_pwr(self):
        if self.tx.pwr.voltage_adjustable:
            # TODO: implement strategy to discharge pwr based on hardware version => variable in TX should tell if it can discharge the pwr or not
            ### if discharge relay manually add on mb_2024_0_2, then should not activate AB relays but simply wait for automatic discharge
            ### if mb_2024_1_X then TX should handle the pwr discharge

            # time.sleep(1.0)
            self.tx.discharge_pwr()

    def _plot_readings(self, save_fig=False, filename=None):
        # Plot graphs
        flag = False
        if self.sp is None:
            flag = True
            self.exec_logger.info('self.sp is None, setting it to 0')
            self.sp = 0
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        fig, ax = plt.subplots(nrows=5, sharex=True)
        ax[0].plot(self.readings[:, 0], self.readings[:, 3], '-r', marker='.', label='iab')
        ax[0].set_ylabel('Iab [mA]')
        ax[1].plot(self.readings[:, 0], self.readings[:, 4] - self.sp, '-b', marker='.', label='vmn')
        ax[1].set_ylabel('Vmn [mV]')
        ax[2].plot(self.readings[:, 0], self.readings[:, 2], '-g', marker='.', label='polarity')
        ax[2].set_ylabel('polarity [-]')
        v = self.readings[:, 2] != 0
        ax[3].plot(self.readings[v, 0], (self.readings[v, 2] * (self.readings[v, 4] - self.sp)) / self.readings[v, 3],
                   '-m', marker='.', label='R [ohm]')
        ax[3].set_ylabel('R [ohm]')
        ax[4].plot(self.readings[v, 0], np.ones_like(self.readings[v, 0]) * self.sp, '-k', marker='.', label='SP [mV]')
        ax[4].set_ylabel('SP [mV]')
        if flag:  # if it was None, we put it back to None to not interfere with the rest
            self.sp = None
        # fig.legend()
        if save_fig:
            if filename is None:
                fig.savefig(f'figures/test.png')
            else:
                fig.savefig(filename)
        else:
            plt.show()
        warnings.resetwarnings()

    def calibrate_rx_bias(self):
        self.rx.bias += (np.mean(self.readings[self.readings[:, 2] == 1, 4])
                         + np.mean(self.readings[self.readings[:, 2] == -1, 4])) / 2.

    def vab_square_wave(self, vab, cycle_duration, sampling_rate=None, cycles=3, polarity=1, duty_cycle=1.,
                        append=False):
        """Performs a Vab injection following a square wave and records full waveform data. Calls in function Vab_pulses.

        Parameters
        ----------
        vab: float
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
        append: bool, optional
            Default: False
        """
        self.exec_logger.event(f'OhmPiHardware\tvab_square_wave\tbegin\t{datetime.datetime.utcnow()}')
        switch_pwr_off, switch_tx_pwr_off = False, False
        # switches tx pwr on if needed (relays switching dps on and off)
        if self.pwr_state == 'off':
            self.pwr_state = 'on'
            switch_tx_pwr_off = True

        # Switches on measuring LED
        if self.tx.measuring == 'off':
            self.tx.measuring = 'on'

        if self.tx.pwr.pwr_state == 'off':
            self.tx.pwr.pwr_state = 'on'
            switch_pwr_off = True

        self._gain_auto(vab=vab)
        assert 0. <= duty_cycle <= 1.
        if duty_cycle < 1.:
            durations = [cycle_duration / 2 * duty_cycle, cycle_duration / 2 * (1. - duty_cycle)] * 2 * cycles
            pol = [-int(polarity * np.heaviside(i % 2, -1.)) for i in range(2 * cycles)]
            # pol = [-int(self.tx.polarity * np.heaviside(i % 2, -1.)) for i in range(2 * cycles)]
            polarities = [0] * (len(pol) * 2)
            polarities[0::2] = pol
        else:
            durations = [cycle_duration / 2] * 2 * cycles
            polarities = [-int(polarity * np.heaviside(i % 2, -1.)) for i in range(2 * cycles)]
        self._vab_pulses(vab, durations, sampling_rate, polarities=polarities, append=append)
        self.exec_logger.event(f'OhmPiHardware\tvab_square_wave\tend\t{datetime.datetime.utcnow()}')
        if switch_pwr_off:
            self.tx.pwr.pwr_state = 'off'
        if switch_tx_pwr_off:
            self.pwr_state = 'off'
        # Switches off measuring LED
        self.tx.measuring = 'off'

    def _vab_pulse(self, vab=None, duration=1., sampling_rate=None, polarity=1, append=False):
        """ Gets VMN and IAB from a single voltage pulse
        """
        # self.tx.polarity = polarity
        if sampling_rate is None:
            sampling_rate = self.sampling_rate
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
        pulse_only = False

        # reads current and voltage during the pulse
        injection = Thread(target=self._inject, kwargs={'injection_duration': duration, 'polarity': polarity})
        readings = Thread(target=self._read_values, kwargs={'sampling_rate': sampling_rate, 'append': append})
        readings.start()
        injection.start()
        readings.join()
        injection.join()
        self.tx.polarity = 0  # TODO: is this necessary?
        if switch_pwr_off:
            self.tx.pwr.pwr_state = 'off'

    def _vab_pulses(self, vab, durations, sampling_rate, polarities=None, append=False):
        switch_pwr_off, switch_tx_pwr_off = False, False

        # switches tx pwr on if needed (relays switching dps on and off)
        if self.pwr_state == 'off':
            self.pwr_state = 'on'
            switch_tx_pwr_off = True
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
            sampling_rate = self.sampling_rate
        if polarities is not None:
            assert len(polarities) == n_pulses
        else:
            polarities = [-int(self.tx.polarity * np.heaviside(i % 2, -1.)) for i in
                          range(n_pulses)]  # TODO: this doesn't work if tx.polarity=0 which is the case at init...
        if not append:
            self._clear_values()
            self.sp = None  # re-initialise SP before new Vab_pulses
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
                b = Barrier(len(mux_workers) + 1)
                self.mux_barrier = b
                for idx, mux in enumerate(mux_workers):
                    # Create a new thread to perform some work
                    self.mux_boards[mux].barrier = b
                    kwargs.update({'elec_dict': elec_dict, 'state': state})
                    mux_workers[idx] = Thread(target=self.mux_boards[mux].switch,
                                              kwargs=kwargs)  # TODO: handle minimum delay between two relays activation (to avoid lagging during test_mux at high speed)
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

    def test_mux(self, channel=None, activation_time=1.0):  # TODO: add test in reverse order on each mux board
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
