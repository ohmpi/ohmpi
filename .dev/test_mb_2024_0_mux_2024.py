import matplotlib
matplotlib.use('TkAgg')
from ohmpi.utils import change_config
change_config('../configs/config_mb_2024_0_2.py', verbose=False)
import importlib
import time
import logging
from ohmpi.config import HARDWARE_CONFIG

stand_alone = False
part_of_hardware_system = False
within_ohmpi = True

# Stand alone
if stand_alone:
    ctl_module = importlib.import_module(f'ohmpi.hardware_components.{HARDWARE_CONFIG["ctl"].pop("model")}')
    pwr_module = importlib.import_module(f'ohmpi.hardware_components.{HARDWARE_CONFIG["pwr"].pop("model")}')
    tx_module = importlib.import_module(f'ohmpi.hardware_components.{HARDWARE_CONFIG["tx"].pop("model")}')
    rx_module = importlib.import_module(f'ohmpi.hardware_components.{HARDWARE_CONFIG["rx"].pop("model")}')

    ctl = ctl_module.Ctl()
    HARDWARE_CONFIG['tx'].update({'ctl': ctl})  # HARDWARE_CONFIG['tx'].pop('ctl', ctl_module.Ctl())})
    HARDWARE_CONFIG['rx'].update({'ctl': ctl})  # HARDWARE_CONFIG['rx'].pop('ctl', ctl_module.Ctl())})
    HARDWARE_CONFIG['tx'].update({'connection': HARDWARE_CONFIG['tx'].pop('connection',
                                                                          ctl.interfaces[
                                                                              HARDWARE_CONFIG['tx'].pop(
                                                                                  'interface_name', 'i2c')])})
    HARDWARE_CONFIG['rx'].update({'connection': HARDWARE_CONFIG['rx'].pop('connection',
                                                                          ctl.interfaces[
                                                                              HARDWARE_CONFIG['rx'].pop(
                                                                                  'interface_name', 'i2c')])})

    rx = rx_module.Rx(**HARDWARE_CONFIG['rx'])
    tx = tx_module.Tx(**HARDWARE_CONFIG['tx'])
    pwr = pwr_module.Pwr(**HARDWARE_CONFIG['pwr'])

    tx.polarity = 1
    time.sleep(1)
    tx.polarity = 0

# mux as part of a OhmPiHardware system
if part_of_hardware_system:
    from ohmpi.hardware_system import OhmPiHardware
    print('Starting test of as part of an OhmPiHardware system.')

    k = OhmPiHardware()
    k.exec_logger.setLevel(logging.DEBUG)
    # Test mux switching
    k.reset_mux()
    k.switch_mux(electrodes=[1, 4, 2, 3], roles=['A', 'B', 'M', 'N'], state='on')
    time.sleep(1.)
    k.switch_mux(electrodes=[1, 4, 2, 3], roles=['A', 'B', 'M', 'N'], state='off')

if within_ohmpi:
    from ohmpi.ohmpi import OhmPi
    # from ohmpi.plots import plot_exec_log

    print('Starting test with OhmPi.')
    k = OhmPi()
    #A, B, M, N = (32, 29, 31, 30)
    k.reset_mux()
    #k._hw.switch_mux([A, B, M, N], state='on')
    #k._hw.vab_square_wave(12.,1., cycles=2)
    #k._hw.switch_mux([A, B, M, N], state='off')
    #k._hw.calibrate_rx_bias()  # electrodes 1 4 2 3 should be connected to a reference circuit
    #k._hw.rx._bias = -1.38
    #print(f'Resistance: {k._hw.last_rho :.2f} ohm, dev. {k._hw.last_dev:.2f} %, rx bias: {k._hw.rx._bias:.2f} mV')
    # k._hw._plot_readings()
    A, B, M, N = (0, 0, 0, 0)
    # k._hw.switch_mux([A, B, M, N], state='on')
    # k._hw.vab_square_wave(12., cycle_duration=10., cycles=3)
    # k._hw.switch_mux([A, B, M, N], state='off')
    # print(f'OhmPiHardware Resistance: {k._hw.last_rho :.2f} ohm, dev. {k._hw.last_dev:.2f} %, rx bias: {k._hw.rx._bias:.2f} mV')
    # k._hw._plot_readings()
    print('using OhmPi')
    d = k.run_measurement([A, B, M, N], injection_duration=1., nb_stack=2, duty_cycle=0.5)
    print(d)
    #k._hw._plot_readings()
    print(f'OhmPiHardware: Resistance: {k._hw.last_resistance() :.2f} ohm, dev. {k._hw.last_dev():.2f} %, sp: {k._hw.sp:.2f} mV, rx bias: {k._hw.rx._bias:.2f} mV')
    # print(f'OhmPi: Resistance: {d["R [ohm]"] :.2f} ohm, dev. {d["R_std [%]"]:.2f} %, rx bias: {k._hw.rx._bias:.2f} mV')
    k._hw._plot_readings(save_fig=False)
    # plot_exec_log('ohmpi/logs/exec.log')
change_config('../configs/config_default.py', verbose=False)
