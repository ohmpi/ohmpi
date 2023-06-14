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
from threading import Thread, Event, Barrier

# Define the default controller, a distinct controller could be defined for each tx, rx or mux board
# when using a distinct controller, the specific controller definition must be included in the component configuration
ctl_module = importlib.import_module(f'ohmpi.hardware_components.{HARDWARE_CONFIG["ctl"]["model"]}')
pwr_module = importlib.import_module(f'ohmpi.hardware_components.{HARDWARE_CONFIG["pwr"]["model"]}')
tx_module = importlib.import_module(f'ohmpi.hardware_components.{HARDWARE_CONFIG["tx"]["model"]}')
rx_module = importlib.import_module(f'ohmpi.hardware_components.{HARDWARE_CONFIG["rx"]["model"]}')
MUX_CONFIG = {}
# mux_boards = []

for mux_id, mux_config in HARDWARE_CONFIG['mux']['boards'].items():
    mux_module = importlib.import_module(f'ohmpi.hardware_components.{mux_config["model"]}')
    MUX_CONFIG[mux_id] = mux_module.MUX_CONFIG
    MUX_CONFIG[mux_id].update(mux_config)
    MUX_CONFIG[mux_id].update({'id': mux_id})
    # mux_boards.append(mux_id)

TX_CONFIG = tx_module.TX_CONFIG
RX_CONFIG = rx_module.RX_CONFIG

current_max = np.min([TX_CONFIG['current_max'], np.min([MUX_CONFIG[i].pop('current_max', np.inf) for i in MUX_CONFIG.keys()])])
voltage_max = np.min([TX_CONFIG['voltage_max'], np.min([MUX_CONFIG[i].pop('voltage_max', np.inf) for i in MUX_CONFIG.keys()])])
voltage_min = RX_CONFIG['voltage_min']


def elapsed_seconds(start_time):
    lap = datetime.datetime.utcnow() - start_time
    return lap.total_seconds()


