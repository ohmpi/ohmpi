from ohmpi.ohmpi import OhmPi
from ohmpi.config import OHMPI_CONFIG

ohmpi = OhmPi(settings=OHMPI_CONFIG['settings'])
if ohmpi.controller is not None:
    ohmpi.controller.loop_forever()
