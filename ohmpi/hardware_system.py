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
    except:
        print(f'Cannot set value {v} in TX_CONFIG[{k}]')

RX_CONFIG = HARDWARE_CONFIG['rx']
for k, v in rx_module.SPECS['rx'].items():
    try:
        RX_CONFIG.update({k: RX_CONFIG.pop(k, v['default'])})
    except:
        print(f'Cannot set value {v} in RX_CONFIG[{k}]')

current_max = np.min([TX_CONFIG['voltage_max']/50/TX_CONFIG['r_shunt'],  # TODO: replace 50 by a TX config
                      np.min(np.hstack((np.inf, [MUX_CONFIG[i].pop('current_max', np.inf) for i in MUX_CONFIG.keys()])))])
voltage_max = np.min([TX_CONFIG['voltage_max'], np.min(np.hstack((np.inf, [MUX_CONFIG[i].pop('voltage_max', np.inf) for i in MUX_CONFIG.keys()])))])
voltage_min = RX_CONFIG['voltage_min']


def elapsed_seconds(start_time):
    lap = datetime.datetime.utcnow() - start_time
    return lap.total_seconds()


class OhmPiHardware:
    def __init__(self, **kwargs):
        # OhmPiHardware initialization
        self.exec_logger = kwargs.pop('exec_logger', None)
        self.exec_logger.event(f'OhmPiHardware\tinit\tbegin\t{datetime.datetime.utcnow()}')
        if self.exec_logger is None:
            self.exec_logger = create_stdout_logger('exec_hw')
        self.data_logger = kwargs.pop('exec_logger', None)
        if self.data_logger is None:
            self.data_logger = create_stdout_logger('data_hw')
        self.soh_logger = kwargs.pop('soh_logger', None)
        if self.soh_logger is None:
            self.soh_logger = create_stdout_logger('soh_hw')
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
        HARDWARE_CONFIG['rx'].update(**HARDWARE_CONFIG['rx'])
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
        if isinstance(HARDWARE_CONFIG['pwr']['ctl'], dict):
            ctl_mod = HARDWARE_CONFIG['pwr']['ctl'].pop('model', self.ctl)
            if isinstance(ctl_mod, str):
                ctl_mod = importlib.import_module(f'ohmpi.hardware_components.{ctl_mod}')
            HARDWARE_CONFIG['pwr']['ctl'] = ctl_mod.Ctl(**HARDWARE_CONFIG['pwr']['ctl'])
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
                update_dict(self._cabling, {k: (mux_id, k[0])})

        # Complete OhmPiHardware initialization
        self.readings = np.array([])  # time series of acquired data
        self._start_time = None  # time of the beginning of a readings acquisition
        self._pulse = 0  # pulse number
        self.exec_logger.event(f'OhmPiHardware\tinit\tend\t{datetime.datetime.utcnow()}')

    def _clear_values(self):
        self.readings = np.array([])
        self._start_time = None
        self._pulse = 0

    def _gain_auto(self, polarities=(1, -1)):  # TODO: improve _gain_auto
        self.exec_logger.event(f'OhmPiHardware\ttx_rx_gain_auto\tbegin\t{datetime.datetime.utcnow()}')
        current, voltage = 0., 0.
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
    def pulses(self):
        pulses = {}
        for i in np.unique(self.readings[:, 1]):
            r = self.readings[self.readings[:, 1] == i, :]
            assert np.all(np.isclose(r[:, 2], r[0, 2]))  # Polarity cannot change within a pulse
            # TODO: check how to generalize in case of multi-channel RX
            pulses.update({i: {'polarity': int(r[0, 2]), 'iab': r[:, 3], 'vmn': r[:, 4]}})
        return pulses

    def _read_values(self, sampling_rate=None, append=False):  # noqa
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
            time.sleep(np.max([self.rx._latency, self.tx._latency])) # if continuous mode
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

    def _compute_tx_volt(self, pulse_duration=0.1, strategy='vmax', tx_volt=5.,
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

        vab_max = np.abs(vab_max)
        vmn_min = np.abs(vmn_min)
        vab = np.min([np.abs(tx_volt), vab_max])
        self.tx.turn_on()
        if 1. / self.rx.sampling_rate > pulse_duration:
            sampling_rate = 1. / pulse_duration  # TODO: check this...
        else:
            sampling_rate = self.tx.sampling_rate
        self._vab_pulse(vab=vab, duration=pulse_duration, sampling_rate=sampling_rate)  # TODO: use a square wave pulse?
        vmn = np.mean(self.readings[:, 4])
        iab = np.mean(self.readings[:, 3])
        # if np.abs(vmn) is too small (smaller than voltage_min), strategy is not constant and vab < vab_max ,
        # then we could call _compute_tx_volt with a tx_volt increased to np.min([vab_max, tx_volt*2.]) for example
        if strategy == 'vmax':
            # implement different strategies
            if vab < vab_max and iab < current_max:
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
        rab = (np.abs(vab) * 1000.) / iab
        self.exec_logger.debug(f'RAB = {rab:.2f} Ohms')
        if vmn < 0:
            polarity = -1  # TODO: check if we really need to return polarity
        else:
            polarity = 1
        return vab, polarity, rab

    def _plot_readings(self, save_fig=False):
        # Plot graphs
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
        ax[4].plot(self.readings[v, 0], np.ones_like(self.readings[v,0]) * self.sp, '-k', marker='.', label='SP [mV]')
        ax[4].set_ylabel('SP [mV]')
        # fig.legend()
        if save_fig:
            fig.savefig(f'figures/test.png')
        else:
            plt.show()

    def calibrate_rx_bias(self):
        self.rx._bias += (np.mean(self.readings[self.readings[:, 2] == 1, 4])
                          + np.mean(self.readings[self.readings[:, 2] == -1, 4])) / 2.

    def vab_square_wave(self, vab, cycle_duration, sampling_rate=None, cycles=3, polarity=1, duty_cycle=1.,
                        append=False):
        self.exec_logger.event(f'OhmPiHardware\tvab_square_wave\tbegin\t{datetime.datetime.utcnow()}')
        self._gain_auto()
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

    def _vab_pulse(self, vab, duration, sampling_rate=None, polarity=1, append=False):
        """ Gets VMN and IAB from a single voltage pulse
        """
        #self.tx.polarity = polarity
        if sampling_rate is None:
            sampling_rate = RX_CONFIG['sampling_rate']
        if self.tx.pwr.voltage_adjustable:
            self.tx.pwr.voltage = vab
        else:
            vab = self.tx.pwr.voltage
        # reads current and voltage during the pulse
        injection = Thread(target=self._inject, kwargs={'injection_duration': duration, 'polarity': polarity})
        readings = Thread(target=self._read_values, kwargs={'sampling_rate': sampling_rate, 'append': append})
        readings.start()
        injection.start()
        readings.join()
        injection.join()
        self.tx.polarity = 0   #TODO: is this necessary?

    def _vab_pulses(self, vab, durations, sampling_rate, polarities=None, append=False):
        n_pulses = len(durations)
        self.exec_logger.debug(f'n_pulses: {n_pulses}')
        if sampling_rate is None:
            sampling_rate = RX_CONFIG['sampling_rate']
        if polarities is not None:
            assert len(polarities) == n_pulses
        else:
            polarities = [-int(self.tx.polarity * np.heaviside(i % 2, -1.)) for i in range(n_pulses)]
        if not append:
            self._clear_values()
        for i in range(n_pulses):
            self._vab_pulse(self, duration=durations[i], sampling_rate=sampling_rate, polarity=polarities[i],
                            append=True)

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
                    mux_workers[idx] = Thread(target=self.mux_boards[mux].switch, kwargs=kwargs)
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

    def test_mux(self, channel=None, activation_time=1.0):
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
            for c in self._cabling.keys():
                self.exec_logger.info(f'Testing electrode {c[0]} with role {c[1]}.')
                self.switch_mux(electrodes=[c[0]], roles=[c[1]], state='on')
                time.sleep(activation_time)
                self.switch_mux(electrodes=[c[0]], roles=[c[1]], state='off')
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
