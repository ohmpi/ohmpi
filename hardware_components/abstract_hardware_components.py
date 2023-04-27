from abc import ABC, abstractmethod

import numpy as np
from OhmPi.logging_setup import create_stdout_logger
import time

class ControllerAbstract(ABC):
    def __init__(self, **kwargs):
        self.board_name = kwargs.pop('board_name', 'unknown Controller hardware')
        self.bus = None # TODO: allow for several buses
        self.exec_logger = kwargs.pop('exec_logger', None)
        if self.exec_logger is None:
            self.exec_logger = create_stdout_logger('exec_ctl')
        self.soh_logger = kwargs.pop('soh_logger', None)
        if self.soh_logger is None:
            self.soh_logger = create_stdout_logger('soh_ctl')
        self.exec_logger.debug(f'{self.board_name} Controller initialization')
        self._cpu_temp_available = False
        self.max_cpu_temp = np.inf
    @property
    def cpu_temperature(self):
        if not self._cpu_temp_available:
            self.exec_logger.warning(f'CPU temperature reading is not available for {self.board_name}')
            cpu_temp = np.nan
        else:
            cpu_temp = self._get_cpu_temp()
            if cpu_temp > self.max_cpu_temp:
                self.soh_logger.warning(f'CPU temperature of {self.board_name} is over the limit!')
        return cpu_temp

    @abstractmethod
    def _get_cpu_temp(self):
        pass

class MuxAbstract(ABC):
    def __init__(self, **kwargs):
        self.board_name = kwargs.pop('board_name', 'unknown MUX hardware')  # TODO: introduce MUX boards that are part of a MUX system (could be the same for RX boards that take part to an RX system (e.g. different channels)
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
        self.controller = kwargs.pop('controller', None)
        cabling = kwargs.pop('cabling', None)
        print(f'cabling: {cabling}')
        self._cabling = {}
        if cabling is not None:
            for k, v in cabling:
                if v[0]==self.board_id:
                    self._cabling.update({k: v[1]})
        self.addresses = kwargs.pop('addresses', None)

    @abstractmethod
    def _get_addresses(self):
        pass

    @abstractmethod
    def reset(self):
        pass

    def switch(self, elec_dict=None, state='on'):
        """Switch a given list of electrodes with different roles.
        Electrodes with a value of 0 will be ignored.

        Parameters
        ----------
        elec_dict : dictionary, optional
            Dictionary of the form: {role: [list of electrodes]}.
        state : str, optional
            Either 'on' or 'off'.
        """
        if elec_dict is not None:
            self.exec_logger.debug(f'Switching {self.board_name} ')
            # check to prevent A == B (SHORT-CIRCUIT)
            if 'A' in elec_dict.keys() and 'B' in elec_dict.keys():
                out = np.in1d(elec_dict['A'], elec_dict['B'])
                if out.any() and state=='on':
                    self.exec_logger.error('Trying to switch on some electrodes with both A and B roles. '
                                           'This would create a short-circuit! Switching aborted.')
                    return

            # check that none of M or N are the same as A or B
            # as to prevent burning the MN part which cannot take
            # the full voltage of the DPS
            if 'A' in elec_dict.keys() and 'B' in elec_dict.keys() and 'M' in elec_dict.keys() and 'N' in elec_dict.keys():
                if (np.in1d(elec_dict['M'], elec_dict['A']).any()
                        or np.in1d(elec_dict['M'], elec_dict['B']).any()
                        or np.in1d(elec_dict['N'], elec_dict['A']).any()
                        or np.in1d(elec_dict['N'], elec_dict['B']).any()) and state=='on':
                    self.exec_logger.error('Trying to switch on some electrodes with both M or N role and A or B role. '
                                           'This could create an over-voltage in the RX! Switching aborted.')
                    return

            # if all ok, then switch the electrodes
            for role in elec_dict:
                for elec in elec_dict[role]:
                    if elec > 0:
                        self.switch_one(elec, role, state)
        else:
            self.exec_logger.warning(f'Missing argument for {self.board_name}.switch: elec_dict is None.')

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
        polarity = kwargs.pop('polarity', 1)
        if polarity is None:
            polarity = 0
        self._polarity = polarity
        inj_time = kwargs.pop('inj_time', 1.)
        self.exec_logger = kwargs.pop('exec_logger', None)
        if self.exec_logger is None:
            self.exec_logger = create_stdout_logger('exec_tx')
        self.soh_logger = kwargs.pop('soh_logger', None)
        if self.soh_logger is None:
            self.soh_logger = create_stdout_logger('soh_tx')
        self.controller = kwargs.pop('controller', None)
        self._inj_time = None
        self._dps_state = 'off'
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

    @property
    @abstractmethod
    def current(self):
        # add actions to read the TX current and return it
        return None

    @current.setter
    @abstractmethod
    def current(self, value, **kwargs):
        # add actions to set the DPS current
        pass

    @abstractmethod
    def current_pulse(self, **kwargs):
        pass

    @abstractmethod
    def inject(self, state='on'):
        assert state in ['on', 'off']

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
    def polarity(self, value):
        assert value in [-1,0,1]
        self._polarity = value
        # add actions to set the polarity (switch relays)

    def turn_off(self):
        self.exec_logger.debug(f'Switching DPS off')
        self._dps_state = 'off'

    def turn_on(self):
        self.exec_logger.debug(f'Switching DPS on')
        self._dps_state = 'on'

    @property
    @abstractmethod
    def voltage(self):
        # add actions to read the DPS voltage and return it
        return None

    @voltage.setter
    @abstractmethod
    def voltage(self, value):
        # add actions to set the DPS voltage
        pass

    @property
    @abstractmethod
    def tx_bat(self):
        pass


    def voltage_pulse(self, voltage=0., length=None, polarity=None):
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
        if polarity is None:
            polarity = self.polarity
        self.polarity = polarity
        self.voltage = voltage
        self.exec_logger.debug(f'Voltage pulse of {polarity * voltage:.3f} V for {length:.3f} s')
        self.inject(state='on')
        time.sleep(length)
        # self.tx_sync.clear()
        self.inject(state='off')


class RxAbstract(ABC):
    def __init__(self, **kwargs):
        self.exec_logger = kwargs.pop('exec_logger', None)
        if self.exec_logger is None:
            self.exec_logger = create_stdout_logger('exec_rx')
        self.soh_logger = kwargs.pop('soh_logger', None)
        if self.soh_logger is None:
            self.soh_logger = create_stdout_logger('soh_rx')
        self.controller = kwargs.pop('controller', None)
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