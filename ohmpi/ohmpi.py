# -*- coding: utf-8 -*-
"""
created on January 6, 2020.
Updates dec 2023; in-depth refactoring May 2023.
Hardware: Licensed under CERN-OHL-S v2 or any later version
Software: Licensed under the GNU General Public License v3.0
Ohmpi.py is a program to control a low-cost and open hardware resistivity meters within the OhmPi project by
Rémi CLEMENT (INRAE), Vivien DUBOIS (INRAE), Hélène GUYARD (IGE), Nicolas FORQUET (INRAE), Yannick FARGIER (IFSTTAR)
Olivier KAUFMANN (UMONS), Arnaud WATLET (UMONS) and Guillaume BLANCHY (FNRS/ULiege).
"""

import os
import json
from copy import deepcopy
import numpy as np
import csv
import time
from shutil import rmtree, make_archive
from threading import Thread
from inspect import getmembers, isfunction
from datetime import datetime
from termcolor import colored
from logging import DEBUG
from ohmpi.utils import get_platform
from ohmpi.logging_setup import setup_loggers
from ohmpi.config import MQTT_CONTROL_CONFIG, OHMPI_CONFIG, EXEC_LOGGING_CONFIG
import ohmpi.deprecated as deprecated
from ohmpi.hardware_system import OhmPiHardware

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