class OhmPiHardware:
    def __init__(self, **kwargs):
        self.exec_logger = kwargs.pop('exec_logger', None)
        if self.exec_logger is None:
            self.exec_logger = create_stdout_logger('exec_hw')
        self.data_logger = kwargs.pop('exec_logger', None)
        if self.data_logger is None:
            self.data_logger = create_stdout_logger('data_hw')
        self.soh_logger = kwargs.pop('soh_logger', None)
        if self.soh_logger is None:
            self.soh_logger = create_stdout_logger('soh_hw')
        self.tx_sync = Event()
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

        HARDWARE_CONFIG['rx'].pop('model')
        HARDWARE_CONFIG['rx'].update(**HARDWARE_CONFIG['rx'])
        HARDWARE_CONFIG['rx'].update({'ctl': HARDWARE_CONFIG['rx'].pop('ctl', self.ctl)})
        if isinstance(HARDWARE_CONFIG['rx']['ctl'], dict):
            ctl_mod = HARDWARE_CONFIG['rx']['ctl'].pop('model', self.ctl)
            if isinstance(ctl_mod, str):
                ctl_mod = importlib.import_module(f'ohmpi.hardware_components.{ctl_mod}')
            HARDWARE_CONFIG['rx']['ctl'] = ctl_mod.Ctl(**HARDWARE_CONFIG['rx']['ctl'])
        HARDWARE_CONFIG['rx'].update({'exec_logger': self.exec_logger, 'data_logger': self.data_logger,
                                       'soh_logger': self.soh_logger})
        self.rx = kwargs.pop('rx', rx_module.Rx(**HARDWARE_CONFIG['rx']))
        HARDWARE_CONFIG['pwr'].pop('model')
        HARDWARE_CONFIG['pwr'].update(**HARDWARE_CONFIG['pwr'])
        HARDWARE_CONFIG['pwr'].update({'ctl': self.ctl})
        HARDWARE_CONFIG['pwr'].update({'exec_logger': self.exec_logger, 'data_logger': self.data_logger,
                                      'soh_logger': self.soh_logger})
        self.pwr = kwargs.pop('pwr', pwr_module.Pwr(**HARDWARE_CONFIG['pwr']))
        HARDWARE_CONFIG['tx'].pop('model')
        HARDWARE_CONFIG['tx'].update(**HARDWARE_CONFIG['tx'])
        HARDWARE_CONFIG['tx'].update({'ctl': self.ctl})
        HARDWARE_CONFIG['tx'].update({'exec_logger': self.exec_logger, 'data_logger': self.data_logger,
                                      'soh_logger': self.soh_logger})
        self.tx = kwargs.pop('tx', tx_module.Tx(**HARDWARE_CONFIG['tx']))
        if isinstance(self.tx, dict):
            self.tx = tx_module.Tx(**self.tx)
        self.tx.pwr = self.pwr
        self._cabling = kwargs.pop('cabling', {})
        self.mux_boards = {}
        for mux_id, mux_config in HARDWARE_CONFIG['mux']['boards'].items():
            mux_config.update({'exec_logger': self.exec_logger, 'data_logger': self.data_logger,
                               'soh_logger': self.soh_logger})
            mux_config.update(**HARDWARE_CONFIG['mux']['boards'][mux_id])
            mux_module = importlib.import_module(f'ohmpi.hardware_components.{mux_config["model"]}')
            ctl = mux_config.pop('ctl', self.ctl)
            if isinstance(ctl, dict):
                mux_ctl_module = importlib.import_module(f'ohmpi.hardware_components.{mux_config["ctl"]["model"]}')
                ctl = mux_ctl_module.Ctl(**self.ctl)
            mux_config.update({'ctl': ctl})
            assert issubclass(type(mux_config['ctl']), CtlAbstract)

            mux_config['id'] = mux_id

            self.mux_boards[mux_id] = mux_module.Mux(**mux_config)

        # self.mux_boards = kwargs.pop('mux', {'mux_1': mux_module.Mux(id='mux_1',
        #                                                              exec_logger=self.exec_logger,
        #                                                              data_logger=self.data_logger,
        #                                                              soh_logger=self.soh_logger,
        #                                                              ctl=self.ctl,
        #                                                              cabling=self._cabling)})

        self.mux_barrier = Barrier(len(self.mux_boards) + 1)
        self._cabling = {}
        for mux_id, mux in self.mux_boards.items():
            mux.barrier = self.mux_barrier
            for k, v in mux.cabling.items():
                update_dict(self._cabling, {k: (mux_id, k[0])})
        self.readings = np.array([])  # time series of acquired data
        self._start_time = None  # time of the beginning of a readings acquisition
        self._pulse = 0  # pulse number

    def _clear_values(self):
        self.readings = np.array([])
        self._start_time = None
        self._pulse = 0

    def _gain_auto(self):  # TODO: improve _gain_auto
        self.tx_sync.wait()
        self.tx.adc_gain_auto()
        self.rx.adc_gain_auto()

    def _inject(self, polarity=1, inj_time=None):  # TODO: deal with voltage or current pulse
        self.tx_sync.set()
        self.tx.voltage_pulse(length=inj_time, polarity=polarity)
        self.tx_sync.clear()

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

    def _read_values(self, sampling_rate, append=False):  # noqa
        if not append:
            self._clear_values()
            _readings = []
        else:
            _readings = self.readings.tolist()
        sample = 0
        self.tx_sync.wait()  #
        if not append or self._start_time is None:
            self._start_time = datetime.datetime.utcnow()
        while self.tx_sync.is_set():
            lap = datetime.datetime.utcnow()
            _readings.append([elapsed_seconds(self._start_time), self._pulse, self.tx.polarity, self.tx.current,
                              self.rx.voltage])
            sample += 1
            sleep_time = self._start_time + datetime.timedelta(seconds=sample * sampling_rate / 1000) - lap
            time.sleep(np.max([0., sleep_time.total_seconds()]))  # TODO set readings to nan if sleep time <0 and skip the sample (sample +=1)
        self.exec_logger.warning(f'pulse {self._pulse}: elapsed time {(lap-self._start_time).total_seconds()} s')  # TODO: Set to debug level
        self.readings = np.array(_readings)
        self._pulse += 1

    @property
    def sp(self):  # TODO: use a time window within pulses
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
            sp = np.mean(mean_vmn[np.ix_(polarity == 1)] - mean_vmn[np.ix_(polarity == -1)]) / 2
            return sp

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
        self.tx.turn_on()
        if self.rx.sampling_rate*1000 > best_tx_injtime:
            sampling_rate = best_tx_injtime  # TODO: check this...
        else:
            sampling_rate = self.tx.sampling_rate
        self._vab_pulse(vab=vab, length=best_tx_injtime, sampling_rate=sampling_rate)  # TODO: use a square wave pulse?
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

    def _plot_readings(self):
        # Plot graphs
        fig, ax = plt.subplots(nrows=2, sharex=True)
        ax[0].plot(self.readings[:, 0], self.readings[:, 3], '-r', marker='.', label='iab')
        ax[0].set_ylabel('Iab [mA]')
        ax[1].plot(self.readings[:, 0], self.readings[:, 2] * self.readings[:, 4], '-b', marker='.', label='vmn')
        ax[1].set_ylabel('Vmn [mV]')
        fig.legend()
        plt.show()

    def vab_square_wave(self, vab, cycle_length, sampling_rate=None, cycles=3, polarity=1, append=False):
        self.tx.polarity = polarity
        lengths = [cycle_length/2]*2*cycles
        # set gains automatically
        gain_auto = Thread(target=self._gain_auto)
        injection = Thread(target=self._inject, kwargs={'inj_time': 0.2, 'polarity': polarity})
        gain_auto.start()
        injection.start()
        self._vab_pulses(vab, lengths, sampling_rate, append=append)

    def _vab_pulse(self, vab, length, sampling_rate=None, polarity=1, append=False):
        """ Gets VMN and IAB from a single voltage pulse
        """
        self.tx.polarity = polarity
        if sampling_rate is None:
            sampling_rate = RX_CONFIG['sampling_rate']
        if self.tx.pwr.voltage_adjustable:
            self.tx.pwr.voltage = vab
        else:
            vab = self.tx.pwr.voltage
        # reads current and voltage during the pulse
        injection = Thread(target=self._inject, kwargs={'inj_time': length, 'polarity': polarity})
        readings = Thread(target=self._read_values, kwargs={'sampling_rate': sampling_rate, 'append': append})
        readings.start()
        injection.start()
        readings.join()
        injection.join()

    def _vab_pulses(self, vab, lengths, sampling_rate, polarities=None, append=False):
        n_pulses = len(lengths)
        if sampling_rate is None:
            sampling_rate = RX_CONFIG['sampling_rate']
        if polarities is not None:
            assert len(polarities) == n_pulses
        else:
            polarities = [-self.tx.polarity * np.heaviside(i % 2, -1.) for i in range(n_pulses)]
        if not append:
            self._clear_values()
        for i in range(n_pulses):
            self._vab_pulse(self, length=lengths[i], sampling_rate=sampling_rate, polarity=polarities[i],
                            append=True)

    def switch_mux(self, electrodes, roles=None, state='off'):
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
                    mux_workers[idx] = Thread(target=self.mux_boards[mux].switch, kwargs={'elec_dict': elec_dict,
                                                                                          'state': state})
                    mux_workers[idx].start()
                self.mux_barrier.wait()
                for mux_worker in mux_workers:
                    mux_worker.join()
        else:
            self.exec_logger.error(
                f'Unable to switch {state} electrodes: number of electrodes and number of roles do not match!')
            status = False
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
        for mux_id, mux in self.mux_boards.items():  # noqa
            self.exec_logger.debug(f'Resetting {mux_id}.')
            mux.reset()
