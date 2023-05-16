from abc import ABC, abstractmethod

import numpy as np
from ohmpi.logging_setup import create_stdout_logger
import time
from threading import Barrier


class CtlAbstract(ABC):
    def __init__(self, **kwargs):
        self.board_name = kwargs.pop('board_name', 'unknown CTL hardware')
        self.bus = None # TODO: allow for several buses
        self.exec_logger = kwargs.pop('exec_logger', None)
        if self.exec_logger is None:
            self.exec_logger = create_stdout_logger('exec_ctl')
        self.soh_logger = kwargs.pop('soh_logger', None)
        if self.soh_logger is None:
            self.soh_logger = create_stdout_logger('soh_ctl')
        self.exec_logger.debug(f'{self.board_name} Ctl initialization')
        self._cpu_temp_available = False
        self.max_cpu_temp = np.inf

    @property
    def cpu_temperature(self):
        if not self._cpu_temp_available:
            self.exec_logger.warning(f'CPU temperature reading is not available for {self.board_name}')
            cpu_temp = np.nan
        else:
            cpu_temp = self._cpu_temp
            if cpu_temp > self.max_cpu_temp:
                self.soh_logger.warning(f'CPU temperature of {self.board_name} is over the limit!')
        return cpu_temp

    @property
    @abstractmethod
    def _cpu_temp(self):
        pass

class PwrAbstract(ABC):
    def __init__(self, **kwargs):
        self.board_name = kwargs.pop('board_name', 'unknown PWR hardware')
        self.exec_logger = kwargs.pop('exec_logger', None)
        if self.exec_logger is None:
            self.exec_logger = create_stdout_logger('exec_mux')
        self.soh_logger = kwargs.pop('soh_logger', None)
        if self.soh_logger is None:
            self.soh_logger = create_stdout_logger('soh_mux')
        self.voltage_adjustable = kwargs.pop('voltage_adjustable', False)
        self._voltage = np.nan
        self._current_adjustable = kwargs.pop('current_adjustable', False)
        self._current = np.nan
        self._state = 'off'

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
        self.exec_logger.debug(f'Switching {self.board_name} off')
        self._state = 'off'

    @abstractmethod
    def turn_on(self):
        self.exec_logger.debug(f'Switching {self.board_name} on')
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
            self.exec_logger.warning(f'Voltage cannot be set on {self.board_name}...')
        else:
            # add actions to set the DPS voltage
            self._voltage = value

