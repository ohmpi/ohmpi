from hwTest import Alimentation, Current, Voltage, Multiplexer

# -*- coding: utf-8 -*-
"""
created on January 6, 2020.
Updates dec 2022.
Hardware: Licensed under CERN-OHL-S v2 or any later version
Software: Licensed under the GNU General Public License v3.0
Ohmpi.py is a program to control a low-cost and open hardware resistivity meter OhmPi that has been developed by
Rémi CLEMENT (INRAE), Vivien DUBOIS (INRAE), Hélène GUYARD (IGE), Nicolas FORQUET (INRAE), Yannick FARGIER (IFSTTAR)
Olivier KAUFMANN (UMONS), Arnaud WATLET (UMONS) and Guillaume BLANCHY (FNRS/ULiege).
"""

import os
from utils import get_platform
import json
import warnings
from copy import deepcopy
import numpy as np
import csv
import time
import shutil
from datetime import datetime
from termcolor import colored
import threading
from logging_setup import setup_loggers
from config import MQTT_CONTROL_CONFIG, OHMPI_CONFIG, EXEC_LOGGING_CONFIG
from logging import DEBUG

# finish import (done only when class is instantiated as some libs are only available on arm64 platform)
try:
    from gpiozero import CPUTemperature  # noqa

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

    def __init__(self, settings=None, sequence=None, use_mux=False, mqtt=True, onpi=None, idps=False):
        """Constructs the ohmpi object

        Parameters
        ----------
        settings:

        sequence:

        use_mux:
            if True use the multiplexor to select active electrodes
        mqtt: bool, defaut: True
            if True publish on mqtt topics while logging, otherwise use other loggers only
        onpi: bool,None default: None
            if None, the platform on which the class is instantiated is determined to set on_pi to either True or False.
            if False the behaviour of an ohmpi will be partially emulated and return random data.
        idps:
            if true uses the DPS
        """

        if onpi is None:
            _, onpi = get_platform()

        self._sequence = sequence
        self.nb_samples = 0
        self.use_mux = use_mux
        self.on_pi = onpi  # True if run from the RaspberryPi with the hardware, otherwise False for random data
        self.status = 'idle'  # either running or idle
        self.thread = None  # contains the handle for the thread taking the measurement

        # set loggers
        config_exec_logger, _, config_data_logger, _, _, msg = setup_loggers(mqtt=mqtt)  # TODO: add SOH
        self.data_logger = config_data_logger
        self.exec_logger = config_exec_logger
        self.soh_logger = None  # TODO: Implement the SOH logger
        print(msg)

        
        # read in hardware parameters (config.py)
        self._read_hardware_config()  # TODO should go to hw.py

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

        self.idps = idps  # flag to use dps for injection or not

        # connect to components on the OhmPi board
        if self.on_pi:
           # initialize hardware
            self.alim = Alimentation()
            self.voltage = Voltage()
            self.current = Current()
            self.mux = Multiplexer()

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

    def _compute_tx_volt(self, best_tx_injtime=0.1, strategy='vmax', tx_volt=5):
        """Estimates best Tx voltage based on different strategies.
        At first a half-cycle is made for a short duration with a fixed
        known voltage. This gives us Iab and Rab. We also measure Vmn.
        A constant c = vmn/iab is computed (only depends on geometric
        factor and ground resistivity, that doesn't change during a
        quadrupole). Then depending on the strategy, we compute which
        vab to inject to reach the minimum/maximum Iab current or
        min/max Vmn.
        
        Parameters
        ----------
        best_tx_injtime : float, optional
            Time in milliseconds for the half-cycle used to compute Rab.
        strategy : str, optional
            Either:
            - vmin : compute Vab to reach a minimum Iab and Vmn
            - vmax : compute Vab to reach a maximum Iab and Vmn
            - constant : apply given Vab
        tx_volt : float, optional
            Voltage apply to try to guess the best voltage. 5 V applied
            by default. If strategy "constant" is chosen, constant voltage
            to applied is "tx_volt".

        Returns
        -------
        vab : float
            Proposed Vab according to the given strategy.
        """

        # hardware limits
        voltage_min = self.voltage.vmin  # V
        voltage_max = self.voltage.vmax
        current_min = self.current.imin  # A
        current_max = self.current.imax
        tx_max = 40.  # volt

        # check of V
        volt = tx_volt
        if volt > tx_max:
            self.exec_logger.warning('Sorry, cannot inject more than 40 V, set it back to 5 V')
            volt = 5.

        # make sure we are not injecting
        self.alim.stop_injection()

        # select a polarity to start with
        self.alim.set_polarity(True)

        # set voltage for test
        self.alim.turn_on()
        self.alim.set_tx_voltage(volt)
        time.sleep(best_tx_injtime)  # inject for given tx time
        self.alim.start_injection()

        # autogain: set best gain
        self.current.set_best_gain()
        self.voltage.set_best_gain()

        # we measure the voltage on both A0 and A2 to guess the polarity
        values = self.read_values(duration=0.1)
        self.alim.stop_injection()
        iab = values[-1, 1]
        vmn = values[-1, 2]

        # compute constant
        c = vmn / iab
        Rab = (volt * 1000.) / iab  # noqa
        self.exec_logger.debug(f'Rab = {Rab:.2f} Ohms')

        # implement different strategies
        if strategy == 'vmax':
            vmn_max = c * current_max
            if voltage_max > vmn_max > voltage_min:
                vab = current_max * Rab
                self.exec_logger.debug('target max current')
            else:
                iab = voltage_max / c
                vab = iab * Rab
                self.exec_logger.debug('target max voltage')
            if vab > 25.:
                vab = 25.
            vab = vab * 0.9

        elif strategy == 'vmin':
            vmn_min = c * current_min
            if voltage_min < vmn_min < voltage_max:
                vab = current_min * Rab
                self.exec_logger.debug('target min current')
            else:
                iab = voltage_min / c
                vab = iab * Rab
                self.exec_logger.debug('target min voltage')
            if vab < 1.:
                vab = 1.
            vab = vab * 1.1

        elif strategy == 'constant':
            vab = volt
        else:
            vab = 5

        return vab

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
        """Interrupts the acquisition when launched in async mode.

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
        try:
            sequence = np.loadtxt(filename, delimiter=" ", dtype=np.uint32)  # load quadrupole file
            self.exec_logger.debug(f'Sequence of {sequence.shape[0]:d} quadrupoles read.')
            self.set_sequence(sequence)
        except Exception as e:
            self.exec_logger.debug('ERROR in load_sequence(): ' + str(e))

        if sequence is not None:
            self.exec_logger.info(f'Sequence {filename} of {sequence.shape[0]:d} quadrupoles loaded.')
        else:
            self.exec_logger.warning(f'Unable to load sequence {filename}')

    def set_sequence(self, sequence):
        """Set a sequence of quadrupoles.
        
        Parameters
        ----------
        sequence : list of list or np.array
            2D array with 1 row per quadrupole.
        """
        # locate lines where the electrode index exceeds the maximum number of electrodes
        test_index_elec = np.array(np.where(sequence > self.max_elec))

        # reshape in case we have a 1D array (=1 quadrupole)
        if len(sequence.shape) == 1:
            sequence = sequence[None, :]
            
        # test for elec A == B
        test_same_elec = np.where(sequence[:, 0] == sequence[:, 1])[0]
        ok = True
        
        # if statement with exit cases (TODO rajouter un else if pour le deuxième cas du ticket #2)
        if test_index_elec.size != 0:
            for i in range(len(test_index_elec[0, :])):
                ok = False
                self.exec_logger.error(f'An electrode index at line {str(test_index_elec[0, i] + 1)} '
                                       f'exceeds the maximum number of electrodes')
            # sys.exit(1)
            sequence = None
        if len(test_same_elec) != 0:
            for i in range(len(test_same_elec)):
                ok = False
                self.exec_logger.error(f'An electrode index A == B detected at line {str(test_same_elec[i] + 1)}')
            # sys.exit(1)
            sequence = None

        # set sequence attribute
        if ok:
            self.sequence = sequence
        else:
            self.exec_logger.error('Unable to set sequence. Fix sequence first.')


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
        self.Imax = OHMPI_CONFIG['Imax']  # maximum current
        self.exec_logger.debug(f'The maximum current cannot be higher than {self.Imax} mA')
        self.coef_p2 = OHMPI_CONFIG['coef_p2']  # slope for current conversion for ads.P2, measurement in V/V
        self.nb_samples = OHMPI_CONFIG['nb_samples']  # number of samples measured for each stack
        self.version = OHMPI_CONFIG['version']  # hardware version
        self.max_elec = OHMPI_CONFIG['max_elec']  # maximum number of electrodes
        self.board_version = OHMPI_CONFIG['board_version']
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

    def set_best_gain(self):
        """Set best gain."""
        self.current.set_best_gain()
        gain0 = self.voltage.get_best_gain(channel=0)
        gain2 = self.voltage.get_best_gain(channel=2)
        self.voltage.set_gain(np.min([gain0, gain2]))

    def read_values(self, duration=0.2, sampling=0.01):
        """Read voltage during a given time for current and voltage ADS.
        
        Parameters
        ----------
        duration : int, optional
            Time in seconds to monitor the voltage.
        sampling : int, optional
            Time between two samples in seconds.

        Returns
        -------
        meas : numpy.array
            Array with first column time in ms from start,
            second column, current in mA, then voltage in mV
            from the different channels.
        """        
        # compute maximum number of samples possible
        # we probably harvest less samples but like this
        # we can already allocated the array and that makes
        # the collection faster
        nsamples = int((int(duration * 1000) // sampling) + 1)

        # measurement of current i and voltage u during injection
        nchannel = len(self.voltage.read_all())
        meas = np.zeros((nsamples, 2 + nchannel)) * np.nan
        start_time = time.time()  # stating measurement time
        elapsed = 0
        for i in range(0, nsamples):
            # reading current value on ADS channels
            elapsed = time.time() - start_time  # real injection time (s)
            if elapsed >= (duration):
                break
            meas[i, 0] = elapsed
            meas[i, 1] = self.current.read()
            meas[i, 2:] = self.voltage.read_all()
            time.sleep(sampling)
        
        return meas[:i-1, :]


    def run_measurement(self, quad=[0, 0, 0, 0], nb_stack=None, injection_duration=None,
                        autogain=True, strategy='constant', tx_volt=5, best_tx_injtime=0.1,
                        duty=1, cmd_id=None):
        """Measures on a quadrupole and returns transfer resistance.

        Parameters
        ----------
        quad : iterable (list of int)
            Quadrupole to measure, just for labelling. Only switch_mux_on/off
            really creates the route to the electrodes.
        nb_stack : int, optional
            Number of stacks. A stacl is considered two half-cycles (one
            positive, one negative).
        injection_duration : int, optional
            Injection time in seconds.
        autogain : bool, optional
            If True, will adapt the gain of the ADS1115 to maximize the
            resolution of the reading.
        strategy : str, optional
            (V3.0 only) If we search for best voltage (tx_volt == 0), we can choose
            different strategy:
            - vmin: find the lowest voltage that gives us a signal
            - vmax: find the highest voltage that stays in the range
            For a constant value, just set the tx_volt.
        tx_volt : float, optional
            (V3.0 only) If specified, voltage will be imposed. If 0, we will look
            for the best voltage. If the best Tx cannot be found, no
            measurement will be taken and values will be NaN.
        best_tx_injtime : float, optional
            (V3.0 only) Injection time in seconds used for finding the best voltage.
        duty : float, optional
            Proportion of time spent on injection vs no injection time.
        cmd_id : str, optional
            Command ID.
        """
        self.exec_logger.debug('Starting measurement')

        if nb_stack is None:
            nb_stack = self.settings['nb_stack']
        if injection_duration is None:
            injection_duration = self.settings['injection_duration']
        tx_volt = float(tx_volt)

        # let's define the pin again as if we run through measure()
        # as it's run in another thread, it doesn't consider these
        # and this can lead to short circuit!
        self.alim = Alimentation()  # TODO carefully test that
        self.alim.stop_injection()

        # get best voltage to inject AND polarity
        if self.idps:
            tx_volt, polarity = self._compute_tx_volt(
                best_tx_injtime=best_tx_injtime, strategy=strategy, tx_volt=tx_volt)
            self.exec_logger.debug(f'Best vab found is {tx_volt:.3f}V')

        # first reset the gain to 2/3 before trying to find best gain (mode 0 is continuous)
        self.current.set_gain(2/3)
        self.voltage.set_gain(2/3)

        # turn on the power supply
        if self.alim.on == False:
            self.alim.turn_on()
        self.alim.set_tx_voltage(tx_volt)
        time.sleep(0.05)  # let it time to reach tx_volt
        
        if tx_volt > 0:  # we found a Vab in the range so we measure
            # find best gain during injection
            if autogain:
                self.alim.start_injection()
                time.sleep(injection_duration)
                self.set_best_gain()
                self.alim.stop_injection()

            # make sure we are not injecting
            self.alim.stop_injection()

            # full data for waveform
            fulldata = []

            # we sample every 10 ms (as using AnalogIn for both current
            # and voltage takes about 7 ms). When we go over the injection
            # duration, we break the loop and truncate the meas arrays
            # only the last values in meas will be taken into account
            start_delay = time.time()
            injtimes = np.zeros(nb_stack * 2)
            for n in range(0, nb_stack * 2):  # for each half-cycles                    
                # current injection polarity
                if (n % 2) == 0:
                    self.alim.set_polarity(True)
                else:
                    self.alim.set_polarity(False)
                self.alim.start_injection()
                
                # reading voltages and currents
                elapsed = time.time() - start_delay
                values = self.read_values(duration=injection_duration)
                injtimes[n] = values[-1, 0]
                values[:, 0] += elapsed
                fulldata.append(values)

                # stop current injection
                self.alim.stop_injection()

                # waiting time (no injection) before next half-cycle
                if duty < 1:
                    duration = injection_duration * (1 - duty)
                    elapsed = time.time() - start_delay
                    values = self.read_values(duration=duration)
                    values[:, 0] += elapsed
                    fulldata.append(values)
                else:
                    fulldata.append(np.array([[], [], [], []]).T)
            
            # TODO get battery voltage and warn if battery is running low
            # TODO send a message on SOH stating the battery level

            # let's do some calculation (out of the stacking loop)
            stacks = np.zeros((len(fulldata) // 2, fulldata[0].shape[1]-1))
            
            # define number of sample to average for the injection half-cycle
            n2avg = int(fulldata[0].shape[0] // 3)

            # compute average for the injection half-cycle
            for n, meas in enumerate(fulldata[::2]):
                stacks[n, :] = np.mean(meas[-n2avg:, 1:], axis=0)

            # identify which of U0 or U2 is on top
            a = 1
            b = 0
            if stacks[0, 1] > stacks[0, 2]:
                a = 0
                b = 1

            # compute average vmn and i
            iab = np.mean(stacks[:, 1])
            vmn = np.mean(stacks[a::2, 1] + stacks[b::2, 2])
            
            # self-potential estimated during on-time
            spon = np.mean(stacks[a::2, 1] - stacks[b::2, 2])

            # remove the average sp computed on injection half-cycle
            vmn = vmn - spon
            
            # compute average self potential between injection half-cycle
            if duty < 1:
                spoff = 0
                n2avg = int(fulldata[0].shape[0] // 3)
                for n, meas in enumerate(fulldata[1::2]):
                    spoff += np.mean(meas[-n2avg:, 2])
                spoff  = spoff / len(fulldata) * 2
        else:
            iab = np.nan
            vmn = np.nan
            spon = np.nan
            fulldata = None

        # set a low voltage for safety
        self.alim.set_tx_voltage(12)

        # reshape full data to an array of good size
        # we need an array of regular size to save in the csv
        if tx_volt > 0:  # TODO what if have different array size?
            for a in fulldata:
                print(a.shape)
            fulldata = np.vstack(fulldata)
            # we create a big enough array given nb_samples, number of
            # half-cycles (1 stack = 2 half-cycles), and twice as we
            # measure decay as well
            nsamples = int((int(injection_duration * 1000) / duty) // 0.01 + 1)
            a = np.zeros((nb_stack * nsamples * 2, fulldata.shape[1])) * np.nan
            a[:fulldata.shape[0], :] = fulldata
            fulldata = a

        # create a dictionary and compute averaged values from all stacks
        d = {
            "time": datetime.now().isoformat(),
            "A": quad[0],
            "B": quad[1],
            "M": quad[2],
            "N": quad[3],
            "injtime [ms]": np.mean(injtimes),
            "Vmn [mV]": vmn,
            "I [mA]": iab,
            "R [ohm]": vmn/iab,
            "Ps [mV]": spon,
            "nbStack": nb_stack,
            "tmp [degC]": CPUTemperature().temperature if arm64_imports else -10,
            "Nb samples [-]": n2avg,
            "stacks": stacks,
            "fulldata": fulldata,
        }

        # to the data logger
        dd = d.copy()
        dd.pop('fulldata')  # too much for logger
        dd.update({'A': str(dd['A'])})
        dd.update({'B': str(dd['B'])})
        dd.update({'M': str(dd['M'])})
        dd.update({'N': str(dd['N'])})

        # round float to 2 decimal
        for key in dd.keys():
            if isinstance(dd[key], float):
                dd[key] = np.round(dd[key], 3)

        dd['cmd_id'] = str(cmd_id)
        self.data_logger.info(dd)

        return d
    
    def run_sequence(self, cmd_id=None, **kwargs):
        """Runs sequence synchronously (=blocking on main thread).
           Additional arguments are passed to run_measurement().

        Parameters
        ----------
        cmd_id : str, optional
            Unique command identifier.
        kwargs : optional
            Optional keyword arguments passed to run_measurement().
            See help(OhmPi.run_measurement).
        """
        self.status = 'running'
        self.exec_logger.debug(f'Status: {self.status}')
        self.exec_logger.debug(f'Measuring sequence: {self.sequence}')

        # create filename with timestamp
        filename = self.settings["export_path"].replace('.csv',
                                                        f'_{datetime.now().strftime("%Y%m%dT%H%M%S")}.csv')
        self.exec_logger.debug(f'Saving to {filename}')

        # make sure all multiplexer are off
        self.mux.reset()

        # measure all quadrupole of the sequence
        if self.sequence is None:
            seq = np.array([[0, 0, 0, 0]])
        else:
            seq = self.sequence.copy()
        for i in range(0, seq.shape[0]):
            quad = seq[i, :]
            if self.status == 'stopping':
                break

            # call the switch_mux function to switch to the right electrodes
            self.switch_mux_on(quad)

            # run a measurement
            acquired_data = self.run_measurement(quad, **kwargs)
            self.data_logger.info(acquired_data)

            # switch mux off
            self.switch_mux_off(quad)

            # add command_id in dataset
            acquired_data.update({'cmd_id': cmd_id})

            # log data to the data logger
            # self.data_logger.info(f'{acquired_data}')
            # save data and print in a text file
            self.append_and_save(filename, acquired_data)
            self.exec_logger.debug(f'quadrupole {i + 1:d}/{seq.shape[0]:d}')

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

    def run_multiple_sequences(self, sequence_delay=None, nb_meas=None, cmd_id=None, **kwargs):
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

    def _quad2qdic(self, quad):
        """Convert a quadrupole to a more flexible qdic
        of format {'A': [1], 'B': [2], 'M': [3], 'N': [4]}.
        This format enable to inject at several electrodes and
        is more flexible for multichannelling (we can add M1, N1, ...).
        
        Parameters
        ----------
        quad : list of int,
            List of quadrupoles. Electrodes equal to 0 are ignored.

        Returns
        -------
            Dictionnary in the form: {role: [list of electrodes]}.
        """
        return dict(zip(['A', 'B', 'M', 'N'], [[a] for a in quad if a > 0]))

    def switch_mux_on(self, quad):
        """"Switch quadrupoles on.
        
        Parameters
        ----------
        quad : list of int,
            List of quadrupoles. Electrodes equal to 0 are ignored.
        """
        qdic = self._quad2qdic(quad)
        self.mux.switch(qdic, 'on')

    def switch_mux_off(self, quad):
        """Switch quadrupoles off.
        
        Parameters
        ----------
        quad : list of int,
            List of quadrupoles. Electrodes equal to 0 are ignored.
        """
        qdic = self._quad2qdic(quad)
        self.mux.switch(qdic, 'off')

    def reset_mux(self):
        """Reset the mux, make sure all relays are off.
        """
        self.mux.reset()

    def rs_check(self, tx_volt=12., cmd_id=None):
        """Checks contact resistances.

        Parameters
        ----------
        tx_volt : float, optional
            Voltage of the injection.
        cmd_id : str, optional
            Unique command identifier.
        """
        # create custom sequence where MN == AB
        # we only check the electrodes which are in the sequence (not all might be connected)
        if self.sequence is None:
            quads = np.array([[1, 2, 0, 0]], dtype=np.uint32)
        else:
            elec = np.sort(np.unique(self.sequence.flatten()))  # assumed order
            quads = np.vstack([
                elec[:-1],
                elec[1:],
                np.zeros(len(elec)-1),
                np.zeros(len(elec)-1)
            ]).T

        # create filename to store RS
        export_path_rs = self.settings['export_path'].replace('.csv', '') \
                         + '_' + datetime.now().strftime('%Y%m%dT%H%M%S') + '_rs.csv'

        # perform RS check
        self.status = 'running'

        # make sure all mux are off to start with
        self.mux.reset()

        # turn on alim
        self.alim.turn_on()
        self.alim.set_tx_voltage(tx_volt)

        # measure all quad of the RS sequence
        for i in range(0, quads.shape[0]):
            quad = quads[i, :]  # quadrupole
            self.switch_mux_on(quad)  # put before raising the pins (otherwise conflict i2c)
            d = self.run_measurement(
                quad=quad, nb_stack=1, injection_duration=0.2,
                tx_volt=tx_volt, autogain=False)
            self.switch_mux_off(quad)

            voltage = d['Tx [V]']
            current = d['I [mA]'] / 1000.

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
        
        self.alim.turn_off()
        self.status = 'idle'

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
    
    def stop(self, **kwargs):
        warnings.warn('This function is deprecated. Use interrupt instead.', DeprecationWarning)
        self.interrupt(**kwargs)

    def _update_acquisition_settings(self, config):
        warnings.warn('This function is deprecated, use update_settings() instead.', DeprecationWarning)
        self.update_settings(settings=config)

    # Properties
    @property
    def sequence(self):
        """Gets sequence"""
        if self._sequence is not None:
            assert isinstance(self._sequence, np.ndarray)
        return self._sequence

    # TODO not sure if the below is still needed now we have a 
    # method set_sequence()
    @sequence.setter
    def sequence(self, sequence):
        """Sets sequence"""
        if sequence is not None:
            assert isinstance(sequence, np.ndarray)
            self.use_mux = True
        else:
            self.use_mux = False
        self._sequence = sequence


VERSION = '3.0.0'

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
