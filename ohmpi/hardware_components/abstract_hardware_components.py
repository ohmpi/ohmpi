from abc import ABC, abstractmethod
import numpy as np
from ohmpi.logging_setup import create_stdout_logger
import time
from threading import Event, Barrier, BrokenBarrierError


class CtlAbstract(ABC):
    def __init__(self, **kwargs):
        self.model = kwargs.pop('model', 'unknown CTL hardware')
        self.interfaces = None
        self.exec_logger = kwargs.pop('exec_logger', None)
        if self.exec_logger is None:
            self.exec_logger = create_stdout_logger('exec_ctl')
        self.soh_logger = kwargs.pop('soh_logger', None)
        if self.soh_logger is None:
            self.soh_logger = create_stdout_logger('soh_ctl')
        self.exec_logger.debug(f'{self.model} Ctl initialization')
        self._cpu_temp_available = False
        self.max_cpu_temp = np.inf
        self.connection = kwargs.pop('connection', None)

    @property
    def cpu_temperature(self):
        if not self._cpu_temp_available:
            self.exec_logger.warning(f'CPU temperature reading is not available for {self.model}')
            cpu_temp = np.nan
        else:
            cpu_temp = self._cpu_temp
            if cpu_temp > self.max_cpu_temp:
                self.soh_logger.warning(f'CPU temperature of {self.model} is over the limit!')
        return cpu_temp

    @property
    @abstractmethod
    def _cpu_temp(self):
        pass


class PwrAbstract(ABC):
    def __init__(self, **kwargs):
        self.model = kwargs.pop('model', 'unknown PWR hardware')
        self.exec_logger = kwargs.pop('exec_logger', None)
        if self.exec_logger is None:
            self.exec_logger = create_stdout_logger('exec_mux')
        self.soh_logger = kwargs.pop('soh_logger', None)
        if self.soh_logger is None:
            self.soh_logger = create_stdout_logger('soh_mux')
        self.voltage_adjustable = kwargs.pop('voltage_adjustable', False)
        self._voltage = np.nan
        self.current_adjustable = kwargs.pop('current_adjustable', False)
        self._current = np.nan
        self._state = 'off'
        self._current_min = kwargs.pop('current_min', 0.)
        self._current_max = kwargs.pop('current_max', 0.)
        self._voltage_min = kwargs.pop('voltage_min', 0.)
        self._voltage_max = kwargs.pop('voltage_max', 0.)
        self.connection = kwargs.pop('connection', None)
        self._battery_voltage = np.nan

    @property
    @abstractmethod
    def current(self):
        # add actions to read the DPS current
        return self._current

    @current.setter
    @abstractmethod
    def current(self, value, **kwargs):
        # add actions to set the DPS current
        pass

    @abstractmethod
    def turn_off(self):
        self.exec_logger.debug(f'Switching {self.model} off')
        self._state = 'off'

    @abstractmethod
    def turn_on(self):
        self.exec_logger.debug(f'Switching {self.model} on')
        self._state = 'on'

    @property
    @abstractmethod
    def voltage(self):
        # add actions to read the DPS voltage
        return self._voltage

    @voltage.setter
    @abstractmethod
    def voltage(self, value):
        assert isinstance(value, float)
        if not self.voltage_adjustable:
            self.exec_logger.debug(f'Voltage cannot be set on {self.model}...')
        else:
            assert self._voltage_min <= value <= self._voltage_max
            # add actions to set the DPS voltage
            self._voltage = value

    def battery_voltage(self):
        # add actions to read the DPS voltage
        self.exec_logger.debug(f'Battery voltage cannot be read on {self.model}...')
        return self._battery_voltage

    def reset_voltage(self):
        if not self.voltage_adjustable:
            self.exec_logger.debug(f'Voltage cannot be set on {self.model}...')
        else:
            self.voltage = self._voltage_min