class MuxAbstract(ABC):
    def __init__(self, **kwargs):
        self.board_name = kwargs.pop('board_name', 'unknown MUX hardware')
        self.exec_logger = kwargs.pop('exec_logger', None)
        if self.exec_logger is None:
            self.exec_logger = create_stdout_logger('exec_mux')
        self.soh_logger = kwargs.pop('soh_logger', None)
        if self.soh_logger is None:
            self.soh_logger = create_stdout_logger('soh_mux')
        self.board_id = kwargs.pop('id', None)
        if self.board_id is None:
            self.exec_logger.error(f'MUX {self.board_name} should have an id !')
        self.exec_logger.debug(f'MUX {self.board_id} ({self.board_name}) initialization')
        self.ctl = kwargs.pop('ctl', None)
        cabling = kwargs.pop('cabling', None)
        self.cabling = {}
        if cabling is not None:
            for k, v in cabling.items():
                if v[0]==self.board_id:
                    self.cabling.update({k: (v[1], k[1])})
        self.exec_logger.debug(f'{self.board_id} cabling: {self.cabling}')
        self.addresses = kwargs.pop('addresses', None)
        self._barrier = kwargs.pop('barrier', Barrier(1))

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

    def switch(self, elec_dict=None, state='off'): # TODO: generalize for other roles
        """Switch a given list of electrodes with different roles.
        Electrodes with a value of 0 will be ignored.

        Parameters
        ----------
        elec_dict : dictionary, optional
            Dictionary of the form: {role: [list of electrodes]}.
        state : str, optional
            Either 'on' or 'off'.
        """
        status = True
        if elec_dict is not None:
            self.exec_logger.debug(f'Switching {self.board_name} ')
            # check to prevent A == B (SHORT-CIRCUIT)
            if 'A' in elec_dict.keys() and 'B' in elec_dict.keys():
                out = np.in1d(elec_dict['A'], elec_dict['B'])
                if out.any() and state=='on':  # noqa
                    self.exec_logger.error('Trying to switch on some electrodes with both A and B roles. '
                                           'This would create a short-circuit! Switching aborted.')
                    status = False
                    return status

            # check that none of M or N are the same as A or B
            # as to prevent burning the MN part which cannot take
            # the full voltage of the DPS
            if 'A' in elec_dict.keys() and 'B' in elec_dict.keys() and 'M' in elec_dict.keys() and 'N' in elec_dict.keys():
                if (np.in1d(elec_dict['M'], elec_dict['A']).any()  # noqa
                        or np.in1d(elec_dict['M'], elec_dict['B']).any()  # noqa
                        or np.in1d(elec_dict['N'], elec_dict['A']).any()  # noqa
                        or np.in1d(elec_dict['N'], elec_dict['B']).any()) and state=='on':  # noqa
                    self.exec_logger.error('Trying to switch on some electrodes with both M or N role and A or B role. '
                                           'This could create an over-voltage in the RX! Switching aborted.')
                    status = False
                    return status

            # if all ok, then wait for the barrier to open, then switch the electrodes
            self.exec_logger.debug(f'{self.board_id} waiting to switch.')
            self.barrier.wait()
            for role in elec_dict:
                for elec in elec_dict[role]:
                    if elec > 0:  # Is this condition related to electrodes to infinity?
                        if (elec, role) in self.cabling.keys():
                            self.switch_one(elec, role, state)
                            status &= True
                        else:
                            self.exec_logger.warning(f'{self.board_id} skipping switching {(elec, role)} because it '
                                                   f'is not in board cabling.')
                            status = False
            self.exec_logger.debug(f'{self.board_id} switching done.')
        else:
            self.exec_logger.warning(f'Missing argument for {self.board_name}.switch: elec_dict is None.')
            status = False
        return status

    @abstractmethod
    def switch_one(self, elec=None, role=None, state=None):
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
        self.exec_logger.debug(f'Starting {self.board_name} test...')
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
        self.board_name = kwargs.pop('board_name', 'unknown TX hardware')
        inj_time = kwargs.pop('inj_time', 1.)
        self.exec_logger = kwargs.pop('exec_logger', None)
        if self.exec_logger is None:
            self.exec_logger = create_stdout_logger('exec_tx')
        self.soh_logger = kwargs.pop('soh_logger', None)
        if self.soh_logger is None:
            self.soh_logger = create_stdout_logger('soh_tx')
        self.ctl = kwargs.pop('ctl', None)
        self.pwr = kwargs.pop('pwr', None)
        self._polarity = 0
        self._inj_time = None
        self._adc_gain = 1.
        self.inj_time = inj_time
        self.exec_logger.debug(f'{self.board_name} TX initialization')

    @property
    def adc_gain(self):
        return self._adc_gain

    @adc_gain.setter
    def adc_gain(self, value):
        self._adc_gain = value
        self.exec_logger.debug(f'Setting TX ADC gain to {value}')

    @abstractmethod
    def adc_gain_auto(self):
        pass

    @abstractmethod
    def current_pulse(self, **kwargs):
        pass

    @abstractmethod
    def inject(self, polarity=1, inj_time=None):
        assert polarity in [-1,0,1]
        if inj_time is None:
            inj_time = self._inj_time
        if np.abs(polarity) > 0:
            self.pwr.turn_on()
            time.sleep(inj_time)
            self.pwr.turn_off()
        else:
            self.pwr.turn_off()
            time.sleep(inj_time)

    @property
    def inj_time(self):
        return self._inj_time

    @inj_time.setter
    def inj_time(self, value):
        assert isinstance(value, float)
        self._inj_time = value

    @property
    def polarity(self):
        return self._polarity

    @polarity.setter
    @abstractmethod
    def polarity(self, polarity):
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
            length = self.inj_time
        self.pwr.voltage = voltage
        self.exec_logger.debug(f'Voltage pulse of {polarity * self.pwr.voltage:.3f} V for {length:.3f} s')
        self.inject(polarity=polarity, inj_time=length)


class RxAbstract(ABC):
    def __init__(self, **kwargs):
        self.exec_logger = kwargs.pop('exec_logger', None)
        if self.exec_logger is None:
            self.exec_logger = create_stdout_logger('exec_rx')
        self.soh_logger = kwargs.pop('soh_logger', None)
        if self.soh_logger is None:
            self.soh_logger = create_stdout_logger('soh_rx')
        self.ctl = kwargs.pop('ctl', None)
        self.board_name = kwargs.pop('board_name', 'unknown RX hardware')
        self._sampling_rate = kwargs.pop('sampling_rate', 1)
        self.exec_logger.debug(f'{self.board_name} RX initialization')
        self._adc_gain = 1.
        self._max_sampling_rate = np.inf

    @property
    def adc_gain(self):
        return self._adc_gain


    @adc_gain.setter
    def adc_gain(self, value):
        self._adc_gain = value
        self.exec_logger.debug(f'Setting RX ADC gain to {value}')

    @abstractmethod
    def adc_gain_auto(self):
        pass

    @property
    def sampling_rate(self):
        return self._sampling_rate

    @sampling_rate.setter
    def sampling_rate(self, value):
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