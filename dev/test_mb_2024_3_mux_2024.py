import matplotlib
matplotlib.use('TkAgg')
from ohmpi.utils import change_config
change_config('../configs/config_mb_2024_0_2__3_mux_2024_dps5005.py', verbose=False)
import importlib
import time
import logging
from ohmpi.config import HARDWARE_CONFIG

stand_alone = False
part_of_hardware_system = True
within_ohmpi = False

# Stand alone
if stand_alone:

    ctl_module = importlib.import_module(f'ohmpi.hardware_components.{HARDWARE_CONFIG["ctl"].pop("model")}')
    pwr_module = importlib.import_module(f'ohmpi.hardware_components.{HARDWARE_CONFIG["pwr"].pop("model")}')
    tx_module = importlib.import_module(f'ohmpi.hardware_components.{HARDWARE_CONFIG["tx"].pop("model")}')
    rx_module = importlib.import_module(f'ohmpi.hardware_components.{HARDWARE_CONFIG["rx"].pop("model")}')

    ctl = ctl_module.Ctl()
    HARDWARE_CONFIG['tx'].update({'ctl': ctl, 'exec_logger': ctl.exec_logger, 'soh_logger': ctl.soh_logger})
    HARDWARE_CONFIG['rx'].update({'ctl': ctl, 'exec_logger': ctl.exec_logger, 'soh_logger': ctl.soh_logger})
    HARDWARE_CONFIG['tx'].update({'connection': HARDWARE_CONFIG['tx'].pop('connection',
                                                                          ctl.interfaces[
                                                                              HARDWARE_CONFIG['tx'].pop(
                                                                                  'interface_name', 'i2c')])})
    HARDWARE_CONFIG['rx'].update({'connection': HARDWARE_CONFIG['rx'].pop('connection',
                                                                          ctl.interfaces[
                                                                              HARDWARE_CONFIG['rx'].pop(
                                                                                  'interface_name', 'i2c')])})

    HARDWARE_CONFIG['pwr'].update({'connection': HARDWARE_CONFIG['pwr'].pop('connection',
                                                                          ctl.interfaces[
                                                                              HARDWARE_CONFIG['pwr'].pop(
                                                                                  'interface_name', None)])})


    rx = rx_module.Rx(**HARDWARE_CONFIG['rx'])
    tx = tx_module.Tx(**HARDWARE_CONFIG['tx'])
    pwr = pwr_module.Pwr(**HARDWARE_CONFIG['pwr'])
    mux_ids = ['mux_02', 'mux_05']
    for m,mux_id in enumerate(mux_ids):
        mux_module = importlib.import_module(
            f'ohmpi.hardware_components.{HARDWARE_CONFIG["mux"]["boards"][mux_id].pop("model")}')

        MUX_CONFIG = HARDWARE_CONFIG['mux']['boards'][mux_id]

        MUX_CONFIG.update({'ctl': ctl, 'connection': MUX_CONFIG.pop('connection', ctl.interfaces[
                                           MUX_CONFIG.pop('interface_name', 'i2c_ext')]), 'exec_logger': ctl.exec_logger,
                       'soh_logger': ctl.soh_logger})
        MUX_CONFIG.update({'id': mux_id})
        mux = mux_module.Mux(**MUX_CONFIG)

        # tx.polarity = 1
        # time.sleep(1)
        # tx.polarity = 0
        # mux.switch(elec_dict={'A': [1], 'B': [4], 'M': [2], 'N': [3]}, state='on')
        # time.sleep(1)
        # voltage = rx.voltage
        # current = tx.current
        # mux.switch(elec_dict={'A': [1], 'B': [4], 'M': [2], 'N': [3]}, state='off')
        # print(f'Resistance: {voltage / current :.2f} ohm, voltage: {voltage:.2f} mV, current: {current:.2f} mA')
        mux.reset()
        mux.test({'A': [i+8*m for i in range(1, 9)], 'B': [i+8*m for i in range(1, 9)],
                  'M': [i+8*m for i in range(1, 9)], 'N': [i+8*m for i in range(1, 9)]}, activation_time=.1)
        mux.reset()

# mux as part of a OhmPiHardware system
if part_of_hardware_system:
    from ohmpi.hardware_system import OhmPiHardware
    print('Starting test of as part of an OhmPiHardware system.')
    # mux_id = 'mux_03'
    k = OhmPiHardware()
    k.exec_logger.setLevel(logging.DEBUG)
    # Test mux switching
    k.reset_mux()
    # k.switch_mux(electrodes=[1, 4, 2, 3], roles=['A', 'B', 'M', 'N'], state='on')
    # time.sleep(1.)
    # k.switch_mux(electrodes=[1, 4, 2, 3], roles=['A', 'B', 'M', 'N'], state='off')
    # k.mux_boards[mux_id].test(activation_time=.4)
    k.test_mux()
    k.reset_mux()

if within_ohmpi:
    from ohmpi.ohmpi import OhmPi
    # from ohmpi.plots import plot_exec_log

    print('Starting test with OhmPi.')
    k = OhmPi()
    # A, B, M, N = (32, 29, 31, 30)
    k.reset_mux()
    k.load_sequence('sequences/ABMN2.txt')
    k.run_sequence(tx_volt=50, injection_duration=1., nb_stack=2, duty_cycle=0.5)
    print('using OhmPi')
    #d = k.run_measurement([A, B, M, N], injection_duration=1., nb_stack=2, duty_cycle=0.5)
    # print(d)
    # k._hw._plot_readings()
    print(f'OhmPiHardware: Resistance: {k._hw.last_resistance() :.2f} ohm, dev. {k._hw.last_dev():.2f} %, sp: {k._hw.sp:.2f} mV, rx bias: {k._hw.rx._bias:.2f} mV')
    print(f'OhmPi: Resistance: {d["R [ohm]"] :.2f} ohm, dev. {d["R_std [%]"]:.2f} %, rx bias: {k._hw.rx._bias:.2f} mV')
    # k._hw._plot_readings(save_fig=False)
    # plot_exec_log('ohmpi/logs/exec.log')
change_config('../configs/config_default.py', verbose=False)
