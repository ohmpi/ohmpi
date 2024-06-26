from ohmpi.config import HARDWARE_CONFIG
import os
from ohmpi.hardware_components import MuxAbstract
MUX_CONFIG = HARDWARE_CONFIG['mux'].pop('default', {})


class Mux(MuxAbstract):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _get_addresses(self):
        pass

    def reset(self):
        pass

    def switch_one(self, *args):
        MuxAbstract.switch_one(self, *args)

    def test(self, *args, **kwargs):
        MuxAbstract.test(self, *args)