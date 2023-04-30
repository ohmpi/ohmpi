# -*- coding: utf-8 -*-
"""
created on January 6, 2020.
Updates dec 2022.
Hardware: Licensed under CERN-OHL-S v2 or any later version
Software: Licensed under the GNU General Public License v3.0
Ohmpi.py is a program to control a low-cost and open hardware resistivity meter OhmPi that is developed by
Rémi CLEMENT (INRAE), Vivien DUBOIS (INRAE), Hélène GUYARD (IGE), Nicolas FORQUET (INRAE), Yannick FARGIER (IFSTTAR)
Olivier KAUFMANN (UMONS), Arnaud WATLET (UMONS) and Guillaume BLANCHY (FNRS/ULiege).
"""

import os
from OhmPi.utils import get_platform
import json
from copy import deepcopy
import numpy as np
import csv
import time
import shutil
from datetime import datetime
from termcolor import colored
import threading
from OhmPi.logging_setup import setup_loggers
from OhmPi.config import MQTT_CONTROL_CONFIG, OHMPI_CONFIG, EXEC_LOGGING_CONFIG
import OhmPi.deprecated as deprecated
from logging import DEBUG
from OhmPi.hardware_system import OhmPiHardware

# finish import (done only when class is instantiated as some libs are only available on arm64 platform)
try:
    arm64_imports = True
except ImportError as error:
    if EXEC_LOGGING_CONFIG['logging_level'] == DEBUG:
        print(colored(f'Import error: {error}', 'yellow'))
    arm64_imports = False
except Exception as error:
    print(colored(f'Unexpected error: {error}', 'red'))
    arm64_imports = None

