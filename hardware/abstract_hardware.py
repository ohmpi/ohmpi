from abc import ABC, abstractmethod
from OhmPi.logging_setup import create_stdout_logger
import time

class ControllerAbstract(ABC):
    def __init__(self, **kwargs):
        self.bus = None

class MuxAbstract(ABC):
    def __init__(self, **kwargs):
        pass

class TxAbstract(ABC):
    def __init__(self, **kwargs):
        self.board_name = kwargs.pop('board_name', 'unknown TX hardware')
        polarity = kwargs.pop('polarity', 1)
        if polarity is None:
            polarity = 0
        self._polarity = polarity
        print(f'polarity: {polarity}')  # TODO: delete me
        inj_time = kwargs.pop('inj_time', 1.)
        self.exec_logger = kwargs.pop('exec_logger', None)
        if self.exec_logger is None:
            self.exec_logger = create_stdout_logger('exec_tx')
        self.soh_logger = kwargs.pop('soh_logger', None)
        if self.soh_logger is None:
            self.soh_logger = create_stdout_logger('soh_tx')
        #self._polarity = polarity
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
    def voltage(self, value, **kwargs):
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
            self.exec_logger = create_stdout_logger('exec_tx')
        self.soh_logger = kwargs.pop('soh_logger', None)
        self.board_name = kwargs.pop('board_name', 'unknown RX hardware')
        self.exec_logger.debug(f'{self.board_name} RX initialization')
        self._adc_gain = 1.

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
    @abstractmethod
    def voltage(self):
        """ Gets the voltage VMN in Volts
        """
        pass