
# we need to start the OhmPi instance so that it listens
# to message from the MQTT broker
import os
import shutil
from ohmpi.utils import change_config
# change_config('../configs/config_mb_2023.py', verbose=False)
# change_config('../configs/config_mb_2023__4_mux_2023.py', verbose=False)
# change_config('../configs/config_mb_2024_0_2__4_mux_2023_dph5005.py', verbose=False)

# start html interface
import subprocess
proc = subprocess.Popen(['python', '-m', 'http.server'])

# start ohmpi listener
try:
    from ohmpi.ohmpi import OhmPi
    from ohmpi.config import OHMPI_CONFIG
    k = OhmPi(settings=OHMPI_CONFIG['settings'])
    k.update_settings({'export_path': 'data_web/measurements.csv'})

    # check if data folder exists
    if os.path.exists('data') is False:
        os.mkdir('data')

    # check if data_web exists
    if os.path.exists('data_web/'):
        print(f'data_web exist, moving {len(os.listdir("data_web"))} files from data_web/ to data/ ...', end='')
        for f in os.listdir('data_web/'):
            shutil.move(os.path.join('data_web', f), os.path.join('data', f))
        print('done')
    else:
        print('creating data_web')
        os.mkdir('data_web')

    # import os
    # k.load_sequence(os.path.join(os.path.dirname(__file__), './sequences/wenner1-16.txt'))
    # k.reset_mux()
    #k.run_multiple_sequences(sequence_delay=20, nb_meas=3)

    if k.controller is not None:
        k.controller.loop_forever()
except Exception as e:
    proc.terminate()
    print('ERROR', e)
    

# restore default config
# change_config('../configs/config_default.py', verbose=False)