VERSION = '3.0.0-beta'


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
            assert get_platform()[1]  # Checks that the system actually runs on a pi if onpi is True
        self.on_pi = onpi  # True if runs from the RaspberryPi with the hardware, otherwise False for random data # TODO : replace with dummy hardware?

        self._sequence = sequence
        self.nb_samples = 0
        self.status = 'idle'  # either running or idle
        self.thread = None  # contains the handle for the thread taking the measurement

        # set loggers
        self.exec_logger, _, self.data_logger, _, self.soh_logger, _, _, msg = setup_loggers(mqtt=mqtt)
        print(msg)

        # specify loggers when instancing the hardware
        self._hw = OhmPiHardware(**{'exec_logger': self.exec_logger, 'data_logger': self.data_logger,
                                    'soh_logger': self.soh_logger})
        self.exec_logger.info('Hardware configured...')
        # default acquisition settings
        self.settings = {
            'injection_duration': 0.2,
            'nb_meas': 1,
            'sequence_delay': 1,
            'nb_stack': 1,
            'sampling_interval': 2,
            'tx_volt': 5,
            'duty_cycle': 0.5,
            'strategy': 'constant',
            'export_path': None,
            'export_dir': 'data',
            'export_name': 'measurement.csv'
        }
        # read in acquisition settings
        # if settings is not None:
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

    @classmethod
    def get_deprecated_methods(cls):
        for i in getmembers(deprecated, isfunction):
            setattr(cls, i[0], i[1])

    @staticmethod
    def append_and_save(filename: str, last_measurement: dict, cmd_id=None):
        # TODO: find alternative approach to save full data (zip, hdf5 or mseed?)
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
        # check if directory 'data' exists
        ddir = os.path.join(os.path.dirname(__file__), '../data/')
        if os.path.exists(ddir) is not True:
            os.mkdir(ddir)

        last_measurement = deepcopy(last_measurement)
        
        # TODO need to make all the full data of the same size (pre-populate
        # readings with NaN in hardware_system.OhmPiHardware.read_values())
        if 'fulldata' in last_measurement:
            # d = last_measurement['fulldata']
            # n = d.shape[0]
            # if n > 1:
            #     idic = dict(zip(['i' + str(i) for i in range(n)], d[:, 0]))
            #     udic = dict(zip(['u' + str(i) for i in range(n)], d[:, 1]))
            #     tdic = dict(zip(['t' + str(i) for i in range(n)], d[:, 2]))
            #     last_measurement.update(idic)
            #     last_measurement.update(udic)
            #     last_measurement.update(tdic)
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
        If A and B were connected to the same electrode, we would create a short-circuit.

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
        ddir = os.path.join(os.path.dirname(__file__), '../data/')
        fnames = [fname for fname in os.listdir(ddir) if fname[-4:] == '.csv']
        ddic = {}
        if cmd_id is None:
            cmd_id = 'unknown'
        for fname in fnames:
            if ((fname != 'readme.txt')
                    and ('_rs' not in fname)
                    and (fname.replace('.csv', '') not in survey_names)):
                #try:
                # reading headers
                with open(os.path.join(ddir, fname), 'r') as f:
                    headers = f.readline().split(',')
                
                # fixing possible incompatibilities with code version
                for i, header in enumerate(headers):
                    if header == 'R [ohm]':
                        headers[i] = 'R [Ohm]'
                icols = list(np.where(np.in1d(headers, ['A', 'B', 'M', 'N', 'R [Ohm]']))[0])
                data = np.loadtxt(os.path.join(ddir, fname), delimiter=',',
                                    skiprows=1, usecols=icols)                    
                data = data[None, :] if len(data.shape) == 1 else data
                ddic[fname.replace('.csv', '')] = {
                    'a': data[:, 0].astype(int).tolist(),
                    'b': data[:, 1].astype(int).tolist(),
                    'm': data[:, 2].astype(int).tolist(),
                    'n': data[:, 3].astype(int).tolist(),
                    'rho': data[:, 4].tolist(),
                }
                #except Exception as e:
                #    print(fname, ':', e)
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
        self.status = 'idle'
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
        sequence : numpy.ndarray
            Array of shape (number quadrupoles * 4).
        """
        self.exec_logger.debug(f'Loading sequence {filename}')
        sequence = np.loadtxt(filename, delimiter=" ", dtype=np.uint32)  # load quadrupole file

        if sequence is not None:
            self.exec_logger.debug(f'Sequence of {sequence.shape[0]:d} quadrupoles read.')

        # locate lines where electrode A == electrode B
        test_same_elec = self._find_identical_in_line(sequence)

        if len(test_same_elec) != 0:
            for i in range(len(test_same_elec)):
                self.exec_logger.error(f'An electrode index A == B detected at line {str(test_same_elec[i] + 1)}')
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
        self.status = 'idle'
        cmd_id = '?'
        try:
            decoded_message = json.loads(message)
            self.exec_logger.debug(f'Decoded message {decoded_message}')
            cmd_id = decoded_message.pop('cmd_id', None)
            cmd = decoded_message.pop('cmd', None)
            kwargs = decoded_message.pop('kwargs', None)
            self.exec_logger.debug(f"Calling method {cmd}({str(kwargs) if kwargs is not None else ''})")
            if cmd_id is None:
                self.exec_logger.warning('You should use a unique identifier for cmd_id')
            if cmd is not None:
                try:
                    if kwargs is None:
                        output = getattr(self, cmd)()
                    else:
                        output = getattr(self, cmd)(**kwargs)
                    status = True
                except Exception as e:
                    self.exec_logger.error(
                        f"Unable to execute {cmd}({str(kwargs) if kwargs is not None else ''}): {e}")
        except Exception as e:
            self.exec_logger.warning(f'Unable to decode command {message}: {e}')
        finally:
            reply = {'cmd_id': cmd_id, 'status': self.status}
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
        # self.r_shunt = OHMPI_CONFIG['R_shunt']  # reference resistance value in ohm
        # self.Imax = OHMPI_CONFIG['Imax']  # maximum current
        # self.exec_logger.debug(f'The maximum current cannot be higher than {self.Imax} mA')
        # self.coef_p2 = OHMPI_CONFIG['coef_p2']  # slope for current conversion for ads.P2, measurement in V/V
        # self.nb_samples = OHMPI_CONFIG['nb_samples']  # number of samples measured for each stack
        # self.version = OHMPI_CONFIG['version']  # hardware version
        # self.max_elec = OHMPI_CONFIG['max_elec']  # maximum number of electrodes
        # self.board_addresses = OHMPI_CONFIG['board_addresses']
        # self.board_version = OHMPI_CONFIG['board_version']
        # self.mcp_board_address = OHMPI_CONFIG['mcp_board_address']
        self.exec_logger.debug(f'OHMPI_CONFIG = {str(OHMPI_CONFIG)}')

    def remove_data(self, cmd_id=None):
        """Remove all data in the data folder

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier
        """
        self.exec_logger.debug(f'Removing all data following command {cmd_id}')
        datadir = os.path.join(os.path.dirname(__file__), '../data')
        rmtree(datadir)
        os.mkdir(datadir)

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

    def download_data(self, cmd_id=None):
        """Create a zip of the data folder.
        """
        datadir = os.path.join(os.path.dirname(__file__), '../data/')
        make_archive(datadir, 'zip', 'data')
        self.data_logger.info(json.dumps({'download': 'ready'}))

    def shutdown(self, cmd_id=None):
        """Shutdown the Raspberry Pi

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier
        """

        if self.on_pi:
            self.exec_logger.info(f'Restarting pi following command {cmd_id}...')
            os.system('poweroff')
        else:
            self.exec_logger.warning('Not on Raspberry Pi, skipping shutdown...')

    def run_measurement(self, quad=None, nb_stack=None, injection_duration=None, duty_cycle=None,
                        autogain=True, strategy='constant', tx_volt=5., best_tx_injtime=0.1,
                        cmd_id=None, vab_max=None, iab_max=None, vmn_max=None, vmn_min=None, **kwargs):
        # TODO: add sampling_interval -> impact on _hw.rx.sampling_rate (store the current value, change the _hw.rx.sampling_rate, do the measurement, reset the sampling_rate to the previous value)
        # TODO: default value of tx_volt and other parameters set to None should be given in config.py and used in function definition
        """Measures on a quadrupole and returns transfer resistance.

        Parameters
        ----------
        quad : iterable (list of int)
            Quadrupole to measure, just for labelling. Only switch_mux_on/off
            really create the route to the electrodes.
        nb_stack : int, optional
            Number of stacks. A stack is considered two pulses (one
            positive, one negative).            If 0, we will look            for the best voltage.
        injection_duration : int, optional
            Injection time in seconds.
        duty_cycle : float, optional, Default: 0.5
            Duty cycle of injection square wave
        strategy : str, optional, default: constant
            Define injection strategy (if power is adjustable, otherwise constant tx_volt)
            Either:
            - vmax : compute Vab to reach a maximum Vmn_max and Iab without exceeding vab_max
            - vmin : compute Vab to reach at least Vmn_min
            - constant : apply given Vab (tx_volt) -
                        Safety check (i.e. short voltage pulses) performed prior to injection to ensure
                        injection within bounds defined in vab_max, iab_max, vmn_max or vmn_min. This can adapt Vab.
                        To bypass safety check before injection, tx_volt should be set equal to vab_max (not recpommanded)
        vab_max : str, optional
            Maximum injection voltage
            Default value set by config or boards specs
        iab_max : str, optional
            Maximum current applied
            Default value set by config or boards specs
        vmn_max : str, optional
            Maximum Vmn allowed
            Default value set by config or boards specs
        vmn_min :
            Minimum Vmn desired (used in strategy vmin)
            Default value set by config or boards specs
        tx_volt : float, optional  # TODO: change tx_volt to Vab
            For power adjustable only. If specified, voltage will be imposed.
        cmd_id : str, optional
            Unique command identifier
        """
        # check pwr is on, if not, let's turn it on
        switch_power_off = False
        if self._hw.pwr_state == 'off':
            self._hw.pwr_state = 'on'
            switch_power_off = True

        self.exec_logger.debug('Starting measurement')
        self.exec_logger.debug('Waiting for data')

        # check arguments
        if quad is None:
            quad = np.array([0, 0, 0, 0])
        if nb_stack is None:
            nb_stack = self.settings['nb_stack']
        if injection_duration is None:
            injection_duration = self.settings['injection_duration']
        if duty_cycle is None:
            duty_cycle = self.settings['duty_cycle']
        # quad = kwargs.pop('quad', [0,0,0,0])
        # nb_stack = kwargs.pop('nb_stack', self.settings['nb_stack'])
        # injection_duration = kwargs.pop('injection_duration', self.settings['injection_duration'])
        # duty_cycle = kwargs.pop('duty_cycle', self.settings['duty_cycle'])
        # tx_volt = float(kwargs.pop('tx_volt', self.settings['tx_volt']))
        bypass_check = kwargs['bypass_check'] if 'bypass_check' in kwargs.keys() else False
        d = {}
        if self.switch_mux_on(quad, bypass_check=bypass_check, cmd_id=cmd_id):
            tx_volt = self._hw._compute_tx_volt(tx_volt=tx_volt, strategy=strategy, vmn_max=vmn_max, vab_max=vab_max, iab_max=iab_max)  # TODO: use tx_volt and vmn_max instead of hardcoded values
            time.sleep(0.5)  # to wait for pwr discharge
            self._hw.vab_square_wave(tx_volt, cycle_duration=injection_duration*2/duty_cycle, cycles=nb_stack, duty_cycle=duty_cycle)
            if 'delay' in kwargs.keys():
                delay = kwargs['delay']
            else:
                delay = injection_duration * 2/3  # TODO: check if this is ok and if last point is not taken the end of injection
            x = np.where((self._hw.readings[:, 0] >= delay) & (self._hw.readings[:, 2] != 0))
            Vmn = self._hw.last_vmn(delay=delay)
            Vmn_std = self._hw.last_vmn_dev(delay=delay)
            I =  self._hw.last_iab(delay=delay)
            I_std =  self._hw.last_iab_dev(delay=delay)
            R = self._hw.last_resistance(delay=delay)
            R_std = self._hw.last_dev(delay=delay)
            d = {
                "time": datetime.now().isoformat(),
                "A": quad[0],
                "B": quad[1],
                "M": quad[2],
                "N": quad[3],
                "inj time [ms]": injection_duration * 1000.,  # NOTE: check this
                "Vmn [mV]": Vmn,
                "I [mA]": I,
                "R [Ohm]": R,
                "R_std [%]": R_std,
                "Ps [mV]": self._hw.sp,
                "nbStack": nb_stack,
                "Tx [V]": tx_volt,
                "CPU temp [degC]": self._hw.ctl.cpu_temperature,
                "Nb samples [-]": len(self._hw.readings[x,2]),  # TODO: use only samples after a delay in each pulse
                "fulldata": self._hw.readings[:, [0, -2, -1]],
                # "I_stack [mA]": i_stack_mean,
                "I_std [%]": I_std,
                # "I_per_stack [mA]": np.array([np.mean(i_stack[i*2:i*2+2]) for i in range(nb_stack)]),
                # "Vmn_stack [mV]": vmn_stack_mean,
                "Vmn_std [%]": Vmn_std,
                # "Vmn_per_stack [mV]": np.array([np.diff(np.mean(vmn_stack[i*2:i*2+2], axis=1))[0] / 2 for i in range(nb_stack)]),
                # "R_stack [ohm]": r_stack_mean,
                # "R_std [ohm]": r_stack_std,
                # "R_per_stack [Ohm]": np.mean([np.diff(np.mean(vmn_stack[i*2:i*2+2], axis=1)) / 2 for i in range(nb_stack)]) / np.array([np.mean(i_stack[i*2:i*2+2]) for i in range(nb_stack)]),
                # "PS_per_stack [mV]":  np.array([np.mean(np.mean(vmn_stack[i*2:i*2+2], axis=1)) for i in range(nb_stack)]),
                # "PS_stack [mV]": ps_stack_mean,
                "R_ab [kOhm]": tx_volt / I
            }

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
            self._hw.switch_mux(electrodes=quad[0:2], roles=['A', 'B'], state='on')
            time.sleep(1.0)
            self._hw.switch_mux(electrodes=quad[0:2], roles=['A', 'B'], state='off')
        else:
            self.exec_logger.info(f'Skipping {quad}')
        self.switch_mux_off(quad, cmd_id)

        # if power was off before measurement, let's turn if off
        if switch_power_off:
            self._hw.pwr_state = 'off'

        return d

    def run_multiple_sequences(self, cmd_id=None, sequence_delay=None, nb_meas=None, **kwargs):  # NOTE : could be renamed repeat_sequence
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

        # # kill previous running thread
        # if self.thread is not None:
        #     self.exec_logger.info('Removing previous thread')
        #     self.thread.stop()
        #     self.thread.join()

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
                    if self.status == 'stopping':
                        break
                    time.sleep(dt)  # waiting for next measurement (time-lapse)
            self.status = 'idle'

        self.thread = Thread(target=func)
        self.thread.start()

    def run_sequence(self, cmd_id=None, **kwargs):
        """Runs sequence synchronously (=blocking on main thread).
           Additional arguments are passed to run_measurement().

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier
        """
        # switch power on
        self._hw.pwr_state = 'on'
        self.status = 'running'
        self.exec_logger.debug(f'Status: {self.status}')
        self.exec_logger.debug(f'Measuring sequence: {self.sequence}')
        t0 = time.time()
        self.reset_mux()
        
        # create filename with timestamp
        if self.settings["export_path"] is None:
            filename = self.settings['export_path'].replace(
                '.csv', f'_{datetime.now().strftime("%Y%m%dT%H%M%S")}.csv')
        else:
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
            #     self.pin2 = self.mcp_board.get_pin(2) # dps -
            #     self.pin2.direction = Direction.OUTPUT
            #     self.pin2.value = True
            #     self.pin3 = self.mcp_board.get_pin(3) # dps -
            #     self.pin3.direction = Direction.OUTPUT
            #     self.pin3.value = True
            #     time.sleep (4)
            #
            #     #self.switch_dps('on')
            # time.sleep(.6)
            # self.switch_mux_on(quad)
            # run a measurement
            if self.on_pi:
                acquired_data = self.run_measurement(quad=quad, **kwargs)
            else:  # for testing, generate random data
                # sum_vmn = np.random.rand(1)[0] * 1000.
                # sum_i = np.random.rand(1)[0] * 100.
                # cmd_id = np.random.randint(1000)
                # acquired_data = {
                #     "time": datetime.now().isoformat(),
                #     "A": quad[0],
                #     "B": quad[1],
                #     "M": quad[2],
                #     "N": quad[3],
                #     "inj time [ms]": self.settings['injection_duration'] * 1000.,
                #     "Vmn [mV]": sum_vmn,
                #     "I [mA]": sum_i,
                #     "R [ohm]": sum_vmn / sum_i,
                #     "Ps [mV]": np.random.randn(1)[0] * 100.,
                #     "nbStack": self.settings['nb_stack'],
                #     "Tx [V]": np.random.randn(1)[0] * 5.,
                #     "CPU temp [degC]": np.random.randn(1)[0] * 50.,
                #     "Nb samples [-]": self.nb_samples,
                # }
                pass
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
        self._hw.pwr_state = 'off'

        # reset to idle if we didn't interrupt the sequence
        if self.status != 'stopping':
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

        self.thread = Thread(target=func)
        self.thread.start()
        self.status = 'idle'

    # TODO: we could build a smarter RS-Check by selecting adjacent electrodes based on their locations and try to
    #  isolate electrodes that are responsible for high resistances (ex: AB high, AC low, BC high
    #  -> might be a problem at B (cf what we did with WofE)
    def rs_check(self, tx_volt=5., cmd_id=None):
        # TODO: add a default value for rs-check in config.py import it in ohmpi.py and add it in rs_check definition
        """Checks contact resistances.
        Strategy: we just open A and B, measure the current and using vAB set or
        assumed (12V assumed for battery), we compute Rab.

        Parameters
        ----------
        tx_volt : float
            Voltage of the injection
        cmd_id : str, optional
            Unique command identifier
        """
        # check pwr is on, if not, let's turn it on
        switch_power_off = False
        if self._hw.pwr_state == 'off':
            self._hw.pwr_state = 'on'
            switch_power_off = True

        # self._hw.tx.pwr.voltage = float(tx_volt)

        # create custom sequence where MN == AB
        # we only check the electrodes which are in the sequence (not all might be connected)
        if self.sequence is None:
            quads = np.array([[1, 2, 0, 0]], dtype=np.uint32)
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

        self.reset_mux()

        # measure all quad of the RS sequence
        for i in range(0, quads.shape[0]):
            quad = quads[i, :]  # quadrupole
            self._hw.switch_mux(electrodes=list(quads[i, :2]), roles=['A', 'B'], state='on')
            self._hw._vab_pulse(duration=0.2, vab=tx_volt)
            current = self._hw.readings[-1, 3]
            voltage = self._hw.tx.pwr.voltage * 1000
            time.sleep(0.2)

            # self.switch_mux_on(quad, bypass_check=True)  # put before raising the pins (otherwise conflict i2c)
            # d = self.run_measurement(quad=quad, nb_stack=1, injection_duration=0.2, tx_volt=tx_volt, autogain=False,
            #                          bypass_check=True)

            # if self._hw.tx.voltage_adjustable:
            #     voltage = self._hw.tx.voltage  # imposed voltage on dps
            # else:
            #     voltage = self._hw.rx.voltage

            # voltage = self._hw.rx.voltage
            # current = self._hw.tx.current

            # compute resistance measured (= contact resistance)
            resist = abs(voltage / current) / 1000 # kOhm
            # print(str(quad) + '> I: {:>10.3f} mA, V: {:>10.3f} mV, R: {:>10.3f} kOhm'.format(
            #    current, voltage, resist))
            # msg = f'Contact resistance {str(quad):s}: I: {current :>10.3f} mA, ' \
            #       f'V: {voltage :>10.3f} mV, ' \
            #       f'R: {resist :>10.3f} kOhm'
            # create a message as dictionnary to be used by the html interface
            msg = {
                'rsdata': {
                    'A': int(quad[0]),
                    'B': int(quad[1]),
                    'rs': resist,  # in kOhm
                }
            }
            self.data_logger.info(json.dumps(msg))

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

        self.status = 'idle'

        # if power was off before measurement, let's turn if off
        if switch_power_off:
            self._hw.pwr_state = 'off'
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
        except Exception as e:
            self.exec_logger.warning(f'Unable to set sequence: {e}')

    def switch_mux_on(self, quadrupole, bypass_check=False, cmd_id=None):
        """Switches on multiplexer relays for given quadrupole.

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier
        quadrupole : list of 4 int
            List of 4 integers representing the electrode numbers.
        bypass_check: bool, optional
            Bypasses checks for A==M or A==N or B==M or B==N (i.e. used for rs-check)
        """
        assert len(quadrupole) == 4
        if (self._hw.tx.pwr.voltage > self._hw.rx._voltage_max) and bypass_check:
            self.exec_logger.warning('Cannot bypass checking electrode roles because tx pwr voltage is over rx maximum voltage')
            self.exec_logger.debug(f'tx pwr voltage: {self._hw.tx.pwr.voltage}, rx max voltage: {self._hw.rx._voltage_max}')
            return False
        else:
            if np.array(quadrupole).all() == np.array([0, 0, 0, 0]).all():  # NOTE: No mux
                return True
            else:
                return self._hw.switch_mux(electrodes=quadrupole, state='on', bypass_check=bypass_check)

    def switch_mux_off(self, quadrupole, cmd_id=None):
        """Switches off multiplexer relays for given quadrupole.

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier
        quadrupole : list of 4 int
            List of 4 integers representing the electrode numbers.
        """
        assert len(quadrupole) == 4
        return self._hw.switch_mux(electrodes=quadrupole, state='off')

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
            self._hw.test_mux(activation_time=activation_time)
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
            - strategy (injection strategy: constant, vmax, vmin)
            - duty_cycle (injection duty cycle comprised between 0.5 - 1)
            - export_dir (directory where to export the data)
            - export_name (name of exported file, timestamp will be added to filename)
            - export_path (path where to export the data, timestamp will be added to filename ;
                            if export_path is given, it goes over export_dir and export_name)


        Parameters
        ----------
        settings : str, dict
            Path to the .json settings file or dictionary of settings.
        cmd_id : str, optional
            Unique command identifier
        """
        if settings is not None:
            try:
                if isinstance(settings, dict):
                    self.settings.update(settings)
                    if 'sequence' in settings:
                        self.set_sequence(settings['sequence'])
                else:
                    with open(settings) as json_file:
                        dic = json.load(json_file)
                    self.settings.update(dic)
                self.exec_logger.debug('Acquisition parameters updated: ' + str(self.settings))
                self.status = 'idle (acquisition updated)'
            except Exception as e:  # noqa
                self.exec_logger.warning('Unable to update settings.')
                self.status = 'idle (unable to update settings)'
        else:
            self.exec_logger.warning('Settings are missing...')

        if self.settings['export_path'] is None:
            self.settings['export_path'] = os.path.join(self.settings['export_dir'], self.settings['export_name'])
        else:
            self.settings['export_dir'] = os.path.split(self.settings['export_path'])[0]
            self.settings['export_name'] = os.path.split(self.settings['export_path'])[1]

    def run_inversion(self, survey_names=[], elec_spacing=1, **kwargs):
        """Run a simple 2D inversion using ResIPy.
        
        Parameters
        ----------
        survey_names : list of string, optional
            Filenames of the survey to be inverted (including extension).
        elec_spacing : float (optional)
            Electrode spacing in meters. We assume same electrode spacing everywhere.
        kwargs : optional
            Additiona keyword arguments passed to `resipy.Project.invert()`. For instance
            `reg_mode` == 0 for batch inversion, `reg_mode == 2` for time-lapse inversion.
            See ResIPy document for more information on options available
            (https://hkex.gitlab.io/resipy/).

        Returns
        -------
        xzv : list of dict
            Each dictionnary with key 'x' and 'z' for the centroid of the elements and 'v'
            for the values in resistivity of the elements.
        """
        # check if we have any files to be inverted
        if len(survey_names) == 0:
            self.exec_logger.error('No file to invert')
            return []
        
        # check if user didn't provide a single string instead of a list
        if isinstance(survey_names, str):
            survey_names = [survey_names]

        # check kwargs for reg_mode
        if 'reg_mode' in kwargs:
            reg_mode = kwargs['reg_mode']
        else:
            reg_mode = 0
            kwargs['reg_mode'] = 0

        pdir = os.path.dirname(__file__)
        # import resipy if available
        try:
            from scipy.interpolate import griddata  # noqa
            import pandas as pd  #noqa
            import sys
            sys.path.append(os.path.join(pdir, '../../resipy/src/'))
            from resipy import Project  # noqa
        except Exception as e:
            self.exec_logger.error('Cannot import ResIPy, scipy or Pandas, error: ' + str(e))
            return []

        # get absolule filename
        fnames = []
        for survey_name in survey_names:
            fname = os.path.join(pdir, '../data', survey_name)
            if os.path.exists(fname):
                fnames.append(fname)
            else:
                self.exec_logger.warning(fname + ' not found')
        
        # define a parser for the "ohmpi" format
        def ohmpiParser(fname):
            df = pd.read_csv(fname)
            df = df.rename(columns={'A':'a', 'B':'b', 'M':'m', 'N':'n'})
            df['vp'] = df['Vmn [mV]']
            df['i'] = df['I [mA]']
            df['resist'] = df['vp']/df['i']
            df['ip'] = np.nan
            emax = np.max(df[['a', 'b', 'm', 'n']].values)
            elec = np.zeros((emax, 3))
            elec[:, 0] = np.arange(emax) * elec_spacing
            return elec, df[['a','b','m','n','vp','i','resist','ip']]
                
        # run inversion
        self.exec_logger.info('ResIPy: import surveys')
        k = Project(typ='R2')  # invert in a temporary directory that will be erased afterwards
        if len(survey_names) == 1:
            k.createSurvey(fnames[0], parser=ohmpiParser)
        elif len(survey_names) > 0 and reg_mode == 0:
            k.createBatchSurvey(fnames, parser=ohmpiParser)
        elif len(survey_names) > 0 and reg_mode > 0:
            k.createTimeLapseSurvey(fnames, parser=ohmpiParser)
        self.exec_logger.info('ResIPy: generate mesh')
        k.createMesh('trian', cl=elec_spacing/5)
        self.exec_logger.info('ResIPy: invert survey')
        k.invert(param=kwargs)

        # read data and regrid on a regular grid for a plotly contour plot
        self.exec_logger.info('Reading inverted surveys')
        k.getResults()
        xzv = []
        for m in k.meshResults:
            df = m.df
            x = np.linspace(df['X'].min(), df['X'].max(), 20)
            z = np.linspace(df['Z'].min(), df['Z'].max(), 20)
            grid_x, grid_z = np.meshgrid(x, z)
            grid_v = griddata(df[['X', 'Z']].values, df['Resistivity(ohm.m)'].values,
                              (grid_x, grid_z), method='nearest')
            
            # set nan to -1
            inan = np.isnan(grid_v)
            grid_v[inan] = -1

            xzv.append({
                'x': x.tolist(),
                'z': z.tolist(),
                'rho': grid_v.tolist(),
            })
        
        self.data_logger.info(json.dumps(xzv))
        return xzv

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


