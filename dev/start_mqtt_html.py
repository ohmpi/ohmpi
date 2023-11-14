
# we need to start the OhmPi instance so that it listens
# to message from the MQTT broker

from ohmpi.utils import change_config
# change_config('../configs/config_mb_2023.py', verbose=False)
change_config('../configs/config_mb_2023_4_mux_2023.py', verbose=False)
#change_config('../configs/config_mb_2024_0_2__4_mux_2023_dps5005.py', verbose=False)

# start html interface
import subprocess
subprocess.Popen(['python', '-m', 'http.server'])

# start ohmpi listener
from ohmpi.ohmpi import OhmPi
from ohmpi.config import OHMPI_CONFIG
k = OhmPi(settings=OHMPI_CONFIG['settings'])
import os
k.load_sequence(os.path.join(os.path.dirname(__file__), '../sequences/wenner16.txt'))
k.reset_mux()
#k.run_multiple_sequences(sequence_delay=20, nb_meas=3)

if k.controller is not None:
    k.controller.loop_forever()

# restore default config
change_config('../configs/config_default.py', verbose=False)