class OhmPi(object):
    """ OhmPi class.
    """

    def __init__(self, settings=None, sequence=None, mqtt=True, onpi=None):
        """Constructs the ohmpi object

        Parameters
        ----------
        settings:

        sequence:

        mqtt: bool, defaut: True
            if True publish on mqtt topics while logging, otherwise use other loggers only
        onpi: bool,None default: None
            if None, the platform on which the class is instantiated is determined to set on_pi to either True or False.
            if False the behaviour of an ohmpi will be partially emulated and return random data.
        """

        if onpi is None:
            _, onpi = get_platform()
        elif onpi:
            assert get_platform()[1] == True  # Checks that the system actually runs on a pi if onpi is True
        self.on_pi = onpi  # True if run from the RaspberryPi with the hardware, otherwise False for random data

        self._sequence = sequence
        self.nb_samples = 0
        self.status = 'idle'  # either running or idle
        self.thread = None  # contains the handle for the thread taking the measurement

        # set loggers
        config_exec_logger, _, config_data_logger, _, config_soh_logger, _, _, msg = setup_loggers(mqtt=mqtt)
        self.exec_logger = config_exec_logger
        self.soh_logger = config_soh_logger
        print(msg)

        # read in hardware parameters (config.py)
        self._hw = OhmPiHardware(**{'exec_logger': self.exec_logger, 'data_logger': self.data_logger,
                                  'soh_logger': self.soh_logger})
        self.exec_logger.info('Hardware configured...')
        # default acquisition settings
        self.settings = {
            'injection_duration': 0.2,
            'nb_meas': 1,
            'sequence_delay': 1,
            'nb_stack': 1,
            'export_path': 'data/measurement.csv'
        }
        # read in acquisition settings
        if settings is not None:
            self.update_settings(settings)

        self.exec_logger.debug('Initialized with settings:' + str(self.settings))

        # read quadrupole sequence
        if sequence is not None:
            self.load_sequence(sequence)

        # set controller
        self.mqtt = mqtt
        self.cmd_id = None
        if self.mqtt:
            import paho.mqtt.client as mqtt_client

            self.exec_logger.debug(f"Connecting to control topic {MQTT_CONTROL_CONFIG['ctrl_topic']}"
                                   f" on {MQTT_CONTROL_CONFIG['hostname']} broker")

            def connect_mqtt() -> mqtt_client:
                def on_connect(mqttclient, userdata, flags, rc):
                    if rc == 0:
                        self.exec_logger.debug(f"Successfully connected to control broker:"
                                               f" {MQTT_CONTROL_CONFIG['hostname']}")
                    else:
                        self.exec_logger.warning(f'Failed to connect to control broker. Return code : {rc}')

                client = mqtt_client.Client(f"ohmpi_{OHMPI_CONFIG['id']}_listener", clean_session=False)
                client.username_pw_set(MQTT_CONTROL_CONFIG['auth'].get('username'),
                                       MQTT_CONTROL_CONFIG['auth']['password'])
                client.on_connect = on_connect
                client.connect(MQTT_CONTROL_CONFIG['hostname'], MQTT_CONTROL_CONFIG['port'])
                return client

            try:
                self.exec_logger.debug(f"Connecting to control broker: {MQTT_CONTROL_CONFIG['hostname']}")
                self.controller = connect_mqtt()
            except Exception as e:
                self.exec_logger.debug(f'Unable to connect control broker: {e}')
                self.controller = None
            if self.controller is not None:
                self.exec_logger.debug(f"Subscribing to control topic {MQTT_CONTROL_CONFIG['ctrl_topic']}")
                try:
                    self.controller.subscribe(MQTT_CONTROL_CONFIG['ctrl_topic'], MQTT_CONTROL_CONFIG['qos'])

                    msg = f"Subscribed to control topic {MQTT_CONTROL_CONFIG['ctrl_topic']}" \
                          f" on {MQTT_CONTROL_CONFIG['hostname']} broker"
                    self.exec_logger.debug(msg)
                    print(colored(f'\u2611 {msg}', 'blue'))
                except Exception as e:
                    self.exec_logger.warning(f'Unable to subscribe to control topic : {e}')
                    self.controller = None
                publisher_config = MQTT_CONTROL_CONFIG.copy()
                publisher_config['topic'] = MQTT_CONTROL_CONFIG['ctrl_topic']
                publisher_config.pop('ctrl_topic')

                def on_message(client, userdata, message):
                    command = message.payload.decode('utf-8')
                    self.exec_logger.debug(f'Received command {command}')
                    self._process_commands(command)

                self.controller.on_message = on_message
            else:
                self.controller = None
                self.exec_logger.warning('No connection to control broker.'
                                         ' Use python/ipython to interact with OhmPi object...')

    def __getattr__(self, name):
        if hasattr(deprecated, name):
            return getattr(deprecated, name)
        else:
            return self.__getattr__(name)

    @staticmethod
    def append_and_save(filename: str, last_measurement: dict, cmd_id=None):
        """Appends and saves the last measurement dict.

        Parameters
        ----------
        filename : str
            filename to save the last measurement dataframe
        last_measurement : dict
            Last measurement taken in the form of a python dictionary
        cmd_id : str, optional
            Unique command identifier
        """
        last_measurement = deepcopy(last_measurement)
        if 'fulldata' in last_measurement:
            d = last_measurement['fulldata']
            n = d.shape[0]
            if n > 1:
                idic = dict(zip(['i' + str(i) for i in range(n)], d[:, 0]))
                udic = dict(zip(['u' + str(i) for i in range(n)], d[:, 1]))
                tdic = dict(zip(['t' + str(i) for i in range(n)], d[:, 2]))
                last_measurement.update(idic)
                last_measurement.update(udic)
                last_measurement.update(tdic)
            last_measurement.pop('fulldata')

        if os.path.isfile(filename):
            # Load data file and append data to it
            with open(filename, 'a') as f:
                w = csv.DictWriter(f, last_measurement.keys())
                w.writerow(last_measurement)
                # last_measurement.to_csv(f, header=False)
        else:
            # create data file and add headers
            with open(filename, 'a') as f:
                w = csv.DictWriter(f, last_measurement.keys())
                w.writeheader()
                w.writerow(last_measurement)


    @staticmethod
    def _find_identical_in_line(quads):
        """Finds quadrupole where A and B are identical.
        If A and B are connected to the same electrode, the Pi burns (short-circuit).

        Parameters
        ----------
        quads : numpy.ndarray
            List of quadrupoles of shape nquad x 4 or 1D vector of shape nquad.

        Returns
        -------
        output : numpy.ndarray 1D array of int
            List of index of rows where A and B are identical.
        """

        # if we have a 1D array (so only 1 quadrupole), make it a 2D array
        if len(quads.shape) == 1:
            quads = quads[None, :]

        output = np.where(quads[:, 0] == quads[:, 1])[0]

        return output

    def get_data(self, survey_names=None, cmd_id=None):
        """Get available data.
        
        Parameters
        ----------
        survey_names : list of str, optional
            List of filenames already available from the html interface. So
            their content won't be returned again. Only files not in the list
            will be read.
        cmd_id : str, optional
            Unique command identifier
        """
        # get all .csv file in data folder
        if survey_names is None:
            survey_names = []
        fnames = [fname for fname in os.listdir('data/') if fname[-4:] == '.csv']
        ddic = {}
        if cmd_id is None:
            cmd_id = 'unknown'
        for fname in fnames:
            if ((fname != 'readme.txt')
                    and ('_rs' not in fname)
                    and (fname.replace('.csv', '') not in survey_names)):
                try:
                    data = np.loadtxt('data/' + fname, delimiter=',',
                                      skiprows=1, usecols=(1, 2, 3, 4, 8))
                    data = data[None, :] if len(data.shape) == 1 else data
                    ddic[fname.replace('.csv', '')] = {
                        'a': data[:, 0].astype(int).tolist(),
                        'b': data[:, 1].astype(int).tolist(),
                        'm': data[:, 2].astype(int).tolist(),
                        'n': data[:, 3].astype(int).tolist(),
                        'rho': data[:, 4].tolist(),
                    }
                except Exception as e:
                    print(fname, ':', e)
        rdic = {'cmd_id': cmd_id, 'data': ddic}
        self.data_logger.info(json.dumps(rdic))
        return ddic

    def interrupt(self, cmd_id=None):
        """Interrupts the acquisition

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier
        """
        self.status = 'stopping'
        if self.thread is not None:
            self.thread.join()
            self.exec_logger.debug('Interrupted sequence acquisition...')
        else:
            self.exec_logger.debug('No sequence measurement thread to interrupt.')
        self.exec_logger.debug(f'Status: {self.status}')

    def load_sequence(self, filename: str, cmd_id=None):
        """Reads quadrupole sequence from file.

        Parameters
        ----------
        filename : str
            Path of the .csv or .txt file with A, B, M and N electrodes.
            Electrode index start at 1.
        cmd_id : str, optional
            Unique command identifier

        Returns
        -------
        sequence : numpy.array
            Array of shape (number quadrupoles * 4).
        """
        self.exec_logger.debug(f'Loading sequence {filename}')
        sequence = np.loadtxt(filename, delimiter=" ", dtype=np.uint32)  # load quadrupole file

        if sequence is not None:
            self.exec_logger.debug(f'Sequence of {sequence.shape[0]:d} quadrupoles read.')

        # locate lines where the electrode index exceeds the maximum number of electrodes
        test_index_elec = np.array(np.where(sequence > self.max_elec))

        # locate lines where electrode A == electrode B
        test_same_elec = self._find_identical_in_line(sequence)

        # if statement with exit cases (TODO rajouter un else if pour le deuxième cas du ticket #2)
        if test_index_elec.size != 0:
            for i in range(len(test_index_elec[0, :])):
                self.exec_logger.error(f'An electrode index at line {str(test_index_elec[0, i] + 1)} '
                                       f'exceeds the maximum number of electrodes')
            # sys.exit(1)
            sequence = None
        elif len(test_same_elec) != 0:
            for i in range(len(test_same_elec)):
                self.exec_logger.error(f'An electrode index A == B detected at line {str(test_same_elec[i] + 1)}')
            # sys.exit(1)
            sequence = None

        if sequence is not None:
            self.exec_logger.info(f'Sequence {filename} of {sequence.shape[0]:d} quadrupoles loaded.')
        else:
            self.exec_logger.warning(f'Unable to load sequence {filename}')
        self.sequence = sequence

    def _process_commands(self, message: str):
        """Processes commands received from the controller(s)

        Parameters
        ----------
        message : str
            message containing a command and arguments or keywords and arguments
        """
        status = False
        cmd_id = '?'
        try:
            decoded_message = json.loads(message)
            self.exec_logger.debug(f'Decoded message {decoded_message}')
            cmd_id = decoded_message.pop('cmd_id', None)
            cmd = decoded_message.pop('cmd', None)
            # args = decoded_message.pop('args', None)
            # if args is not None:
            #    if len(args) != 0:
            #        if args[0] != '[':
            #            args = f'["{args}"]'
            #        self.exec_logger.debug(f'args to decode: {args}')
            #        args = json.loads(args) if args != '[]' else None
            #        self.exec_logger.debug(f'Decoded args {args}')
            #    else:
            #        args = None
            kwargs = decoded_message.pop('kwargs', None)
            # if kwargs is not None:
            #     if len(kwargs) != 0:
            #         if kwargs[0] != '{':
            #             kwargs = '{"' + kwargs + '"}'
            #         self.exec_logger.debug(f'kwargs to decode: {kwargs}')
            #         kwargs = json.loads(kwargs) if kwargs != '' else None
            #         self.exec_logger.debug(f'Decoded kwargs {kwargs}')
            #     else:
            #         kwargs = None
            self.exec_logger.debug(f"Calling method {cmd}({str(kwargs) if kwargs is not None else ''})")
            # self.exec_logger.debug(f"Calling method {cmd}({str(args) + ', ' if args is not None else ''}"
            #                        f"{str(kwargs) if kwargs is not None else ''})")
            if cmd_id is None:
                self.exec_logger.warning('You should use a unique identifier for cmd_id')
            if cmd is not None:
                try:
                    # if args is None:
                    #     if kwargs is None:
                    #         output = getattr(self, cmd)()
                    #     else:
                    #         output = getattr(self, cmd)(**kwargs)
                    # else:
                    if kwargs is None:
                        output = getattr(self, cmd)()
                    else:
                        output = getattr(self, cmd)(**kwargs)
                    status = True
                except Exception as e:
                    self.exec_logger.error(
                        f"Unable to execute {cmd}({str(kwargs) if kwargs is not None else ''}): {e}")
                    status = False
        except Exception as e:
            self.exec_logger.warning(f'Unable to decode command {message}: {e}')
            status = False
        finally:
            reply = {'cmd_id': cmd_id, 'status': status}
            reply = json.dumps(reply)
            self.exec_logger.debug(f'Execution report: {reply}')

    def quit(self, cmd_id=None):
        """Quits OhmPi

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier
        """

        self.exec_logger.debug(f'Quitting ohmpi.py following command {cmd_id}')
        exit()

    def _read_hardware_config(self):
        """Reads hardware configuration from config.py
        """
        self.exec_logger.debug('Getting hardware config')
        self.id = OHMPI_CONFIG['id']  # ID of the OhmPi
        self.r_shunt = OHMPI_CONFIG['R_shunt']  # reference resistance value in ohm
        self.Imax = OHMPI_CONFIG['Imax']  # maximum current
        self.exec_logger.debug(f'The maximum current cannot be higher than {self.Imax} mA')
        self.coef_p2 = OHMPI_CONFIG['coef_p2']  # slope for current conversion for ads.P2, measurement in V/V
        self.nb_samples = OHMPI_CONFIG['nb_samples']  # number of samples measured for each stack
        self.version = OHMPI_CONFIG['version']  # hardware version
        self.max_elec = OHMPI_CONFIG['max_elec']  # maximum number of electrodes
        self.board_addresses = OHMPI_CONFIG['board_addresses']
        self.board_version = OHMPI_CONFIG['board_version']
        self.mcp_board_address = OHMPI_CONFIG['mcp_board_address']
        self.exec_logger.debug(f'OHMPI_CONFIG = {str(OHMPI_CONFIG)}')

    def remove_data(self, cmd_id=None):
        """Remove all data in the data folder

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier
        """
        self.exec_logger.debug(f'Removing all data following command {cmd_id}')
        shutil.rmtree('data')
        os.mkdir('data')

    def restart(self, cmd_id=None):
        """Restarts the Raspberry Pi

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier
        """

        if self.on_pi:
            self.exec_logger.info(f'Restarting pi following command {cmd_id}...')
            os.system('reboot')
        else:
            self.exec_logger.warning('Not on Raspberry Pi, skipping reboot...')

    def run_measurement(self, quad=None, nb_stack=None, injection_duration=None,
                        autogain=True, strategy='constant', tx_volt=5., best_tx_injtime=0.1,
                        cmd_id=None):
        """Measures on a quadrupole and returns transfer resistance.

        Parameters
        ----------
        quad : iterable (list of int)
            Quadrupole to measure, just for labelling. Only switch_mux_on/off
            really create the route to the electrodes.
        nb_stack : int, optional
            Number of stacks. A stack is considered two half-cycles (one
            positive, one negative).
        injection_duration : int, optional
            Injection time in seconds.
        autogain : bool, optional
            If True, will adapt the gain of the ADS1115 to maximize the
            resolution of the reading.
        strategy : str, optional
            (V3.0 only) If we search for best voltage (tx_volt == 0), we can choose
            vmax strategy : find the highest voltage that stays in the range
            For a constant value, just set the tx_volt.
        tx_volt : float, optional
            (V3.0 only) If specified, voltage will be imposed. If 0, we will look
            for the best voltage. If the best Tx cannot be found, no
            measurement will be taken and values will be NaN.
        best_tx_injtime : float, optional
            (V3.0 only) Injection time in seconds used for finding the best voltage.
        cmd_id : str, optional
            Unique command identifier
        """
        self.exec_logger.debug('Starting measurement')
        self.exec_logger.debug('Waiting for data')

        # check arguments
        if quad is None:
            quad = [0, 0, 0, 0]

        if self.on_pi: # TODO : Remove this condition?
            if nb_stack is None:
                nb_stack = self.settings['nb_stack']
            if injection_duration is None:
                injection_duration = self.settings['injection_duration']
            tx_volt = float(tx_volt)

            # inner variable initialization
            sum_i = 0
            sum_vmn = 0
            sum_ps = 0

            # # let's define the pin again as if we run through measure()
            # # as it's run in another thread, it doesn't consider these
            # # and this can lead to short circuit!
            #
            # self.pin0 = self.mcp_board.get_pin(0)
            # self.pin0.direction = Direction.OUTPUT
            # self.pin0.value = False
            # self.pin1 = self.mcp_board.get_pin(1)
            # self.pin1.direction = Direction.OUTPUT
            # self.pin1.value = False
            # self.pin7 = self.mcp_board.get_pin(7) #IHM on mesaurement
            # self.pin7.direction = Direction.OUTPUT
            # self.pin7.value = False

            # if self.sequence is None:
