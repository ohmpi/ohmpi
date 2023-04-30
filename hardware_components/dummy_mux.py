from OhmPi.config import HARDWARE_CONFIG
import os
from OhmPi.hardware_components import MuxAbstract
MUX_CONFIG = HARDWARE_CONFIG['mux'].pop('default', {})

class Mux(MuxAbstract):
    def __init__(self, **kwargs):
        kwargs.update({'board_name': os.path.basename(__file__).rstrip('.py')})
        super().__init__(**kwargs)

    def _get_addresses(self):
        pass

    def reset(self):
        pass

    def switch_one(self, *args):
        MuxAbstract.switch_one(self, *args)

    def test(self, *args):
        MuxAbstract.test(self, *args)