print(colored(r' ________________________________' + '\n' +
              r'|  _  | | | ||  \/  || ___ \_   _|' + '\n' +
              r'| | | | |_| || .  . || |_/ / | |' + '\n' +
              r'| | | |  _  || |\/| ||  __/  | |' + '\n' +
              r'\ \_/ / | | || |  | || |    _| |_' + '\n' +
              r' \___/\_| |_/\_|  |_/\_|    \___/ ', 'red'))
print('Version:', VERSION)
platform, on_pi = get_platform()

if on_pi:
    print(colored(f'\u2611 Running on {platform}', 'green'))
    # TODO: check model for compatible platforms (exclude Raspberry Pi versions that are not supported...)
    #       and emit a warning otherwise
    if not arm64_imports:
        print(colored(f'Warning: Required packages are missing.\n'
                      f'Please run ./env.sh at command prompt to update your virtual environment\n', 'yellow'))
else:
    print(colored(f'\u26A0 Not running on the Raspberry Pi platform.\nFor simulation purposes only...', 'yellow'))

current_time = datetime.now()
print(f'local date and time : {current_time.strftime("%Y-%m-%d %H:%M:%S")}')
OhmPi.get_deprecated_methods()

# for testing
if __name__ == "__main__":
    ohmpi = OhmPi(settings=OHMPI_CONFIG['settings'])
    if ohmpi.controller is not None:
        ohmpi.controller.loop_forever()