#                 if self.idps:
#
#                     # self.switch_dps('on')
#                     self.pin2 = self.mcp_board.get_pin(2) # dsp +
#                     self.pin2.direction = Direction.OUTPUT
#                     self.pin2.value = True
#                     self.pin3 = self.mcp_board.get_pin(3) # dsp -
#                     self.pin3.direction = Direction.OUTPUT
#                     self.pin3.value = True
#                     time.sleep(4)
#
#             self.pin5 = self.mcp_board.get_pin(5) #IHM on mesaurement
#             self.pin5.direction = Direction.OUTPUT
#             self.pin5.value = True
#             self.pin6 = self.mcp_board.get_pin(6) #IHM on mesaurement
#             self.pin6.direction = Direction.OUTPUT
#             self.pin6.value = False
#             self.pin7 = self.mcp_board.get_pin(7) #IHM on mesaurement
#             self.pin7.direction = Direction.OUTPUT
#             self.pin7.value = False
#             if self.idps:
#                 if self.DPS.read_register(0x05,2) < 11:
#                     self.pin7.value = True# max current allowed (100 mA for relays) #voltage
#
#             # get best voltage to inject AND polarity
#             if self.idps:
#                 tx_volt, polarity, Rab = self._compute_tx_volt(
#                     best_tx_injtime=best_tx_injtime, strategy=strategy, tx_volt=tx_volt)
#                 self.exec_logger.debug(f'Best VAB found is {tx_volt:.3f}V')
#             else:
#                 polarity = 1
#                 Rab = None
#
#             # first reset the gain to 2/3 before trying to find best gain (mode 0 is continuous)
#             self.ads_current = ads.ADS1115(self.i2c, gain=2 / 3, data_rate=860,
#                                            address=self.ads_current_address, mode=0)
#             self.ads_voltage = ads.ADS1115(self.i2c, gain=2 / 3, data_rate=860,
#                                            address=self.ads_voltage_address, mode=0)
#             # turn on the power supply
#             start_delay = None
#             end_delay = None
#             out_of_range = False
#             if self.idps:
#                 if not np.isnan(tx_volt):
#                     self.DPS.write_register(0x0000, tx_volt, 2)  # set tx voltage in V
#                     self.DPS.write_register(0x09, 1)  # DPS5005 on
#                     time.sleep(0.3)
#                 else:
#                     self.exec_logger.debug('No best voltage found, will not take measurement')
#                     out_of_range = True
#
#             if not out_of_range:  # we found a Vab in the range so we measure
#                 if autogain:
#
#                     # compute autogain
#                     gain_voltage = []
#                     for n in [0,1]:  # make short cycle for gain computation
#                         self.ads_voltage = ads.ADS1115(self.i2c, gain=2 / 3, data_rate=860,
#                                                        address=self.ads_voltage_address, mode=0)
#                         if n == 0:
#                             self.pin0.value = True
#                             self.pin1.value = False
#                             if self.board_version == 'mb.2023.0.0':
#                                 self.pin6.value = True # IHM current injection led on
#                         else:
#                             self.pin0.value = False
#                             self.pin1.value = True  # current injection nr2
#                             if self.board_version == 'mb.2023.0.0':
#                                 self.pin6.value = True # IHM current injection led on
#
#                         time.sleep(injection_duration)
#                         gain_current = self._gain_auto(AnalogIn(self.ads_current, ads.P0))
#
#                         if polarity > 0:
#                             if n == 0:
#                                 gain_voltage.append(self._gain_auto(AnalogIn(self.ads_voltage, ads.P0)))
#                             else:
#                                 gain_voltage.append(self._gain_auto(AnalogIn(self.ads_voltage, ads.P2)))
#                         else:
#                             if n == 0:
#                                 gain_voltage.append(self._gain_auto(AnalogIn(self.ads_voltage, ads.P2)))
#                             else:
#                                 gain_voltage.append(self._gain_auto(AnalogIn(self.ads_voltage, ads.P0)))
#
#                         self.pin0.value = False
#                         self.pin1.value = False
#                         time.sleep(injection_duration)
#                         if n == 0:
#                             gain_voltage.append(self._gain_auto(AnalogIn(self.ads_voltage, ads.P0)))
#                         else:
#                             gain_voltage.append(self._gain_auto(AnalogIn(self.ads_voltage, ads.P2)))
#                         if self.board_version == 'mb.2023.0.0':
#                             self.pin6.value = False # IHM current injection led off
#
#                     self.exec_logger.debug(f'Gain current: {gain_current:.3f}, gain voltage: {gain_voltage[0]:.3f}, '
#                                            f'{gain_voltage[1]:.3f}')
#                     self.ads_current = ads.ADS1115(self.i2c, gain=gain_current, data_rate=860,
#                                                 address=self.ads_current_address, mode=0)
#
#                 self.pin0.value = False
#                 self.pin1.value = False
#
#                 # one stack = 2 half-cycles (one positive, one negative)
#                 pinMN = 0 if polarity > 0 else 2  # noqa
#
#                 # sampling for each stack at the end of the injection
#                 sampling_interval = 10  # ms    # TODO: make this a config option
#                 self.nb_samples = int(injection_duration * 1000 // sampling_interval) + 1  #TODO: check this strategy
#
#                 # full data for waveform
#                 fulldata = []
#
#                 #  we sample every 10 ms (as using AnalogIn for both current
#                 # and voltage takes about 7 ms). When we go over the injection
#                 # duration, we break the loop and truncate the meas arrays
#                 # only the last values in meas will be taken into account
#                 start_time = time.time()  # start counter
#                 for n in range(0, nb_stack * 2):  # for each half-cycles
#                     # current injection
#                     if (n % 2) == 0:
#                         self.pin0.value = True
#                         self.pin1.value = False
#                         if autogain: # select gain computed on first half cycle
#                             self.ads_voltage = ads.ADS1115(self.i2c, gain=np.min(gain_voltage), data_rate=860,
#                                                            address=self.ads_voltage_address, mode=0)
#                     else:
#                         self.pin0.value = False
#                         self.pin1.value = True  # current injection nr2
#                         if autogain: # select gain computed on first half cycle
#                             self.ads_voltage = ads.ADS1115(self.i2c, gain=np.min(gain_voltage),data_rate=860,
#                                                            address=self.ads_voltage_address, mode=0)
#                     self.exec_logger.debug(f'Stack {n} {self.pin0.value} {self.pin1.value}')
#                     if self.board_version == 'mb.2023.0.0':
#                         self.pin6.value = True  # IHM current injection led on
#                     # measurement of current i and voltage u during injection
#                     meas = np.zeros((self.nb_samples, 3)) * np.nan
#                     start_delay = time.time()  # stating measurement time
#                     dt = 0
#                     k = 0
#                     for k in range(0, self.nb_samples):
#                         # reading current value on ADS channels
#                         meas[k, 0] = (AnalogIn(self.ads_current, ads.P0).voltage * 1000) / (50 * self.r_shunt)
#                         if self.board_version == 'mb.2023.0.0':
#                             if pinMN == 0:
#                                 meas[k, 1] = AnalogIn(self.ads_voltage, ads.P0).voltage * 1000
#                             else:
#                                 meas[k, 1] = -AnalogIn(self.ads_voltage, ads.P2).voltage * 1000
#                         elif self.board_version == '22.10':
#                             meas[k, 1] = -AnalogIn(self.ads_voltage, ads.P0, ads.P1).voltage * self.coef_p2 * 1000
#                         # else:
#                         #    self.exec_logger.debug('Unknown board')
#                         time.sleep(sampling_interval / 1000)
#                         dt = time.time() - start_delay  # real injection time (s)
#                         meas[k, 2] = time.time() - start_time
#                         if dt > (injection_duration - 0 * sampling_interval / 1000.):
#                             break
#
#                     # stop current injection
#                     self.pin0.value = False
#                     self.pin1.value = False
# #                     if autogain: # select gain computed on first half cycle
# #                             self.ads_voltage = ads.ADS1115(self.i2c, gain=gain_voltage[2],data_rate=860,
# #                                                            address=self.ads_voltage_address, mode=0)
#                     self.pin6.value = False# IHM current injection led on
#                     end_delay = time.time()
#
#                     # truncate the meas array if we didn't fill the last samples  #TODO: check why
#                     meas = meas[:k + 1]
#
#                     # measurement of current i and voltage u during off time
#                     measpp = np.zeros((meas.shape[0], 3)) * np.nan
#                     start_delay = time.time()  # stating measurement time
#                     dt = 0
#                     for k in range(0, measpp.shape[0]):
#                         # reading current value on ADS channels
#                         measpp[k, 0] = (AnalogIn(self.ads_current, ads.P0).voltage * 1000.) / (50 * self.r_shunt)
#                         if self.board_version == 'mb.2023.0.0':
#                             if pinMN == 0:
#                                 measpp[k, 1] = AnalogIn(self.ads_voltage, ads.P0).voltage * 1000.
#                             else:
#                                 measpp[k, 1] = AnalogIn(self.ads_voltage, ads.P2).voltage * 1000. * -1
#                         elif self.board_version == '22.10':
#                             measpp[k, 1] = -AnalogIn(self.ads_voltage, ads.P0, ads.P1).voltage * self.coef_p2 * 1000.
#                         else:
#                             self.exec_logger.debug('unknown board')
#                         time.sleep(sampling_interval / 1000)
#                         dt = time.time() - start_delay  # real injection time (s)
#                         measpp[k, 2] = time.time() - start_time
#                         if dt > (injection_duration - 0 * sampling_interval / 1000.):
#                             break
#
#                     end_delay = time.time()
#
#                     # truncate the meas array if we didn't fill the last samples
#                     measpp = measpp[:k + 1]
#
#                     # we alternate on which ADS1115 pin we measure because of sign of voltage
#                     if pinMN == 0:
#                         pinMN = 2  # noqa
#                     else:
#                         pinMN = 0  # noqa
#
#                     # store data for full wave form
#                     fulldata.append(meas)
#                     fulldata.append(measpp)
#
#                 # TODO get battery voltage and warn if battery is running low
#                 # TODO send a message on SOH stating the battery level
#
#                 # let's do some calculation (out of the stacking loop)
#
#                 # i_stack = np.empty(2 * nb_stack, dtype=object)
#                 # vmn_stack = np.empty(2 * nb_stack, dtype=object)
#                 i_stack, vmn_stack = [], []
#                 # select appropriate window length to average the readings
#                 window = int(np.min([f.shape[0] for f in fulldata[::2]]) // 3)
#                 for n, meas in enumerate(fulldata[::2]):
#                     # take average from the samples per stack, then sum them all
#                     # average for the last third of the stacked values
#                     #  is done outside the loop
#                     i_stack.append(meas[-int(window):, 0])
#                     vmn_stack.append(meas[-int(window):, 1])
#
#                     sum_i = sum_i + (np.mean(meas[-int(meas.shape[0] // 3):, 0]))
#                     vmn1 = np.mean(meas[-int(meas.shape[0] // 3), 1])
#                     if (n % 2) == 0:
#                         sum_vmn = sum_vmn - vmn1
#                         sum_ps = sum_ps + vmn1
#                     else:
#                         sum_vmn = sum_vmn + vmn1
#                         sum_ps = sum_ps + vmn1
#
#             else:
#                 sum_i = np.nan
#                 sum_vmn = np.nan
#                 sum_ps = np.nan
#                 fulldata = None
#
#             if self.idps:
#                 self.DPS.write_register(0x0000, 0, 2)  # reset to 0 volt
#                 self.DPS.write_register(0x09, 0)  # DPS5005 off
#
#             # reshape full data to an array of good size
#             # we need an array of regular size to save in the csv
#             if not out_of_range:
#                 fulldata = np.vstack(fulldata)
#                 # we create a big enough array given nb_samples, number of
#                 # half-cycles (1 stack = 2 half-cycles), and twice as we
#                 # measure decay as well
#                 a = np.zeros((nb_stack * self.nb_samples * 2 * 2, 3)) * np.nan
#                 a[:fulldata.shape[0], :] = fulldata
#                 fulldata = a
#             else:
#                 np.array([[]])
#
#             vmn_stack_mean = np.mean([np.diff(np.mean(vmn_stack[i*2:i*2+2], axis=1)) / 2 for i in range(nb_stack)])
#             vmn_std =np.sqrt(np.std(vmn_stack[::2])**2 + np.std(vmn_stack[1::2])**2) # np.sum([np.std(vmn_stack[::2]),np.std(vmn_stack[1::2])])
#             i_stack_mean = np.mean(i_stack)
#             i_std = np.mean(np.array([np.std(i_stack[::2]), np.std(i_stack[1::2])]))
#             r_stack_mean = vmn_stack_mean / i_stack_mean
#             r_stack_std = np.sqrt((vmn_std/vmn_stack_mean)**2 + (i_std/i_stack_mean)**2) * r_stack_mean
#             ps_stack_mean = np.mean(np.array([np.mean(np.mean(vmn_stack[i * 2:i * 2 + 2], axis=1)) for i in range(nb_stack)]))

            # create a dictionary and compute averaged values from all stacks
            # if self.board_version == 'mb.2023.0.0':
            # d = {
            #     "time": datetime.now().isoformat(),
            #     "A": quad[0],
            #     "B": quad[1],
            #     "M": quad[2],
            #     "N": quad[3],
            #     "inj time [ms]": (end_delay - start_delay) * 1000. if not out_of_range else 0.,
            #     "Vmn [mV]": sum_vmn / (2 * nb_stack),
            #     "I [mA]": sum_i / (2 * nb_stack),
            #     "R [ohm]": sum_vmn / sum_i,
            #     "Ps [mV]": sum_ps / (2 * nb_stack),
            #     "nbStack": nb_stack,
            #     "Tx [V]": tx_volt if not out_of_range else 0.,
            #     "CPU temp [degC]": self._hw.cpu_temperature,
            #     "Nb samples [-]": self.nb_samples,
            #     "fulldata": fulldata,
            #     "I_stack [mA]": i_stack_mean,
            #     "I_std [mA]": i_std,
            #     "I_per_stack [mA]": np.array([np.mean(i_stack[i*2:i*2+2]) for i in range(nb_stack)]),
            #     "Vmn_stack [mV]": vmn_stack_mean,
            #     "Vmn_std [mV]": vmn_std,
            #     "Vmn_per_stack [mV]": np.array([np.diff(np.mean(vmn_stack[i*2:i*2+2], axis=1))[0] / 2 for i in range(nb_stack)]),
            #     "R_stack [ohm]": r_stack_mean,
            #     "R_std [ohm]": r_stack_std,
            #     "R_per_stack [Ohm]": np.mean([np.diff(np.mean(vmn_stack[i*2:i*2+2], axis=1)) / 2 for i in range(nb_stack)]) / np.array([np.mean(i_stack[i*2:i*2+2]) for i in range(nb_stack)]),
            #     "PS_per_stack [mV]":  np.array([np.mean(np.mean(vmn_stack[i*2:i*2+2], axis=1)) for i in range(nb_stack)]),
            #     "PS_stack [mV]": ps_stack_mean,
            #     "R_ab [ohm]": Rab
            # }
                # print(np.array([(vmn_stack[i*2:i*2+2]) for i in range(nb_stack)]))
            # elif self.board_version == '22.10':
            #     d = {
            #         "time": datetime.now().isoformat(),
            #         "A": quad[0],
            #         "B": quad[1],
            #         "M": quad[2],
            #         "N": quad[3],
            #         "inj time [ms]": (end_delay - start_delay) * 1000. if not out_of_range else 0.,
            #         "Vmn [mV]": sum_vmn / (2 * nb_stack),
            #         "I [mA]": sum_i / (2 * nb_stack),
            #         "R [ohm]": sum_vmn / sum_i,
            #         "Ps [mV]": sum_ps / (2 * nb_stack),
            #         "nbStack": nb_stack,
            #         "Tx [V]": tx_volt if not out_of_range else 0.,
            #         "CPU temp [degC]": CPUTemperature().temperature,
            #         "Nb samples [-]": self.nb_samples,
            #         "fulldata": fulldata,
            #     }
            d = {}

        else:  # for testing, generate random data
            d = {'time': datetime.now().isoformat(), 'A': quad[0], 'B': quad[1], 'M': quad[2], 'N': quad[3],
                 'R [ohm]': np.abs(np.random.randn(1)).tolist()}

        # to the data logger
        dd = d.copy()
        dd.pop('fulldata')  # too much for logger
        dd.update({'A': str(dd['A'])})
        dd.update({'B': str(dd['B'])})
        dd.update({'M': str(dd['M'])})
        dd.update({'N': str(dd['N'])})

        # round float to 2 decimal
        for key in dd.keys():  # Check why this is applied on keys and not values...
            if isinstance(dd[key], float):
                dd[key] = np.round(dd[key], 3)

        dd['cmd_id'] = str(cmd_id)
        self.data_logger.info(dd)
        # self.pin5.value = False #IHM led on measurement off
        # if self.sequence is None :
        #     self.switch_dps('off')

        return d

    def run_multiple_sequences(self, cmd_id=None, sequence_delay=None, nb_meas=None, **kwargs):
        """Runs multiple sequences in a separate thread for monitoring mode.
           Can be stopped by 'OhmPi.interrupt()'.
           Additional arguments are passed to run_measurement().

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier
        sequence_delay : int, optional
            Number of seconds at which the sequence must be started from each others.
        nb_meas : int, optional
            Number of time the sequence must be repeated.
        kwargs : dict, optional
            See help(k.run_measurement) for more info.
        """
        # self.run = True
        if sequence_delay is None:
            sequence_delay = self.settings['sequence_delay']
        sequence_delay = int(sequence_delay)
        if nb_meas is None:
            nb_meas = self.settings['nb_meas']
        self.status = 'running'
        self.exec_logger.debug(f'Status: {self.status}')
        self.exec_logger.debug(f'Measuring sequence: {self.sequence}')

        def func():
            for g in range(0, nb_meas):  # for time-lapse monitoring
                if self.status == 'stopping':
                    self.exec_logger.warning('Data acquisition interrupted')
                    break
                t0 = time.time()
                self.run_sequence(**kwargs)

                # sleeping time between sequence
                dt = sequence_delay - (time.time() - t0)
                if dt < 0:
                    dt = 0
                if nb_meas > 1:
                    time.sleep(dt)  # waiting for next measurement (time-lapse)
            self.status = 'idle'

        self.thread = threading.Thread(target=func)
        self.thread.start()

    def run_sequence(self, cmd_id=None, **kwargs):
        """Runs sequence synchronously (=blocking on main thread).
           Additional arguments are passed to run_measurement().

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier
        """
        self.status = 'running'
        self.exec_logger.debug(f'Status: {self.status}')
        self.exec_logger.debug(f'Measuring sequence: {self.sequence}')
        t0 = time.time()
        self.reset_mux()
        
        # create filename with timestamp
        filename = self.settings["export_path"].replace('.csv',
                                                        f'_{datetime.now().strftime("%Y%m%dT%H%M%S")}.csv')
        self.exec_logger.debug(f'Saving to {filename}')

        # make sure all multiplexer are off
        

        # measure all quadrupole of the sequence
        if self.sequence is None:
            n = 1
        else:
            n = self.sequence.shape[0]
        for i in range(0, n):
            if self.sequence is None:
                quad = np.array([0, 0, 0, 0])
            else:
                quad = self.sequence[i, :]  # quadrupole
            if self.status == 'stopping':
                break
            # if i == 0:
            #     # call the switch_mux function to switch to the right electrodes
            #     # switch on DPS
            #     self.mcp_board = MCP23008(self.i2c, address=self.mcp_board_address)
            #     self.pin2 = self.mcp_board.get_pin(2) # dsp -
            #     self.pin2.direction = Direction.OUTPUT
            #     self.pin2.value = True
            #     self.pin3 = self.mcp_board.get_pin(3) # dsp -
            #     self.pin3.direction = Direction.OUTPUT
            #     self.pin3.value = True
            #     time.sleep (4)
            #
            #     #self.switch_dps('on')
            # time.sleep(.6)
            # self.switch_mux_on(quad)
            # run a measurement
            if self.on_pi:
                acquired_data = self.run_measurement(quad, **kwargs)
            else:  # for testing, generate random data
                sum_vmn = np.random.rand(1)[0] * 1000.
                sum_i = np.random.rand(1)[0] * 100.
                cmd_id = np.random.randint(1000)
                acquired_data = {
                    "time": datetime.now().isoformat(),
                    "A": quad[0],
                    "B": quad[1],
                    "M": quad[2],
                    "N": quad[3],
                    "inj time [ms]": self.settings['injection_duration'] * 1000.,
                    "Vmn [mV]": sum_vmn,
                    "I [mA]": sum_i,
                    "R [ohm]": sum_vmn / sum_i,
                    "Ps [mV]": np.random.randn(1)[0] * 100.,
                    "nbStack": self.settings['nb_stack'],
                    "Tx [V]": np.random.randn(1)[0] * 5.,
                    "CPU temp [degC]": np.random.randn(1)[0] * 50.,
                    "Nb samples [-]": self.nb_samples,
                }
                self.data_logger.info(acquired_data)

            # # switch mux off
            # self.switch_mux_off(quad)
            #
            # # add command_id in dataset
            acquired_data.update({'cmd_id': cmd_id})
            # log data to the data logger
            # self.data_logger.info(f'{acquired_data}')
            # save data and print in a text file
            self.append_and_save(filename, acquired_data)
            self.exec_logger.debug(f'quadrupole {i + 1:d}/{n:d}')

        # self.switch_dps('off')
        self.status = 'idle'

    def run_sequence_async(self, cmd_id=None, **kwargs):
        """Runs the sequence in a separate thread. Can be stopped by 'OhmPi.interrupt()'.
            Additional arguments are passed to run_measurement().

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier
        """

        def func():
            self.run_sequence(**kwargs)

        self.thread = threading.Thread(target=func)
        self.thread.start()
        self.status = 'idle'

    def rs_check(self, tx_volt=12., cmd_id=None): # TODO: we could build a smarter RS-Check by selecting adjacent electrodes based on their locations and try to isolate electrodes that are responsible for high resistances (ex: AB high, AC low, BC high -> might be a problem at B (cf what we did with WofE)
        """Checks contact resistances

        Parameters
        ----------
        tx_volt : float
            Voltage of the injection
        cmd_id : str, optional
            Unique command identifier
        """
        # create custom sequence where MN == AB
        # we only check the electrodes which are in the sequence (not all might be connected)
        if self.sequence is None or not self.use_mux:
            quads = np.array([[1, 2, 1, 2]], dtype=np.uint32)
        else:
            elec = np.sort(np.unique(self.sequence.flatten()))  # assumed order
            quads = np.vstack([
                elec[:-1],
                elec[1:],
                elec[:-1],
                elec[1:],
            ]).T
        # if self.idps:
        #     quads[:, 2:] = 0  # we don't open Vmn to prevent burning the MN part
        #     # as it has a smaller range of accepted voltage

        # create filename to store RS
        export_path_rs = self.settings['export_path'].replace('.csv', '') \
                         + '_' + datetime.now().strftime('%Y%m%dT%H%M%S') + '_rs.csv'

        # perform RS check
        self.status = 'running'

        if self.on_pi:
            # make sure all mux are off to start with
            self._hw.mux_boards.reset_mux()

            # measure all quad of the RS sequence
            for i in range(0, quads.shape[0]):
                quad = quads[i, :]  # quadrupole
                self.switch_mux_on(quad)  # put before raising the pins (otherwise conflict i2c)
                d = self.run_measurement(quad=quad, nb_stack=1, injection_duration=0.2, tx_volt=tx_volt, autogain=False)

                if self.idps:
                    voltage = tx_volt * 1000.  # imposed voltage on dps5005
                else:
                    voltage = d['Vmn [mV]']
                current = d['I [mA]']

                # compute resistance measured (= contact resistance)
                resist = abs(voltage / current) / 1000.
                # print(str(quad) + '> I: {:>10.3f} mA, V: {:>10.3f} mV, R: {:>10.3f} kOhm'.format(
                #    current, voltage, resist))
                msg = f'Contact resistance {str(quad):s}: I: {current * 1000.:>10.3f} mA, ' \
                      f'V: {voltage :>10.3f} mV, ' \
                      f'R: {resist :>10.3f} kOhm'

                self.exec_logger.debug(msg)

                # if contact resistance = 0 -> we have a short circuit!!
                if resist < 1e-5:
                    msg = f'!!!SHORT CIRCUIT!!! {str(quad):s}: {resist:.3f} kOhm'
                    self.exec_logger.warning(msg)

                # save data in a text file
                self.append_and_save(export_path_rs, {
                    'A': quad[0],
                    'B': quad[1],
                    'RS [kOhm]': resist,
                })

                # close mux path and put pin back to GND
                self.switch_mux_off(quad)
        else:
            pass
        self.status = 'idle'

    #
    #         # TODO if interrupted, we would need to restore the values
    #         # TODO or we offer the possibility in 'run_measurement' to have rs_check each time?

    def set_sequence(self, sequence=None, cmd_id=None):
        """Sets the sequence to acquire

        Parameters
        ----------
        sequence : list, str
            sequence of quadrupoles
        cmd_id: str, optional
            Unique command identifier
        """
        try:
            self.sequence = np.array(sequence).astype(int)
            # self.sequence = np.loadtxt(StringIO(sequence)).astype('uint32')
            status = True
        except Exception as e:
            self.exec_logger.warning(f'Unable to set sequence: {e}')
            status = False

    def switch_dps(self, state='off'):
        """Switches DPS on or off.

            Parameters
            ----------
            state : str
                'on', 'off'
            """
        self._hw.switch_dps(state=state)

    def switch_mux_on(self, quadrupole, cmd_id=None):
        """Switches on multiplexer relays for given quadrupole.

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier
        quadrupole : list of 4 int
            List of 4 integers representing the electrode numbers.
        """

        self._hw.switch_mux(electrodes=quadrupole, state='on')

    def switch_mux_off(self, quadrupole, cmd_id=None):
        """Switches off multiplexer relays for given quadrupole.

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier
        quadrupole : list of 4 int
            List of 4 integers representing the electrode numbers.
        """

        self._hw.switch_mux(electrodes=quadrupole, state='off')

    def test_mux(self, activation_time=1.0, mux_id=None, cmd_id=None): # TODO: add this in the MUX code
        """Interactive method to test the multiplexer boards.

        Parameters
        ----------
        activation_time : float, optional
            Time in seconds during which the relays are activated.
        mux_id : str, optional
            id of the mux_board to test
        cmd_id : str, optional
            Unique command identifier
        """
        self.reset_mux() # All mux boards should be reset even if we only want to test one otherwise we might create a shortcut
        if mux_id is None:
            self._hw.test_mux(activation_time)
        else:
            self._hw.mux_boards[mux_id].test(activation_time=activation_time)


    def reset_mux(self, cmd_id=None):
        """Switches off all multiplexer relays.

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier
        """
        self._hw.reset_mux()

    def update_settings(self, settings: str, cmd_id=None):
        """Updates acquisition settings from a json file or dictionary.
        Parameters can be:
            - nb_electrodes (number of electrode used, if 4, no MUX needed)
            - injection_duration (in seconds)
            - nb_meas (total number of times the sequence will be run)
            - sequence_delay (delay in second between each sequence run)
            - nb_stack (number of stack for each quadrupole measurement)
            - export_path (path where to export the data, timestamp will be added to filename)

        Parameters
        ----------
        settings : str, dict
            Path to the .json settings file or dictionary of settings.
        cmd_id : str, optional
            Unique command identifier
        """
        status = False
        if settings is not None:
            try:
                if isinstance(settings, dict):
                    self.settings.update(settings)
                else:
                    with open(settings) as json_file:
                        dic = json.load(json_file)
                    self.settings.update(dic)
                self.exec_logger.debug('Acquisition parameters updated: ' + str(self.settings))
                status = True
            except Exception as e:  # noqa
                self.exec_logger.warning('Unable to update settings.')
                status = False
        else:
            self.exec_logger.warning('Settings are missing...')
        return status

    # Properties
    @property
    def sequence(self):
        """Gets sequence"""
        if self._sequence is not None:
            assert isinstance(self._sequence, np.ndarray)
        return self._sequence

    @sequence.setter
    def sequence(self, sequence):
        """Sets sequence"""
        if sequence is not None:
            assert isinstance(sequence, np.ndarray)
        self._sequence = sequence


