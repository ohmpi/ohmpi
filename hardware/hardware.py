from abc import ABC
import os
import sys
from time import gmtime
import logging

class ControllerAbstract(ABC):
    def __init__(self, **kwargs):
        self.bus = None

class MuxAbstract(ABC):
    pass

class TxAbstract(ABC):
    def __init__(self, **kwargs):
        polarity = kwargs.pop('polarity', 1)
        inj_time = kwargs.pop('inj_time', 1.)
        self.exec_logger = kwargs.pop('exec_logger', None)
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
        self._polarity = None
        self._inj_time = None
        self._dps_state = 'off'
        self.polarity = polarity
        self.inj_time = inj_time
        self.board_name = os.path.basename(__file__)
        self.exec_logger.debug(f'TX {self.board_name} initialization')

    @property
    def current(self):
        # add actions to read the DPS current and return it
        return None

    @current.setter
    def current(self, value, **kwargs):
        # add actions to set the DPS current
        pass

    def current_pulse(self, **kwargs):
        pass

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
    def voltage(self):
        # add actions to read the DPS voltage and return it
        return None

    @voltage.setter
    def voltage(self, value, **kwargs):
        # add actions to set the DPS voltage
        pass

    def voltage_pulse(self, voltage, length, polarity):
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
        pass


class RxAbstract(ABC):
    def __init__(self, **kwargs):
        self.exec_logger = kwargs.pop('exec_logger', None)
        self.soh_logger = kwargs.pop('soh_logger', None)
        self.board_name = os.path.basename(__file__)
        self.exec_logger.debug(f'RX {self.board_name} initialization')

