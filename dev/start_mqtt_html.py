
# we need to start the OhmPi instance so that it listens
# to message from the MQTT broker

import subprocess
# launch webserver

from ohmpi.utils import change_config
#change_config('../configs/config_mb_2023.py', verbose=False)
change_config('../configs/config_mb_2024_0_2__4_mux_2023_dps5005.py', verbose=False)

from ohmpi.ohmpi import OhmPi
from ohmpi.config import OHMPI_CONFIG
ohmpi = OhmPi(settings=OHMPI_CONFIG['settings'])
if ohmpi.controller is not None:
    ohmpi.controller.loop_forever()

# restore default config
change_config('../configs/config_default.py', verbose=False)
