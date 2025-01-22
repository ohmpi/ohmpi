import os
import shutil

check_r_shunt = True
check_jumpers_msg = False
print('This assistant helps you configure a basic system with a measurement board and from 0 to 4 mux of the same type.'
      '\nFor more complex configurations including a combination of mux boards with different types or roles, '
      'please read the docs and explore the configs folder for examples and write your customized configuration file.')

mb = None
while True:
    if mb in ['v2023', 'v2024']:
        break
    else:
        mb = input('Choose a measurement boards: [v2023/v2024]: ')

if mb == 'v2024':
    mb = 'v2024_1_X_'  # NOTE: used to be set to mb_2024_0_2 by default
    print(f'Using board version {mb}. If you are using another version of this board,'
          f' make sure to update your config.py file using this tool.\n')

use_mux = '?'
while True:
    if use_mux in ('yes', 'Yes'):
        use_mux = True
        break
    elif use_mux in ('no, No'):
        use_mux = False
        break
    else:
        use_mux = input('Would you like to use mux boards? [yes/no]: ')

if use_mux:
    mux = None
    while True:
        mux_types = ['v2023', 'v2024']
        if mux in mux_types:
            break
        else:
            mux = input('Choose a mux board type: [v2023/v2024]: ')

    roles = None
    if mux == 'v2024':
        while True:
            if roles in ['2roles', '4roles']:
                break
            else:
                roles = input('How are your mux boards configured: [2roles/4roles]: ')
        check_jumpers_msg = True

    nb_mux = None
    while True:
        if nb_mux in ['1', '2', '3', '4']:
            break
        else:
            nb_mux = input('Number of multiplexers: [1/2/3/4]: ')

pwr = None
while True:
    if pwr in ['battery', 'dph5005']:
        break
    else:
        pwr = input('Tx power: [battery/dph5005]:')
if use_mux:
    config = ('config_mb_' + mb[1:] + '_' + nb_mux + '_mux_' + mux[1:])
    if roles is not None:
        config = (config + '_' + roles + '.py')
    else:
        config = (config + '.py')
else:
    config = ('config_mb_' + mb[1:] + '.py')

if pwr != 'battery':
    config = config.replace('.py', '_' + pwr + '.py')
    if use_mux is False:
        config = config.replace('__', '_')
print('Using this configuration: ' + config)

if os.path.exists('configs/' + config):
    shutil.copyfile('configs/' + config, 'ohmpi/config.py')
    shutil.copyfile('configs/' + config, 'configs/config_backup.py')
    from ohmpi.config import HARDWARE_CONFIG, r_shunt, ohmpi_id
    print(f'Your configuration has been set. Your OhmPi id is set to {ohmpi_id}.')
    print(f'The configuration file is stored in ohmpi/config.py, a backup copy is stored in configs/config_backup.py')
    print('You should now carefully verify that the configuration file fits your hardware setup.\n')
    k = 1
    if check_r_shunt:
        print(f'{k}. Check that the value of the shunt resistor value is {r_shunt} Ohm as stated in the config file.')
        k += 1
    if check_jumpers_msg:
        print(f'\n{k}. Make sure to check that all your mux boards {mux} are configured in {roles} and that'
              ' the jumpers are set as stated below:')
        for mux, c in HARDWARE_CONFIG['mux']['boards'].items():
            print(f'     Mux board {mux}: jumper addr1: {c["addr1"]},\t jumper addr2: {c["addr2"]}')
        k += 1
    print(f'\n{k}. If you experience problems while starting or operation your OhmPi, analyse the logs and/or try '
          f'setting your the loggers "logging_level" to logging.DEBUG.')
    k += 1
    print(f'\n{k}. Refer to the documentation for optional tests to conduct before using your instrument.')

    # print('\n' + '_'*100)
    # with open('ohmpi/config.py', mode='rt') as f:
    #     for line in f.readlines():
    #         print(line, end='')
    # print('\n'+'_'*100)
    print('\n' + '*' * 93)
    print('*** You may customize the configuration of your OhmPi by editing the ohmpi/config.py file ***')
    print('***   The MQTT communication can be encrypted with TLS/SSL but it is not set by default   ***')
    print('***  You should then change the username and password used to connect to the mqtt broker  ***')
    print('***     Make sure you understand what you are doing to avoid damaging to your system      ***')
    print('***  If you successfully updated your ohmpi/config.py file, update your backup copy too   ***')
    print('*' * 93)
    if pwr != 'battery':
        print('\n' + '#' * 93)
        print('###                      WARNING - INJECTION VOLTAGE LIMITATION SET!                      ###')
        print('###                      ===========================================                      ###')
        print('###    A limitation has been set on the injection voltage to conduct the initial tests.   ###')
        print('###   To lift this voltage limitation, please edit your ohmpi/config.py (and backup) and  ###')
        print("###                adapt or remove the 'voltage' specification in the 'pwr'               ###")
        print("###                        value of the HARDWARE_CONFIG dictionary.                       ###")
        print('\n' + '#' * 93)
else:
    print('The configuration you have selected cannot be set by this tool.\n'
          'You probably requested a configuration that makes little sense in most cases.')