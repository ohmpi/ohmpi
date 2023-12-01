
print('This assistent helps you configure a basic system with a measurement board and from 0 to 4 mux of the same type. For more complex configuration with multiple mux of different types, please have a look in the configs/ folder.')

mb = None
while True:
    if mb in ['v2023', 'v2024']:
        break
    else:
        mb = input('Choose a measurement boards: [v2023/v2024]: ')

mux = None
while True:
    if mux in ['v2023', 'v2024']:
        break
    else:
        mux = input('Choose a mux boards: [v2023/v2024]: ')

nb_mux = None
while True:
    if nb_mux in ['0', '1', '2', '3', '4']:
        break
    else:
        nb_mux = input('Number of multiplexers: [0, 1, 2, 3, 4]: ')
        
        
config = 'config_mb_' + mb[1:] + '_' + nb_mux + '_mux_' + mux[1:] + '.py'
print('Using this configuration: ' + config)

import os
import shutil
if os.path.exists('configs/' + config):
    shutil.copyfile('configs/' + config, 'ohmpi/config.py')
else:
    print('configuration not found')