class MuxAbstract(ABC):
    def __init__(self, **kwargs):
        self.model = kwargs.pop('model', 'unknown MUX hardware')
        self.exec_logger = kwargs.pop('exec_logger', create_stdout_logger('exec_mux'))
        self.soh_logger = kwargs.pop('soh_logger', create_stdout_logger('soh_mux'))
        self.board_id = kwargs.pop('id', None)
        if self.board_id is None:
            self.exec_logger.error(f'MUX {self.model} should have an id !')
        self.exec_logger.debug(f'MUX {self.model}: {self.board_id} initialization')
        self.connection = kwargs.pop('connection', None)
        cabling = kwargs.pop('cabling', None)
        self.cabling = {}
        if cabling is not None:
            for k, v in cabling.items():
                if v[0] == self.board_id:
                    self.cabling.update({k: (v[1], k[1])})
        self.exec_logger.debug(f'{self.board_id} cabling: {self.cabling}')
        self.addresses = kwargs.pop('addresses', None)
        self._barrier = kwargs.pop('barrier', Barrier(1))
        self._activation_delay = kwargs.pop('activation_delay', 0.)  # in s
        self._release_delay = kwargs.pop('release_delay', 0.)  # in s

    @abstractmethod
    def _get_addresses(self):
        pass

    @property
    def barrier(self):
        return self._barrier

    @barrier.setter
    def barrier(self, value):
        assert isinstance(value, Barrier)
        self._barrier = value

    @abstractmethod
    def reset(self):
        pass

    def switch(self, elec_dict=None, state='off', bypass_check=False):  # TODO: generalize for other roles
        """Switch a given list of electrodes with different roles.
        Electrodes with a value of 0 will be ignored.

        Parameters
        ----------
        elec_dict : dictionary, optional
            Dictionary of the form: {role: [list of electrodes]}.
        state : str, optional
            Either 'on' or 'off'.
        bypass_check: bool, optional
            Bypasses checks for A==M or A==M or B==M or B==N (i.e. used for rs-check)
        """
        status = True
        if elec_dict is not None:
            self.exec_logger.debug(f'Switching {self.model} ')
            # check to prevent A == B (SHORT-CIRCUIT)
            if 'A' in elec_dict.keys() and 'B' in elec_dict.keys():
                out = np.in1d(elec_dict['A'], elec_dict['B'])
                if out.any() and state == 'on':  # noqa
                    self.exec_logger.error('Trying to switch on some electrodes with both A and B roles. '
                                           'This would create a short-circuit! Switching aborted.')
                    status = False
                    return status

            # check that none of M or N are the same as A or B
            # as to prevent burning the MN part which cannot take
            # the full voltage of the DPS
            if 'A' in elec_dict.keys() and 'B' in elec_dict.keys() and 'M' in elec_dict.keys() \
                    and 'N' in elec_dict.keys():
                if bypass_check:
                    self.exec_logger.debug(f'Bypassing :{bypass_check}')
                elif (np.in1d(elec_dict['M'], elec_dict['A']).any()  # noqa
                        or np.in1d(elec_dict['M'], elec_dict['B']).any()  # noqa
                        or np.in1d(elec_dict['N'], elec_dict['A']).any()  # noqa
                        or np.in1d(elec_dict['N'], elec_dict['B']).any()) and state=='on':  # noqa
                    self.exec_logger.error('Trying to switch on some electrodes with both M or N role and A or B role. '
                                           'This could create an over-voltage in the RX! Switching aborted.')
                    self.barrier.abort()
                    status = False
                    return status

            # if all ok, then wait for the barrier to open, then switch the electrodes
            self.exec_logger.debug(f'{self.board_id} waiting to switch.')
            try:
                self.barrier.wait()
                for role in elec_dict:
                    for elec in elec_dict[role]:
                        if elec > 0:  # Is this condition related to electrodes to infinity?
                            if (elec, role) in self.cabling.keys():
                                self.switch_one(elec, role, state)
                                status &= True
                            else:
                                self.exec_logger.debug(f'{self.board_id} skipping switching {(elec, role)} because it '
                                                       f'is not in board cabling.')
                                status = False
                self.exec_logger.debug(f'{self.board_id} switching done.')
            except BrokenBarrierError:
                self.exec_logger.debug(f'Barrier error {self.board_id} switching aborted.')
                status = False
        else:
            self.exec_logger.warning(f'Missing argument for {self.model}.switch: elec_dict is None.')
            status = False
        if state == 'on':
            time.sleep(self._activation_delay)
        elif state == 'off':
            time.sleep(self._release_delay)
        return status

    @abstractmethod
    def switch_one(self, elec=None, role=None, state=None):
        """Switches one single relay.

        Parameters
        ----------
        elec :
        role :
        state : str, optional
            Either 'on' or 'off'.
        """
        self.exec_logger.debug(f'switching {state} electrode {elec} with role {role}')

    def test(self, elec_dict, activation_time=1.):
        """Method to test the multiplexer.

        Parameters
        ----------
        elec_dict : dictionary, optional
            Dictionary of the form: {role: [list of electrodes]}.
        activation_time : float, optional
            Time in seconds during which the relays are activated.
        """
        self.exec_logger.debug(f'Starting {self.model} test...')
        self.reset()

        for role in elec_dict.keys():
            for elec in elec_dict[role]:
                self.switch_one(elec, role, 'on')
                time.sleep(activation_time)
                self.switch_one(elec, role, 'off')
                time.sleep(activation_time)
        self.exec_logger.debug('Test finished.')


