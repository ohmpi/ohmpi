import logging
from ohmpi.utils import change_config
change_config('../configs/config_dummy.py', verbose=True)

from ohmpi.hardware_components.dummy_tx import Tx
from ohmpi.hardware_components.dummy_rx import Rx
from ohmpi.logging_setup import create_stdout_logger

# exec_logger = create_stdout_logger(name='exec')
# soh_logger = create_stdout_logger(name='soh')

stand_alone = False
part_of_hardware_system = False
within_ohmpi = True

# Stand alone
if stand_alone:
    print('\nCreating TX...')
    tx = Tx(exec_logger=exec_logger, soh_logger=soh_logger)
    print('\nCreating RX...')
    rx = Rx(exec_logger=exec_logger, soh_logger=soh_logger)

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
    k.test_mux(activation_time=0.01)
    k.reset_mux()

if within_ohmpi:
    from ohmpi.ohmpi import OhmPi
    # from ohmpi.plots import plot_exec_log

    print('Starting test with OhmPi.')
    k = OhmPi(mqtt=False)
    k._hw.exec_logger.setLevel(logging.DEBUG)
    A, B, M, N = (32, 29, 31, 30)
    # k.reset_mux()
    # k.test_mux(activation_time=0.01)#mux_id='mux_A')
    # k._hw.switch_mux([A, B, M, N], state='on')
    # k._hw.vab_square_wave(12.,1., cycles=2)
    # TODO self.tx_sync_wait() is blocking here
    # k._hw.switch_mux([A, B, M, N], state='off')
    # k._hw.calibrate_rx_bias()  # electrodes 1 4 2 3 should be connected to a reference circuit
    # k._hw.rx._bias = -1.38
    # print(f'Resistance: {k._hw.last_rho :.2f} ohm, dev. {k._hw.last_dev:.2f} %, rx bias: {k._hw.rx._bias:.2f} mV')
    # k._hw._plot_readings()
    A, B, M, N = (0, 0, 0, 0)
    # k._hw.switch_mux([A, B, M, N], state='on')
    # k._hw.vab_square_wave(12., cycle_duration=10., cycles=3)
    # k._hw.switch_mux([A, B, M, N], state='off')
    # print(f'OhmPiHardware Resistance: {k._hw.last_rho :.2f} ohm, dev. {k._hw.last_dev:.2f} %, rx bias: {k._hw.rx._bias:.2f} mV')
    # k._hw._plot_readings()
    print('using OhmPi')
    # d = k.run_measurement([A, B, M, N], injection_duration=1., nb_stack=2, duty_cycle=0.5)
    # print('---', d)
    # k._hw._plot_readings()
    # print(f'OhmPiHardware: Resistance: {k._hw.last_resistance() :.2f} ohm, dev. {k._hw.last_dev():.2f} %, sp: {k._hw.sp:.2f} mV, rx bias: {k._hw.rx._bias:.2f} mV')
    # print(f'OhmPi: Resistance: {d["R [ohm]"] :.2f} ohm, dev. {d["R_std [%]"]:.2f} %, rx bias: {k._hw.rx._bias:.2f} mV')
    # k._hw._plot_readings(save_fig=False)
    # plot_exec_log('ohmpi/logs/exec.log')
change_config('../configs/config_default.py', verbose=False)
