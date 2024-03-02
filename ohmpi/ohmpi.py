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
import pandas as pd
from zipfile import ZipFile
from shutil import rmtree, make_archive
from threading import Thread
from queue import Queue
from inspect import getmembers, isfunction
from datetime import datetime
from termcolor import colored
from logging import DEBUG
from ohmpi.utils import get_platform
from ohmpi.logging_setup import setup_loggers
from ohmpi.config import MQTT_CONTROL_CONFIG, OHMPI_CONFIG, EXEC_LOGGING_CONFIG
import ohmpi.deprecated as deprecated
from ohmpi.hardware_system import OhmPiHardware
from ohmpi.sequence import (dpdp1, dpdp2, wenner_alpha, wenner_beta, wenner,
                          wenner_gamma, schlum1, schlum2, multigrad)
from tqdm.auto import tqdm

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

VERSION = 'v2024.0.0'


class OhmPi(object):
    """OhmPi class.
    """
    def __init__(self, settings=None, sequence=None, mqtt=True):
        """Construct the ohmpi object.

        Parameters
        ----------
        settings : dict, optional
            Dictionnary of parameters. Possible parameters with their default values:
            `{'injection_duration': 0.2, 'nb_meas': 1, 'sequence_delay': 1,
            'nb_stack': 1, 'sampling_interval': 2, 'tx_volt': 5, 'duty_cycle': 0.5,
            'strategy': 'constant', 'export_path': None
        sequence : str, optional
            Path of the .csv or .txt file with A, B, M and N electrodes.
            Electrode index starts at 1. See `OhmPi.load_sequence()` for full docstring.
        mqtt : bool, optional
            If True (default), publish on mqtt topics while logging,
            otherwise use other loggers only (print).
        """
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
        self.settings = {}
        self.update_settings(os.path.join(os.path.split(os.path.dirname(__file__))[0], 'settings/default.json'))

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

    @classmethod
    def get_deprecated_methods(cls):
        for i in getmembers(deprecated, isfunction):
            setattr(cls, i[0], i[1])

    def append_and_save(self, filename: str, last_measurement: dict, fw_in_csv=None, fw_in_zip=None, cmd_id=None):
        """Appends and saves the last measurement dict.

        Parameters
        ----------
        filename : str
            Filename of the .csv.
        last_measurement : dict
            Last measurement taken in the form of a python dictionary.
        fw_in_csv : bool, optional
            Wether to save the full-waveform data in the .csv (one line per quadrupole).
            As these readings have different lengths for different quadrupole, the data are padded with NaN.
            If None, default is read from default.json.
        fw_in_zip : bool, optional
            Wether to save the full-waveform data in a separate .csv in long format to be zipped to
            spare space. If None, default is read from default.json.
        cmd_id : str, optional
            Unique command identifier.
        """
        # check arguments
        if fw_in_csv is None:
            fw_in_csv = self.settings['fw_in_csv']
        if fw_in_zip is None:
            fw_in_zip = self.settings['fw_in_zip']

        # check if directory 'data' exists
        ddir = os.path.split(filename)[0]
        if os.path.exists(ddir) is not True:
            os.mkdir(ddir)

        last_measurement = deepcopy(last_measurement)
        
        if 'full_waveform' in last_measurement:
            # save full waveform data in a long .csv file
            if fw_in_zip:
                fw_filename = filename.replace('.csv', '_fw.csv')
                if not os.path.exists(fw_filename):  # new file, write headers first
                    with open(fw_filename, 'w') as f:
                        f.write('A,B,M,N,t,current,voltage\n')
                # write full data
                with open(fw_filename, 'a') as f:
                    dd = last_measurement['full_waveform']
                    aa = np.repeat(last_measurement['A'], dd.shape[0])
                    bb = np.repeat(last_measurement['B'], dd.shape[0])
                    mm = np.repeat(last_measurement['M'], dd.shape[0])
                    nn = np.repeat(last_measurement['N'], dd.shape[0])
                    fwdata = np.c_[aa, bb, mm, nn, dd]
                    np.savetxt(f, fwdata, delimiter=',', fmt=['%d', '%d', '%d', '%d', '%.3f', '%.3f', '%.3f'])

            if fw_in_csv:
                d = last_measurement['full_waveform']
                n = d.shape[0]
                if n > 1:
                    idic = dict(zip(['i' + str(i) for i in range(n)], d[:, 0]))
                    udic = dict(zip(['u' + str(i) for i in range(n)], d[:, 1]))
                    tdic = dict(zip(['t' + str(i) for i in range(n)], d[:, 2]))
                    last_measurement.update(idic)
                    last_measurement.update(udic)
                    last_measurement.update(tdic)

            last_measurement.pop('full_waveform')
        
        if os.path.isfile(filename):
            # Load data file and append data to it
            with open(filename, 'a') as f:
                w = csv.DictWriter(f, last_measurement.keys())
                w.writerow(last_measurement)
        else:
            # create data file and add headers
            with open(filename, 'a') as f:
                w = csv.DictWriter(f, last_measurement.keys())
                w.writeheader()
                w.writerow(last_measurement)

    def create_sequence(self, nelec, params=[('dpdp', 1, 8)], ireciprocal=False, fpath=None):
        """Creates a sequence of quadrupole. The sequence is saved automatically
        to sequences/mysequence.csv and used within OhmPi class. Several type of
        sequence or sequence with different parameters can be combined together.

        Parameters
        ----------
        nelec : int
            Number of electrodes.
        params : list of tuple, optional
            Each tuple is the form (<array_name>, param1, param2, ...)
            Dipole spacing is specified in terms of "number of electrode spacing".
            Dipole spacing is often referred to 'a'. Number of levels is a multiplier
            of 'a', often refere to 'n'. For multigradient array, an additional parameter
            's' is needed.
            Types of sequences available are :
            - ('wenner', a)
            - ('dpdp', a, n)
            - ('schlum', a, n)
            - ('multigrad', a, n, s)
        ireciprocal : bool, optional
            If True, will add reciprocal quadrupoles (so MNAB) to the sequence.
        fpath : str, optional
            Path where to save the sequence (including filename and extension). By
            default, sequence is saved in ohmpi/sequences/sequence.txt.
        """
        # dictionnary of function to create sequence
        fdico = {
            'dpdp': dpdp1, 
            'wenner': wenner,
            'schlum': schlum1,
            'multigrad': multigrad,
        }
        # check arguments
        if fpath is None:
            fpath = os.path.join(os.path.dirname(__file__), '../sequences/sequence.txt')
        qs = []

        # create sequence
        for p in params:
            pok = [int(p[i]) for i in np.arange(1, len(p))]  # make sure all are int
            qs.append(fdico[p[0]](nelec, *pok).values.astype(int))
        quad = np.vstack(qs)
        if len(quad.shape) == 1:  # only one quadrupole
            quad = quad[None, :]

        # add reciprocal
        if ireciprocal:
            quad = np.r_[quad, quad[:, [2, 3, 0, 1]]]
        self.sequence = quad

        # save sequence
        np.savetxt(fpath, self.sequence, delimiter=' ', fmt='%d')
        print('{:d} quadrupoles generated.'.format(self.sequence.shape[0]))

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
            Unique command identifier.
        """
        # get all .csv file in data folder
        if survey_names is None:
            survey_names = []
        ddir = os.path.dirname(self.settings['export_path'])
        fnames = [fname for fname in os.listdir(ddir) if fname[-4:] == '.csv' and fname[-7:] != '_fw.csv']
        ddic = {}
        if cmd_id is None:
            cmd_id = 'unknown'
        for fname in fnames:
            if ((fname != 'readme.txt')
                    and ('_rs' not in fname)
                    and (fname.replace('.csv', '') not in survey_names)):
                # try:
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
                # except Exception as e:
                #    print(fname, ':', e)
        rdic = {'cmd_id': cmd_id, 'data': ddic}
        self.data_logger.info(json.dumps(rdic))
        return ddic

    def interrupt(self, cmd_id=None):
        """Interrupts the acquisition.

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier.
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
            Unique command identifier.

        Returns
        -------
        sequence : numpy.ndarray
            Array of shape (number quadrupoles * 4).
        """
        self.exec_logger.debug(f'Loading sequence {filename}')
        sequence = np.loadtxt(filename, delimiter=" ", dtype=np.uint32, ndmin=2)  # load quadrupole file

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
        """Processes commands received from the controller(s).

        Parameters
        ----------
        message : str
            Message containing a command and arguments or keywords and arguments.
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
        """Quits OhmPi.

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier.
        """

        self.exec_logger.debug(f'Quitting ohmpi.py following command {cmd_id}')
        exit()

    def _read_hardware_config(self):
        """Reads hardware configuration from config.py.
        """
        self.exec_logger.debug('Getting hardware config')
        self.id = OHMPI_CONFIG['id']  # ID of the OhmPi
        self.exec_logger.debug(f'OHMPI_CONFIG = {str(OHMPI_CONFIG)}')

    def remove_data(self, cmd_id=None):
        """Remove all data in the ´export_path´ folder on the raspberrypi.

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier.
        """
        self.exec_logger.debug(f'Removing all data following command {cmd_id}')
        datadir = os.path.dirname(self.settings['export_path'])
        rmtree(datadir)
        os.mkdir(datadir)

    def restart(self, cmd_id=None):
        """Restarts the Raspberry Pi.

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier.
        """
        self.exec_logger.info(f'Restarting pi following command {cmd_id}...')
        os.system('reboot')  # this may need admin rights

    def download_data(self, cmd_id=None):
        """Create a zip of the data folder to then download it easily.
        """
        datadir, _ = os.path.split(self.settings['export_path'])
        zippath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data'))
        make_archive(zippath, 'zip', datadir)
        self.data_logger.info(json.dumps({'download': 'ready'}))

    def shutdown(self, cmd_id=None):
        """Shutdown the Raspberry Pi.

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier
        """
        self.exec_logger.info(f'Restarting pi following command {cmd_id}...')
        os.system('poweroff')  # this may require admin rights

    def plot_last_fw(self, save_fig=False, filename=None):
        """Plots last full waveform measurement

        Parameters
        ----------
        save_fig: boolean, optional - default (False)
        filename: str, optional. Path to save plot. By default figures/test.png"""

        self._hw._plot_readings(save_fig=save_fig, filename=filename)

    def run_measurement(self, quad=None, nb_stack=None, injection_duration=None, duty_cycle=None,
                        autogain=True, strategy=None, tx_volt=None, best_tx_injtime=0.1,
                        cmd_id=None, vab_max=None, iab_max=None, vmn_max=None, vmn_min=None, **kwargs):
        # TODO: add sampling_interval -> impact on _hw.rx.sampling_rate (store the current value,
        #  change the _hw.rx.sampling_rate, do the measurement, reset the sampling_rate to the previous value)
        # TODO: default value of tx_volt and other parameters set to None should be given in config.py and used
        #  in function definition
        """Measures on a quadrupole and returns a dictionnary with the transfer resistance.

        Parameters
        ----------
        quad : iterable (list of int)
            Quadrupole to measure, just for labelling. Only switch_mux_on/off
            really create the route to the electrodes.
        nb_stack : int, optional
            Number of stacks. A stack is considered two pulses (one
            positive, one negative). If 0, we will look for the best voltage.
        injection_duration : int, optional
            Injection time in seconds.
        duty_cycle : float, optional
            Duty cycle (default=0.5) of injection square wave.
        strategy : str, optional, default: constant
            Define injection strategy (if power is adjustable, otherwise constant tx_volt, generally 12V battery is used).
            Either:
            - vmax : compute Vab to reach a maximum Vmn_max and Iab without exceeding vab_max
            - vmin : compute Vab to reach at least Vmn_min
            - constant : apply given Vab (tx_volt) but checks if expected readings not out-of-range
            - full_constant: apply given Vab (tx_volt) with no out-of-range checks for optimising duration at the risk of out-of-range readings
            Safety check (i.e. short voltage pulses) performed prior to injection to ensure
            injection within bounds defined in vab_max, iab_max, vmn_max or vmn_min. This can adapt Vab.
            To bypass safety check before injection, tx_volt should be set equal to vab_max (not recpommanded)
        vab_max : str, optional
            Maximum injection voltage.
            Default value set by config or boards specs
        iab_max : str, optional
            Maximum current applied.
            Default value set by config or boards specs
        vmn_max : str, optional
            Maximum Vmn allowed.
            Default value set by config or boards specs
        vmn_min :
            Minimum Vmn desired (used in strategy vmin).
            Default value set by config or boards specs
        tx_volt : float, optional  # TODO: change tx_volt to Vab
            For power adjustable only. If specified, voltage will be imposed.
        cmd_id : str, optional
            Unique command identifier.
        """
        # check pwr is on, if not, let's turn it on
        switch_power_off = False
        if self._hw.tx.pwr.voltage_adjustable and self._hw.pwr_state == 'off':
            self._hw.pwr_state = 'on'
            switch_power_off = True

        self.exec_logger.debug('Starting measurement')
        self.exec_logger.debug('Waiting for data')

        # check arguments
        if quad is None:
            quad = np.array([0, 0, 0, 0])
        if nb_stack is None and 'nb_stack' in self.settings:
            nb_stack = self.settings['nb_stack']
        if injection_duration is None and 'injection_duration' in self.settings:
            injection_duration = self.settings['injection_duration']
        if duty_cycle is None and 'duty_cycle' in self.settings:
            duty_cycle = self.settings['duty_cycle']
        if tx_volt is None and 'tx_volt' in self.settings:
            tx_volt = self.settings['tx_volt']
        if strategy is None and 'strategy' in self.settings:
            strategy = self.settings['strategy']
        if vab_max is None and 'vab_max' in self.settings:
            vab_max = self.settings['vab_max']
        if iab_max is None and 'iab_max' in self.settings:
            iab_max = self.settings['iab_max']
        if vmn_max is None and 'vmn_max' in self.settings:
            vmn_max = self.settings['vmn_max']
        if vmn_min is None and 'vmn_min' in self.settings:
            vmn_min = self.settings['vmn_min']
        bypass_check = kwargs['bypass_check'] if 'bypass_check' in kwargs.keys() else False
        d = {}

        def switch_mux_on(queue,quad,bypass_check,cmd_id):
            result = self.switch_mux_on(quad, bypass_check, cmd_id)  # Function that returns the value you want to return
            queue.put(result)
        q = Queue()
        switch_mux_on = Thread(target=switch_mux_on, args=(q,quad,bypass_check,cmd_id))
        switch_pwr_on = Thread(target=setattr, args=(self._hw.tx.pwr, 'pwr_state', 'on'))
        switch_mux_on.start()
        switch_pwr_on.start()
        switch_mux_on.join()
        switch_pwr_on.join()
        status = q.get()
        if status:
            vab = self._hw.compute_tx_volt(tx_volt=tx_volt, strategy=strategy, vmn_max=vmn_max, vab_max=vab_max,
                                               iab_max=iab_max, vmn_min=vmn_min)
            # time.sleep(0.5)  # to wait for pwr discharge
            self._hw.vab_square_wave(vab, cycle_duration=injection_duration*2/duty_cycle, cycles=nb_stack, duty_cycle=duty_cycle)
            self.switch_mux_off(quad, cmd_id)

            if 'delay' in kwargs.keys():
                delay = kwargs['delay']
                if delay > injection_duration:
                    delay = injection_duration
            else:
                delay = injection_duration * 2/3  # TODO: check if this is ok and if last point is not taken at the end of injection
            x = self._hw.select_samples(delay)
            Vmn = self._hw.last_vmn(delay=delay)
            Vmn_std = self._hw.last_vmn_dev(delay=delay)
            I = self._hw.last_iab(delay=delay)
            I_std = self._hw.last_iab_dev(delay=delay)
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
                "Tx [V]": vab,
                "CPU temp [degC]": self._hw.ctl.cpu_temperature,
                "Nb samples [-]": len(self._hw.readings[x, 2]),  # TODO: use only samples after a delay in each pulse
                "full_waveform": self._hw.readings[:, [0, -2, -1]],
                "I_std [%]": I_std,
                "Vmn_std [%]": Vmn_std,
                "R_ab [kOhm]": vab / I
            }

            # to the data logger
            dd = d.copy()
            dd.pop('full_waveform')  # too much for logger
            dd.update({'A': str(dd['A'])})
            dd.update({'B': str(dd['B'])})
            dd.update({'M': str(dd['M'])})
            dd.update({'N': str(dd['N'])})

            # round float to 2 decimal
            for key in dd.keys():  # Check why this is applied on keys and not values...
                if isinstance(dd[key], float):
                    dd[key] = np.round(dd[key], 3)
            dd['cmd_id'] = str(cmd_id)

            # log data to the data logger
            print('\r')
            self.data_logger.info(dd)

            # if strategy not constant, then switch dps off (button) in case following measurement within sequence
            # TODO: check if this is the right strategy to handle DPS pwr state on/off after measurement
            if (strategy == 'vmax' or strategy == 'vmin') and vab - tx_volt > 5.:  # if starting tx_volt was too far (> 5 V) from actual vab, then turn pwr off
                self._hw.tx.pwr.pwr_state = 'off'

                # Discharge DPS capa
                # TODO: For pwr_adjustable only and dependent on TX version so should be placed at PWR level (or at _hw level)
                self._hw.discharge_pwr()
                # self._hw.switch_mux(electrodes=quad[0:2], roles=['A', 'B'], state='on')
                # self._hw.tx.polarity = 1
                # time.sleep(1.0)
                # self._hw.tx.polarity = 0
                # self._hw.switch_mux(electrodes=quad[0:2], roles=['A', 'B'], state='off')
        else:
            self.exec_logger.info(f'Skipping {quad}')

        # if power was off before measurement, let's turn if off
        if switch_power_off:
            self._hw.pwr_state = 'off'

        return d

    def repeat_sequence(self, **kwargs):
        """Identical to run_multiple_sequences().
        """
        self.run_multiple_sequences(**kwargs)

    def run_multiple_sequences(self, sequence_delay=None, nb_meas=None, fw_in_csv=None,
                               fw_in_zip=None, cmd_id=None, **kwargs):
        """Runs multiple sequences in a separate thread for monitoring mode.
           Can be stopped by 'OhmPi.interrupt()'.
           Additional arguments are passed to run_measurement().

        Parameters
        ----------
        sequence_delay : int, optional
            Number of seconds at which the sequence must be started from each others.
        nb_meas : int, optional
            Number of time the sequence must be repeated.
        fw_in_csv : bool, optional
            Wether to save the full-waveform data in the .csv (one line per quadrupole).
            As these readings have different lengths for different quadrupole, the data are padded with NaN.
            If None, default is read from default.json.
        fw_in_zip : bool, optional
            Wether to save the full-waveform data in a separate .csv in long format to be zipped to
            spare space. If None, default is read from default.json.
        cmd_id : str, optional
            Unique command identifier.
        kwargs : dict, optional
            See help(OhmPi.run_measurement) for more info.
        """
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
                self.run_sequence(fw_in_csv=fw_in_csv, fw_in_zip=fw_in_zip, **kwargs)
                dt = sequence_delay - (time.time() - t0)  # sleeping time between sequence
                if dt < 0:
                    dt = 0
                if nb_meas > 1:
                    if self.status == 'stopping':
                        break
                    time.sleep(dt)  # waiting for next measurement (time-lapse)
            self.status = 'idle'

        self.thread = Thread(target=func)
        self.thread.start()

    def run_sequence(self, fw_in_csv=None, fw_in_zip=None, cmd_id=None, **kwargs):
        """Runs sequence synchronously (=blocking on main thread).
           Additional arguments are passed to run_measurement().

        Parameters
        ----------
        fw_in_csv : bool, optional
            Wether to save the full-waveform data in the .csv (one line per quadrupole).
            As these readings have different lengths for different quadrupole, the data are padded with NaN.
            If None, default is read from default.json.
        fw_in_zip : bool, optional
            Wether to save the full-waveform data in a separate .csv in long format to be zipped to
            spare space. If None, default is read from default.json.
        cmd_id : str, optional
            Unique command identifier.
        """
        # check arguments
        if fw_in_csv is None:
            fw_in_csv = self.settings['fw_in_csv']
        if fw_in_zip is None:
            fw_in_zip = self.settings['fw_in_zip']

        # switch power on
        if self._hw.tx.pwr.voltage_adjustable:
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

        # measure all quadrupole of the sequence
        if self.sequence is None:
            n = 1
        else:
            n = self.sequence.shape[0]
        for i in tqdm(range(0, n), "Sequence progress", unit='injection', ncols=100, colour='green'):
            if self.sequence is None:
                quad = np.array([0, 0, 0, 0])
            else:
                quad = self.sequence[i, :]  # quadrupole
            if self.status == 'stopping':
                break
            # run a measurement
            acquired_data = self.run_measurement(quad=quad, **kwargs)

            # add command_id in dataset
            acquired_data.update({'cmd_id': cmd_id})
            # log data to the data logger
            # self.data_logger.info(f'{acquired_data}')  # NOTE: It could be useful to keep the cmd_id in the
            # save data and print in a text file
            self.append_and_save(filename, acquired_data, fw_in_csv=fw_in_csv, fw_in_zip=fw_in_zip)
            self.exec_logger.debug(f'quadrupole {i + 1:d}/{n:d}')
        self._hw.pwr_state = 'off'

        # file management
        if fw_in_csv:  # make sure we have the same number of columns
            with open(filename, 'r') as f:
                x = f.readlines()

            # get column of start of full-waveform
            icol = 0
            for i, col in enumerate(x[0].split(',')):
                if col == 'i0':
                    icol = i
                    break

            # get longest possible line
            max_length = np.max([len(row.split(',')) for row in x]) - icol
            nreadings = max_length // 3

            # create padding array for full-waveform  # TODO test this!
            with open(filename, 'w') as f:
                # write back headers
                xs = x[0].split(',')
                f.write(','.join(xs[:icol]))
                f.write(',')
                for i, col in enumerate(['t', 'i', 'v']):
                    f.write(','.join([col + str(j) for j in range(nreadings)]))
                    if col == 'v':
                        f.write('\n')
                    else:
                        f.write(',')
                # write back rows
                for i, row in enumerate(x[1:]):
                    xs = row.split(',')
                    f.write(','.join(xs[:icol]))
                    f.write(',')
                    fw = np.array(xs[icol:])
                    fw_pad = fw.reshape((3, -1)).T
                    fw_padded = np.zeros((nreadings, 3), dtype=fw_pad.dtype)
                    fw_padded[:fw_pad.shape[0], :] = fw_pad
                    f.write(','.join(fw_padded.T.flatten()).replace('\n', '') + '\n')

        if fw_in_zip:
            fwfilename = filename.replace('.csv', '_fw')
            with ZipFile(fwfilename + '.zip', 'w') as myzip:
                myzip.write(fwfilename + '.csv', os.path.basename(fwfilename) + '.csv')
            os.remove(fwfilename + '.csv')

        # reset to idle if we didn't interrupt the sequence
        if self.status != 'stopping':
            self.status = 'idle'

    def run_sequence_async(self, cmd_id=None, **kwargs):
        """Runs the sequence in a separate thread. Can be stopped by 'OhmPi.interrupt()'.
            Additional arguments are passed to run_measurement().

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier.
        """

        def func():
            self.run_sequence(**kwargs)

        self.thread = Thread(target=func)
        self.thread.start()
        self.status = 'idle'

    # TODO: we could build a smarter RS-Check by selecting adjacent electrodes based on their locations and try to
    #  isolate electrodes that are responsible for high resistances (ex: AB high, AC low, BC high
    #  -> might be a problem at B (cf what we did with WofE)
    def rs_check(self, tx_volt=5.0, cmd_id=None, couple=None):
        # TODO: add a default value for rs-check in config.py import it in ohmpi.py and add it in rs_check definition
        """Checks contact resistances.
        Strategy: we just open A and B, measure the current and using vAB set or
        assumed (12V assumed for battery), we compute Rab.

        Parameters
        ----------
        tx_volt : float
            Voltage of the injection.
        couple  : array, for selecting a couple of electrode for checking resistance
        cmd_id : str, optional
            Unique command identifier.
        """
        # check pwr is on, if not, let's turn it on
        switch_tx_pwr_off = False
        if self._hw.pwr_state == 'off':
            self._hw.pwr_state = 'on'
            switch_tx_pwr_off = True

        # create custom sequence where MN == AB
        # we only check the electrodes which are in the sequence (not all might be connected)
        if couple is None:
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
        else:
            quads = np.array([[couple[0], couple[1], 0, 0]], dtype=np.uint32)
           
        # create filename to store RS
        export_path_rs = self.settings['export_path'].replace('.csv', '') \
                         + '_' + datetime.now().strftime('%Y%m%dT%H%M%S') + '_rs.csv'

        # perform RS check
        self.status = 'running'
        self.reset_mux()

        # switches off measuring LED
        self._hw.tx.measuring = 'on'

        # turn dps_pwr_on if needed
        switch_pwr_off = False

        if self._hw.pwr.pwr_state == 'off':
            self._hw.pwr.pwr_state = 'on'
            switch_pwr_off = True

        # measure all quad of the RS sequence
        for i in range(0, quads.shape[0]):
            quad = quads[i, :]  # quadrupole
            self._hw.switch_mux(electrodes=list(quads[i, :2]), roles=['A', 'B'], state='on')
            self._hw._vab_pulse(duration=0.2, vab=tx_volt)
            current = self._hw.readings[-1, 3]
            vab = self._hw.tx.pwr.voltage
            print(vab, current)
            time.sleep(0.2)

            # compute resistance measured (= contact resistance)
            rab = abs(vab*1000 / current) / 1000  # kOhm
            
            # create a message as dictionnary to be used by the html interface
            msg = {
                'rsdata': {
                    'A': int(quad[0]),
                    'B': int(quad[1]),
                    'rs': np.round(rab, 3),  # in kOhm
                }
            }
            self.data_logger.info(json.dumps(msg))

            # if contact resistance = 0 -> we have a short circuit!!
            if rab < 1e-5:
                msg = f'!!!SHORT CIRCUIT!!! {str(quad):s}: {rab:.3f} kOhm'
                self.exec_logger.warning(msg)

            # save data in a text file
            self.append_and_save(export_path_rs, {
                'A': quad[0],
                'B': quad[1],
                'RS [kOhm]': np.round(rab, 3),
            })

            # close mux path and put pin back to GND
            self.switch_mux_off(quad)

        self.status = 'idle'
        if switch_pwr_off:
            self._hw.pwr.pwr_state = 'off'

        # switches off measuring LED
        self._hw.tx.measuring = 'off'

        # if power was off before measurement, let's turn if off
        if switch_tx_pwr_off:
            self._hw.pwr_state = 'off'
    
        # TODO if interrupted, we would need to restore the values
        # TODO or we offer the possibility in 'run_measurement' to have rs_check each time?

    def set_sequence(self, sequence=None, cmd_id=None):
        """Sets the sequence to acquire.

        Parameters
        ----------
        sequence : list of list or array_like
            Sequence of quadrupoles (list of list or array_like).
        cmd_id: str, optional
            Unique command identifier.
        """
        try:
            self.sequence = np.array(sequence).astype(int)
        except Exception as e:
            self.exec_logger.warning(f'Unable to set sequence: {e}')

    def switch_mux_on(self, quadrupole, bypass_check=False, cmd_id=None):
        """Switches on multiplexer relays for given quadrupole.

        Parameters
        ----------
        quadrupole : list of 4 int
            List of 4 integers representing the electrode numbers.
        bypass_check: bool, optional
            Bypasses checks for A==M or A==N or B==M or B==N (i.e. used for rs-check).
        cmd_id : str, optional
            Unique command identifier.
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
        quadrupole : list of 4 int
            List of 4 integers representing the electrode numbers.
        cmd_id : str, optional
            Unique command identifier.
        """
        assert len(quadrupole) == 4
        return self._hw.switch_mux(electrodes=quadrupole, state='off')

    def test_mux(self, activation_time=0.2, mux_id=None, cmd_id=None):
        """Interactive method to test the multiplexer boards.

        Parameters
        ----------
        activation_time : float, optional
            Time in seconds during which the relays are activated.
        mux_id : str, optional
            ID of the mux_board to test.
        cmd_id : str, optional
            Unique command identifier.
        """
        self.reset_mux()  # NOTE: all mux boards should be reset even if we only want to test one go avoid shortcuts
        if mux_id is None:
            self._hw.test_mux(activation_time=activation_time)
        else:
            self._hw.mux_boards[mux_id].test(activation_time=activation_time)

    def reset_mux(self, cmd_id=None):
        """Switches off all multiplexer relays.

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier.
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
        - export_path (path where to export the data, timestamp will be added to filename)

        Parameters
        ----------
        settings : str, dict
            Path to the .json settings file or dictionary of settings.
        cmd_id : str, optional
            Unique command identifier.
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
            self.settings['export_path'] = os.path.join("data", "measurement.csv")

        if not os.path.isabs(self.settings['export_path']):
            export_dir = os.path.split(os.path.dirname(__file__))[0]
            self.settings['export_path'] = os.path.join(export_dir, self.settings['export_path'])

    def export(self, fnames=None, outputdir=None, ftype='bert', elec_spacing=1):
        """Export surveys stored in the 'data/' folder into an output
        folder.

        Parameters
        ----------
        fnames : list of str, optional
            List of path (not filename) to survey in ohmpi format to be converted.
        outputdir : str, optional
            Path of the output directory where the new files are stored. If None,
            a directory called 'output' is created in OhmPi.
        ftype : str, optional
            Type of export. To be chosen between:
            - bert (same as pygimli)
            - pygimli (same as bert)
            - protocol (for resipy, R2 codes)
        elec_spacing : float, optional
            Electrode spacing in meters. Same electrode spacing is assumed.
        """
        # handle parameters default values
        if fnames is None:
            datadir = os.path.join(os.path.dirname(__file__), '../data/')
            fnames = [os.path.join(datadir, f) for f in os.listdir(datadir) if f[-4:] == '.csv']
        if outputdir is None:
            outputdir = os.path.join(os.path.dirname(__file__), '../output/')
        if os.path.exists(outputdir) is False:
            os.mkdir(outputdir)
        ftype = ftype.lower()
        
        # define parser
        def ohmpi_parser(fname):
            df = pd.read_csv(fname)
            df = df.rename(columns={'A': 'a', 'B': 'b', 'M': 'm', 'N': 'n'})
            df['vp'] = df['Vmn [mV]']
            df['i'] = df['I [mA]']
            df['resist'] = df['vp']/df['i']
            df['ip'] = np.nan
            emax = np.max(df[['a', 'b', 'm', 'n']].values)
            elec = np.zeros((emax, 3))
            elec[:, 0] = np.arange(emax) * elec_spacing
            return elec, df[['a', 'b', 'm', 'n', 'vp', 'i', 'resist', 'ip']]
        
        # read all files and save them in the desired format
        for fname in tqdm(fnames):
            try:
                elec, df = ohmpi_parser(fname)
                fout = os.path.join(outputdir, os.path.basename(fname).replace('.csv', ''))
                if ftype == 'protocol':
                    fout = fout + '.dat'
                    with open(fout, 'w') as f:
                        f.write('{:d}\n'.format(df.shape[0]))
                    with open(fout, 'a') as f:
                        df['index'] = np.arange(1, df.shape[0]+1)
                        df[['index', 'a', 'b', 'm', 'n', 'resist']].to_csv(
                            f, index=False, sep=' ', header=False)
                elif ftype == 'bert' or ftype == 'pygimli':
                    fout = fout + '.dat'
                    with open(fout, 'w') as f:
                        f.write('{:d} # positions electrodes\n'.format(elec.shape[0]))
                        f.write('#\tx\ty\tz\n')
                        for j in range(elec.shape[0]):
                            f.write('{:.2f}\t{:.2f}\t{:.2f}\n'.format(*elec[j, :]))
                        f.write('{:d} # number of data\n'.format(df.shape[0]))
                        f.write('#\ta\tb\tm\tn\tR\n')
                    with open(fout, 'a') as f:
                        df[['a', 'b', 'm', 'n', 'resist']].to_csv(
                            f, index=False, sep='\t', header=False)
            except Exception as e:
                print('export(): could not save file', fname)

    def run_inversion(self, survey_names=None, elec_spacing=1, **kwargs):
        """Run a simple 2D inversion using ResIPy (https://gitlab.com/hkex/resipy).
        
        Parameters
        ----------
        survey_names : list of string, optional
            Filenames of the survey to be inverted (including extension).
        elec_spacing : float (optional)
            Electrode spacing in meters. We assume same electrode spacing everywhere. Default is 1 m.
        kwargs : optional
            Additional keyword arguments passed to `resipy.Project.invert()`. For instance
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
        if survey_names is None:
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

        # import resipy if available
        pdir = os.path.dirname(__file__)
        try:
            from scipy.interpolate import griddata  # noqa
            import pandas as pd  # noqa
            import sys
            sys.path.append(os.path.join(pdir, '../../resipy/src'))
            from resipy import Project  # noqa
        except Exception as e:
            self.exec_logger.error('Cannot import ResIPy, scipy or Pandas, error: ' + str(e))
            return []

        # get absolule filename
        fnames = []
        for survey_name in survey_names:
            fname = os.path.join(os.path.dirname(self.settings['export_path']), survey_name)
            if os.path.exists(fname):
                fnames.append(fname)
            else:
                self.exec_logger.warning(fname + ' not found')
        
        # define a parser for the "ohmpi" format
        def ohmpi_parser(fname):
            df = pd.read_csv(fname)
            df = df.rename(columns={'A': 'a', 'B': 'b', 'M': 'm', 'N': 'n'})
            df['vp'] = df['Vmn [mV]']
            df['i'] = df['I [mA]']
            df['resist'] = df['vp']/df['i']
            df['ip'] = np.nan
            emax = np.max(df[['a', 'b', 'm', 'n']].values)
            elec = np.zeros((emax, 3))
            elec[:, 0] = np.arange(emax) * elec_spacing
            return elec, df[['a', 'b', 'm', 'n', 'vp', 'i', 'resist', 'ip']]
                
        # run inversion
        self.exec_logger.info('ResIPy: import surveys')
        k = Project(typ='R2')  # invert in a temporary directory that will be erased afterwards
        if len(survey_names) == 1:
            k.createSurvey(fnames[0], parser=ohmpi_parser)
        elif len(survey_names) > 0 and reg_mode == 0:
            k.createBatchSurvey(fnames, parser=ohmpi_parser)
        elif len(survey_names) > 0 and reg_mode > 0:
            k.createTimeLapseSurvey(fnames, parser=ohmpi_parser)
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
            
            # set nan to -1 (hard to parse NaN in JSON)
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
OhmPi.get_deprecated_methods()  # TODO: check if this could be removed...

# for testing
if __name__ == "__main__":
    ohmpi = OhmPi(settings=OHMPI_CONFIG['settings'])
    if ohmpi.controller is not None:
        ohmpi.controller.loop_forever()