VERSION = '2.2.0-alpha'

print(colored(r' ________________________________' + '\n' +
              r'|  _  | | | ||  \/  || ___ \_   _|' + '\n' +
              r'| | | | |_| || .  . || |_/ / | |' + '\n' +
              r'| | | |  _  || |\/| ||  __/  | |' + '\n' +
              r'\ \_/ / | | || |  | || |    _| |_' + '\n' +
              r' \___/\_| |_/\_|  |_/\_|    \___/ ', 'red'))
print('Version:', VERSION)
platform, on_pi = get_platform()

if on_pi:
    print(colored(f'\u2611 Running on {platform} platform', 'green'))
    # TODO: check model for compatible platforms (exclude Raspberry Pi versions that are not supported...)
    #       and emit a warning otherwise
    if not arm64_imports:
        print(colored(f'Warning: Required packages are missing.\n'
                      f'Please run ./env.sh at command prompt to update your virtual environment\n', 'yellow'))
else:
    print(colored(f'\u26A0 Not running on the Raspberry Pi platform.\nFor simulation purposes only...', 'yellow'))

current_time = datetime.now()
print(f'local date and time : {current_time.strftime("%Y-%m-%d %H:%M:%S")}')

# for testing
if __name__ == "__main__":
    ohmpi = OhmPi(settings=OHMPI_CONFIG['settings'])
    if ohmpi.controller is not None:
        ohmpi.controller.loop_forever()
