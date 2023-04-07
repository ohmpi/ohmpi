from abc import ABC
import os
class ControllerAbstract(ABC):
    def __init__(self, **kwargs):
        self.bus = None

class MuxAbstract(ABC):
    pass

class TxAbstract(ABC):
    def __init__(self, **kwargs):
        polarity = kwargs.pop('polarity', 1)
        inj_time = kwargs.pop('inj_time', 1.)
        exec_logger = kwargs.pop('exec_logger', None)
        soh_logger = kwargs.pop('soh_logger', None)
        self._polarity = None
        self._inj_time = None
        self.polarity = polarity
        self.inj_time = inj_time
        board_name = os.path.basename(__file__)
        self.exec_logger.debug(f'TX {board_name} Initialized.')

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
        assert value in [-1,1]
        self._polarity = value
        # add actions to set the polarity (switch relays)

    def turn_off(self):
        # add actions to turn the DPS off
        pass

    def turn_on(self):
        # add actions to turn the DPS on
        pass

    @property
    def voltage(self):
        # add actions to read the DPS voltage and return it
        return None

    @voltage.setter
    def voltage(self, value, **kwargs):
        # add actions to set the DPS voltage
        pass

    def current(self, **kwargs):
        pass


class RxAbstract(ABC):
    pass