class TxAbstract(ABC):
    def __init__(self, **kwargs):
        self.model = kwargs.pop('model', 'unknown TX hardware')
        injection_duration = kwargs.pop('injection_duration', 1.)
        self.exec_logger = kwargs.pop('exec_logger', None)
        if self.exec_logger is None:
            self.exec_logger = create_stdout_logger('exec_tx')
        self.soh_logger = kwargs.pop('soh_logger', None)
        if self.soh_logger is None:
            self.soh_logger = create_stdout_logger('soh_tx')
        self.connection = kwargs.pop('connection', None)
        self.pwr = kwargs.pop('pwr', None)
        self._polarity = 0
        self._injection_duration = None
        self._adc_gain = 1.
        self.injection_duration = injection_duration
        self._latency = kwargs.pop('latency', 0.)
        self.tx_sync = kwargs.pop('tx_sync', Event())
        self.exec_logger.debug(f'{self.model} TX initialization')

    @property
    def adc_gain(self):
        return self._adc_gain

    @adc_gain.setter
    def adc_gain(self, value):
        """
        Set gain on RX ADC
        Parameters
        ----------
        value: float
        """
        self._adc_gain = value
        self.exec_logger.debug(f'Setting TX ADC gain to {value}')

    @abstractmethod
    def _adc_gain_auto(self):
        pass

    @abstractmethod
    def current_pulse(self, **kwargs):
        pass

    @abstractmethod
    def inject(self, polarity=1, injection_duration=None, switch_pwr=False):
        """
        Abstract method to define injection
        Parameters
        ----------
        polarity: int, default 1
            Injection polarity, can be eiter  1, 0 or -1
        injection_duration: float, default None
            Injection duration in seconds
        switch_pwr: bool
            switches on and off tx.pwr
        """
        assert polarity in [-1, 0, 1]
        if injection_duration is None:
            injection_duration = self._injection_duration
        if np.abs(polarity) > 0:
            if switch_pwr:
                self.pwr.turn_on()
            self.tx_sync.set()
            time.sleep(injection_duration)
            self.tx_sync.clear()
            if switch_pwr:
                self.pwr.turn_off()
        else:
            self.tx_sync.set()
            if switch_pwr:
                self.pwr.turn_off()
            time.sleep(injection_duration)
            self.tx_sync.clear()

    @property
    def injection_duration(self):
        return self._injection_duration

    @injection_duration.setter
    def injection_duration(self, value):
        assert isinstance(value, float)
        assert value > 0.
        self._injection_duration = value

    @property
    def polarity(self):
        return self._polarity

    @polarity.setter
    @abstractmethod
    def polarity(self, polarity):
        """
        Sets polarity value
        Parameters
        ----------
        polarity: int
            Either -1, 0 or 1.
        """
        assert polarity in [-1, 0, 1]
        self._polarity = polarity

    @property
    @abstractmethod
    def tx_bat(self):
        pass

    def voltage_pulse(self, voltage=0., length=None, polarity=1):
        """ Generates a square voltage pulse

        Parameters
        ----------
        voltage: float, optional
            Voltage to apply in volts, tx_v_def is applied if omitted.
        length: float, optional
            Length of the pulse in seconds
        polarity: 1,0,-1
            Polarity of the pulse
        """
        if length is None:
            length = self.injection_duration
        self.pwr.voltage = voltage
        self.exec_logger.debug(f'Voltage pulse of {polarity * self.pwr.voltage:.3f} V for {length:.3f} s')
        self.inject(polarity=polarity, injection_duration=length)

    def switch_pwr(self):
        self.exec_logger.debug(f'Power source cannot be switched on or off on {self.model}')

class RxAbstract(ABC):
    def __init__(self, **kwargs):
        self.exec_logger = kwargs.pop('exec_logger', None)
        if self.exec_logger is None:
            self.exec_logger = create_stdout_logger('exec_rx')
        self.soh_logger = kwargs.pop('soh_logger', None)
        if self.soh_logger is None:
            self.soh_logger = create_stdout_logger('soh_rx')
        self.connection = kwargs.pop('connection', None)
        self.model = kwargs.pop('model', 'unknown RX hardware')
        self._sampling_rate = kwargs.pop('sampling_rate', 1)  # ms
        self.exec_logger.debug(f'{self.model} RX initialization')
        self._voltage_max = kwargs.pop('voltage_max', 0.)
        self._adc_gain = 1.
        self._max_sampling_rate = np.inf
        self._latency = kwargs.pop('latency', 0.)
        self._bias = kwargs.pop('bias', 0.)
        self._vmn_hardware_offset = kwargs.pop('vmn_hardware_offset', 0.)

    @property
    def adc_gain(self):
        return self._adc_gain

    @adc_gain.setter
    def adc_gain(self, value):
        """
        Sets gain on RX ADC
        Parameters
        ----------
        value: float
        """
        self._adc_gain = value
        self.exec_logger.debug(f'Setting RX ADC gain to {value}')

    @abstractmethod
    def _adc_gain_auto(self):
        pass

    @property
    def sampling_rate(self):
        return self._sampling_rate

    @sampling_rate.setter
    def sampling_rate(self, value):
        """
        Sets sampling rate
        Parameters
        ----------
        value: float, in Hz
        """
        assert value > 0.
        if value > self._max_sampling_rate:
            self.exec_logger.warning(f'{self} maximum sampling rate is {self._max_sampling_rate}. '
                                     f'Setting sampling rate to the highest allowed value.')
            value = self._max_sampling_rate
        self._sampling_rate = value
        self.exec_logger.debug(f'Sampling rate set to {value}')

    @property
    @abstractmethod
    def voltage(self):
        """ Gets the voltage VMN in Volts
        """
        pass
