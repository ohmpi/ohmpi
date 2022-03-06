# -*- coding: utf-8 -*-
"""
created on January 6, 2020.
Update March 2022
Ohmpi.py is a program to control a low-cost and open hardware resistivity meter OhmPi that has been developed by
Rémi CLEMENT (INRAE),Vivien DUBOIS (INRAE), Hélène GUYARD (IGE), Nicolas FORQUET (INRAE), Yannick FARGIER (IFSTTAR)
Olivier KAUFMANN (UMONS) and Guillaume BLANCHY (ILVO).
"""

import os
import io
import json
import numpy as np
import csv
import time
from datetime import datetime
from termcolor import colored
import threading
from logging_setup import setup_loggers
# from mqtt_setup import mqtt_client_setup

# finish import (done only when class is instantiated as some libs are
# only available on arm64 platform)
try:
    import board
    import busio
    import adafruit_tca9548a
    import adafruit_ads1x15.ads1115 as ads
    from adafruit_ads1x15.analog_in import AnalogIn
    from adafruit_mcp230xx.mcp23008 import MCP23008
    from adafruit_mcp230xx.mcp23017 import MCP23017
    import digitalio
    from digitalio import Direction
    from gpiozero import CPUTemperature
    arm64_imports = True
except ImportError as e:
    print(f'Warning: {e}')
    arm64_imports = False

msg_logger, msg_log_filename, data_logger, data_log_filename, logging_level = setup_loggers()
# mqtt_client, measurement_topic = mqtt_client_setup()
# msg_logger.info(f'publishing mqtt to topic {measurement_topic}')
VERSION = '2.0.1'

print('\033[1m'+'\033[31m'+' ________________________________')
print(r'|  _  | | | ||  \/  || ___ \_   _|')
print(r'| | | | |_| || .  . || |_/ / | |')
print(r'| | | |  _  || |\/| ||  __/  | |')
print(r'\ \_/ / | | || |  | || |    _| |_')
print(r' \___/\_| |_/\_|  |_/\_|    \___/ ')
print('\033[0m')
print('OhmPi start')
print('Version:', VERSION)

current_time = datetime.now()
print(current_time.strftime("%Y-%m-%d %H:%M:%S"))


class OhmPi(object):
    """Create the main OhmPi object.

    Parameters
    ----------
    config : str, optional
        Path to the .json configuration file.
    sequence : str, optional
        Path to the .txt where the sequence is read. By default, a 1 quadrupole
        sequence: 1, 2, 3, 4 is used.
    output : str, optional
        Either 'print' for a console output or 'mqtt' for publication onto
        MQTT broker.
    """
    def __init__(self, config=None, sequence=None, output='print', data_logger=None, msg_logger=None, soh_logger=None):
        # flags and attributes
        # self.on_pi = on_pi  # True if run from the RaspberryPi with the hardware, otherwise False for random data
        self.output = output  # type of output print
        self.status = 'idle'  # either running or idle
        self.run = False  # flag is True when measuring
        self.thread = None  # contains the handle for the thread taking the measurement
        self.path = 'data/'  # where to save the .csv
        self.data_logger = data_logger
        self.msg_logger = msg_logger
        self.soh_logger = soh_logger


        if not arm64_imports:
            self.log_msg(f'Warning: {e}\n Some libraries only available on arm64 platform could not be imported.\n'
                      f'The Ohmpi class will fake operations for testing purposes.', 'warning')

        # read in hardware parameters (settings.py)
        self._read_hardware_parameters()

        # default acquisition parameters
        self.pardict = {
            'injection_duration': 0.2,
            'nbr_meas': 100,
            'sequence_delay': 1,
            'nb_stack': 1,
            'export_path': 'data/measurement.csv'
        }

        # read in acquisition parameters
        if config is not None:
            self._read_acquisition_parameters(config)

        self.log_msg('Initialized with configuration:' + str(self.pardict), level='debug')
    
        # read quadrupole sequence
        if sequence is None:
            self.sequence = np.array([[1, 2, 3, 4]])
        else:
            self.read_quad(sequence)

        # connect to components on the OhmPi board
        if self.on_pi:
            # activation of I2C protocol
            self.i2c = busio.I2C(board.SCL, board.SDA)

            # I2C connexion to MCP23008, for current injection
            self.mcp = MCP23008(self.i2c, address=0x20)
            
            # ADS1115 for current measurement (AB)
            self.ads_current = ads.ADS1115(self.i2c, gain=16, data_rate=860, address=0x48)
            
            # ADS1115 for voltage measurement (MN)
            self.ads_voltage = ads.ADS1115(self.i2c, gain=2/3, data_rate=860, address=0x49)

    def log_msg(self, msg, level='debug'):
        """Function for output management.

        Parameters
        ----------
        msg : str
            Body of the message.
        level : str, optional
            Level of the message, either: 'error', 'warn', 'debug'
        """
        # TODO all message to be logged using python logging library and rotating log

        if self.msg_logger is not None:
            self.msg_logger.info(msg)
        # if self.output == 'print':
        #     if level == 'error':
        #         print(colored(level.upper() + ' : ' + msg, 'red'))
        #     elif level == 'warn':
        #         print(colored(level.upper() + ' : ' + msg, 'yellow'))
        #     else:
        #         print(level.upper() + ' : ' + msg)
        # elif self.output == 'mqtt':
        #     if level == 'debug':
        #         # TODO mqtt transmission here
        #         pass

    def _read_acquisition_parameters(self, config):
        """Read acquisition parameters.
        Parameters can be:
            - nb_electrodes (number of electrode used, if 4, no MUX needed)
            - injection_duration (in seconds)
            - nbr_meas (total number of times the sequence will be run)
            - sequence_delay (delay in second between each sequence run)
            - stack (number of stack for each quadrupole measurement)
            - export_path (path where to export the data, timestamp will be added to filename)

        Parameters
        ----------
        config : str
            Path to the .json or dictionary.
        """
        if isinstance(config, dict):
            self.pardict.update(config)
        else:
            with open(config) as json_file:
                dic = json.load(json_file)
            self.pardict.update(dic)
        self.log_msg('Acquisition parameters updated: ' + str(self.pardict), level='debug')

    def _read_hardware_parameters(self):
        """Read hardware parameters from settings.py.
        """
        from settings import OHMPI_CONFIG
        self.id = OHMPI_CONFIG['id']  # ID of the OhmPi
        self.r_shunt = OHMPI_CONFIG['R_shunt']  # reference resistance value in ohm
        self.Imax = OHMPI_CONFIG['Imax']  # maximum current
        self.log_msg(f'The maximum current cannot be higher than {self.Imax} mA', level='warn')
        self.coef_p2 = OHMPI_CONFIG['coef_p2']  # slope for current conversion for ads.P2, measurement in V/V
        self.coef_p3 = OHMPI_CONFIG['coef_p3']  # slope for current conversion for ads.P3, measurement in V/V
        self.offset_p2 = OHMPI_CONFIG['offset_p2']
        self.offset_p3 = OHMPI_CONFIG['offset_p3']
        self.nb_samples = OHMPI_CONFIG['integer']  # number of samples measured for each stack
        self.version = OHMPI_CONFIG['version']  # hardware version
        self.max_elec = OHMPI_CONFIG['max_elec']  # maximum number of electrodes
        self.board_address = OHMPI_CONFIG['board_address']
        self.log_msg('OHMPI_CONFIG = ' + str(OHMPI_CONFIG), level='debug')

    @staticmethod
    def find_identical_in_line(quads):
        """Find quadrupole which where A and B are identical.
        If A and B are connected to the same relay, the Pi burns (short-circuit).
        
        Parameters
        ----------
        quads : 1D or 2D array
            List of quadrupoles of shape nquad x 4 or 1D vector of shape nquad.
        
        Returns
        -------
        output : 1D array of int
            List of index of rows where A and B are identical.
        """
        # TODO is this needed for M and N?

        # if we have a 1D array (so only 1 quadrupole), make it 2D
        if len(quads.shape) == 1:
            quads = quads[None, :]

        output = np.where(quads[:, 0] == quads[:, 1])[0]

        # output = []
        # if array_object.ndim == 1:
        #     temp = np.zeros(4)
        #     for i in range(len(array_object)):
        #         temp[i] = np.count_nonzero(array_object == array_object[i])
        #     if any(temp > 1):
        #         output.append(0)
        # else:
        #     for i in range(len(array_object[:,1])):
        #         temp = np.zeros(len(array_object[1,:]))
        #         for j in range(len(array_object[1,:])):
        #             temp[j] = np.count_nonzero(array_object[i,:] == array_object[i,j])
        #         if any(temp > 1):
        #             output.append(i)
        return output

    @property
    def on_pi(self):
        """Returns True if code is running on a raspberry pi and required arm64 libs have been imported"""
        running_on_pi = False
        try:
            with io.open('/sys/firmware/devicetree/base/model', 'r') as f:
                if 'raspberry pi' in f.read().lower():
                    running_on_pi = True
        except FileNotFoundError:
            pass
        return running_on_pi and arm64_imports

    def read_quad(self, filename):
        """Read quadrupole sequence from file.

        Parameters
        ----------
        filename : str
            Path of the .csv or .txt file with A, B, M and N electrodes.
            Electrode index start at 1.

        Returns
        -------
        output : numpy.array
            Array of shape (number quadrupoles * 4).
        """
        output = np.loadtxt(filename, delimiter=" ", dtype=int)  # load quadrupole file
        
        # locate lines where the electrode index exceeds the maximum number of electrodes
        test_index_elec = np.array(np.where(output > self.max_elec))
        
        # locate lines where electrode A == electrode B
        test_same_elec = self.find_identical_in_line(output)
        
        # if statement with exit cases (TODO rajouter un else if pour le deuxième cas du ticket #2)
        if test_index_elec.size != 0:
            for i in range(len(test_index_elec[0, :])):
                self.log_msg('Error: An electrode index at line ' + str(test_index_elec[0, i] + 1) +
                          ' exceeds the maximum number of electrodes', level='error')
            # sys.exit(1)
            output = None
        elif len(test_same_elec) != 0:
            for i in range(len(test_same_elec)):
                self.log_msg('Error: An electrode index A == B detected at line ' + str(test_same_elec[i] + 1),
                             level="error")
            # sys.exit(1)
            output = None

        if output is not None:
            self.log_msg('Sequence of {:d} quadrupoles read.'.format(output.shape[0]), level='debug')
    
        self.sequence = output

    def switch_mux(self, electrode_nr, state, role):
        """Select the right channel for the multiplexer cascade for a given electrode.
        
        Parameters
        ----------
        electrode_nr : int
            Electrode index to be switched on or off.
        state : str
            Either 'on' or 'off'.
        role : str
            Either 'A', 'B', 'M' or 'N', so we can assign it to a MUX board.
        """
        if self.sequence.max() <= 4:  # only 4 electrodes so no MUX
            pass
        else:
            # choose with MUX board
            tca = adafruit_tca9548a.TCA9548A(self.i2c, self.board_address[role])
            
            # find I2C address of the electrode and corresponding relay
            # TODO from number of electrode, the below can be guessed
            # considering that one MCP23017 can cover 16 electrodes
            electrode_nr = electrode_nr - 1  # switch to 0 indexing
            i2c_address = 7 - electrode_nr // 16  # quotient without rest of the division
            relay_nr = electrode_nr - (electrode_nr // 16)*16
            relay_nr = relay_nr + 1  # switch back to 1 based indexing

            # if electrode_nr < 17:
            #     i2c_address = 7
            #     relay_nr = electrode_nr
            # elif 16 < electrode_nr < 33:
            #     i2c_address = 6
            #     relay_nr = electrode_nr - 16
            # elif 32 < electrode_nr < 49:
            #     i2c_address = 5
            #     relay_nr = electrode_nr - 32
            # elif 48 < electrode_nr < 65:
            #     i2c_address = 4
            #     relay_nr = electrode_nr - 48

            if i2c_address is not None:
                # select the MCP23017 of the selected MUX board
                mcp2 = MCP23017(tca[i2c_address])
                mcp2.get_pin(relay_nr-1).direction = digitalio.Direction.OUTPUT
                
                if state == 'on':
                    mcp2.get_pin(relay_nr-1).value = True
                else:
                    mcp2.get_pin(relay_nr-1).value = False
                
                self.log_msg(f'Switching relay {relay_nr} {state} for electrode {electrode_nr}', level='debug')
            else:
                self.log_msg(f'Unable to address electrode nr {electrode_nr}', level='warn')

    def switch_mux_on(self, quadrupole):
        """Switch on multiplexer relays for given quadrupole.
        
        Parameters
        ----------
        quadrupole : list of 4 int
            List of 4 integers representing the electrode numbers.
        """
        roles = ['A', 'B', 'M', 'N']
        # another check to be sure A != B
        if quadrupole[0] != quadrupole[1]:
            for i in range(0, 4):
                self.switch_mux(quadrupole[i], 'on', roles[i])
        else:
            self.log_msg('A == B -> short circuit detected!', level='error')

    def switch_mux_off(self, quadrupole):
        """Switch off multiplexer relays for given quadrupole.
        
        Parameters
        ----------
        quadrupole : list of 4 int
            List of 4 integers representing the electrode numbers.
        """
        roles = ['A', 'B', 'M', 'N']
        for i in range(0, 4):
            self.switch_mux(quadrupole[i], 'off', roles[i])

    def reset_mux(self):
        """Switch off all multiplexer relays."""
        roles = ['A', 'B', 'M', 'N']
        for i in range(0, 4):
            for j in range(1, self.max_elec + 1):
                self.switch_mux(j, 'off', roles[i])
        self.log_msg('All MUX switched off.', level='debug')

    def run_measurement(self, quad, nb_stack=None, injection_duration=None):  # NOTE: quad not used?!
        """ Do a 4 electrode measurement and measure transfer resistance obtained.

        Parameters
        ----------
        nb_stack : int, optional
            Number of stacks.
        injection_duration : int, optional
            Injection time in seconds.
        quad : list of int
            Quadrupole to measure.
        """
        # TODO here we can add the current_injected or voltage_injected in mA or mV
        # check arguments
        if nb_stack is None:
            nb_stack = self.pardict['stack']
        if injection_duration is None:
            injection_duration = self.pardict['injection_duration']

        start_time = time.time()

        # inner variable initialization
        injection_current = 0
        sum_vmn = 0
        sum_ps = 0
        
        # injection courant and measure
        pin0 = self.mcp.get_pin(0)
        pin0.direction = Direction.OUTPUT
        pin1 = self.mcp.get_pin(1)
        pin1.direction = Direction.OUTPUT
        pin0.value = False
        pin1.value = False
        
        # TODO I don't get why 3 + 2*nb_stack - 1? why not just rnage(nb_stack)?
        # or do we consider 1 stack = one full polarity? do we discard the first 3 readings?
        for n in range(0, 3+2*nb_stack-1):
            # current injection
            if (n % 2) == 0:
                pin1.value = True
                pin0.value = False  # current injection polarity nr1
            else:
                pin0.value = True
                pin1.value = False  # current injection nr2
            start_delay = time.time()  # stating measurement time
            time.sleep(injection_duration)  # delay depending on current injection duration

            # measurement of current i and voltage u
            # sampling for each stack at the end of the injection
            meas = np.zeros((self.nb_samples, 3))
            for k in range(0, self.nb_samples):
                # reading current value on ADS channel A0
                meas[k, 0] = (AnalogIn(self.ads_current, ads.P0).voltage*1000) / (50 * self.r_shunt)
                meas[k, 1] = AnalogIn(self.ads_voltage, ads.P0).voltage * self.coef_p2 * 1000
                # reading voltage value on ADS channel A2
                meas[k, 2] = AnalogIn(self.ads_voltage, ads.P1).voltage * self.coef_p3 * 1000

            # stop current injection
            pin1.value = False
            pin0.value = False
            end_delay = time.time()

            # take average from the samples per stack, then sum them all
            # average for all stack is done outside the loop
            injection_current = injection_current + (np.mean(meas[:, 0]))
            vmn1 = np.mean(meas[:, 1]) - np.mean(meas[:, 2])
            if (n % 2) == 0:
                sum_vmn = sum_vmn - vmn1
                sum_ps = sum_ps + vmn1
            else:
                sum_vmn = sum_vmn + vmn1
                sum_ps = sum_ps + vmn1

            # TODO get battery voltage and warn if battery is running low
            
            end_calc = time.time()

            # TODO I am not sure I understand the computation below
            # wait twice the actual injection time between two injection
            # so it's a 50% duty cycle right?
            time.sleep(2*(end_delay-start_delay)-(end_calc-start_delay))
            
        # create a dictionary and compute averaged values from all stacks
        d = {
            "time": [datetime.now()],
            "A": [1],
            "B": [2],
            "M": [3],
            "N": [4],
            "inj time [ms]": (end_delay - start_delay) * 1000,
            "Vmn [mV]": [(sum_vmn / (3 + 2 * nb_stack - 1))],
            "I [mA]": [(injection_current / (3 + 2 * nb_stack - 1))],
            "R [ohm]": [(sum_vmn / (3 + 2 * nb_stack - 1) / (injection_current / (3 + 2 * nb_stack - 1)))],
            "Ps [mV]": [(sum_ps / (3 + 2 * nb_stack - 1))],
            "nbStack": [nb_stack],
            "CPU temp [degC]": [CPUTemperature().temperature],
            "Time [s]": [(-start_time + time.time())],
            "Nb samples [-]": [self.nb_samples]    
        }

        # round number to two decimal for nicer string output
        output = [f'{d[k]}\t' for k in d.keys]
        output = output[:-1] + '\n'
        for k in d.keys:
            if isinstance(d[k], float):
                val = np.round(d[k], 2)
            else:
                val = d[k]
                output += f'{val}\t'
        output = output[:-1]
        self.log_msg(output, level='debug')
        time.sleep(1)  # NOTE: why this?

        return d

    def rs_check(self):
        """Check contact resistance.
        """
        # create custom sequence where MN == AB
        nelec = self.sequence.max()  # number of elec used in the sequence
        quads = np.vstack([
            np.arange(nelec - 1) + 1,
            np.arange(nelec - 1) + 2,
            np.arange(nelec - 1) + 1,
            np.arange(nelec - 1) + 2
            ]).T
        
        # create backup TODO not good
        export_path = self.pardict['export_path'].copy()
        sequence = self.sequence.copy()

        # assign new value
        self.pardict['export_path'] = export_path.replace('.csv', '_rs.csv')
        self.sequence = quads
        
        # run the RS check
        self.log_msg('RS check (check contact resistance)', level='debug')
        self.measure()
        
        # restore
        self.pardict['export_path'] = export_path
        self.sequence = sequence

        # TODO if interrupted, we would need to restore the values
        # TODO or we offer the possiblity in 'run_measurement' to have rs_check each time?

    @staticmethod
    def append_and_save(fname, last_measurement):
        """Append and save last measurement dataframe.

        Parameters
        ----------
        fname : str
            filename to save the last measurement dataframe
        last_measurement : dict
            Last measurement taken in the form of a python dictionary
        """
        
        if os.path.isfile(fname):
            # Load data file and append data to it
            with open(fname, 'a') as f:
                w = csv.DictWriter(f, last_measurement.keys())
                w.writerow(last_measurement)
                # last_measurement.to_csv(f, header=False)
        else:
            # create data file and add headers
            with open(fname, 'a') as f:
                w = csv.DictWriter(f, last_measurement.keys())
                w.writeheader()
                w.writerow(last_measurement)
                # last_measurement.to_csv(f, header=True)

    def measure(self):
        """Run the sequence in a separate thread. Can be stopped by 'OhmPi.stop()'.
        """
        self.run = True
        self.status = 'running'
        self.log_msg('status = ' + self.status, level='debug')

        def func():
            for g in range(0, self.pardict["nbr_meas"]):  # for time-lapse monitoring
                if self.run is False:
                    self.log_msg('INTERRUPTED', level='debug')
                    break
                t0 = time.time()

                # create filename with timestamp
                fname = self.pardict["export_path"].replace('.csv', '_' + datetime.now().strftime('%Y%m%dT%H%M%S')
                                                            + '.csv')
                self.log_msg('saving to ' + fname, level='debug')

                # make sure all multiplexer are off
                self.reset_mux()

                # measure all quadrupole of the sequence
                for i in range(0, self.sequence.shape[0]):
                    quad = self.sequence[i, :]  # quadrupole
                    if self.run is False:
                        break
                    
                    # call the switch_mux function to switch to the right electrodes
                    self.switch_mux_on(quad)

                    # run a measurement
                    if self.on_pi:
                        current_measurement = self.run_measurement(quad, self.pardict["stack"],
                                                                   self.pardict["injection_duration"])
                    else:  # for testing, generate random data
                        current_measurement = {
                            'A': [quad[0]], 'B': [quad[1]], 'M': [quad[2]], 'N': [quad[3]],
                            'R [ohm]': np.abs(np.random.randn(1))
                        }
                    
                    # switch mux off
                    self.switch_mux_off(quad)

                    # save data and print in a text file
                    self.append_and_save(fname, current_measurement)
                    self.log_msg('{:d}/{:d}'.format(i + 1, self.sequence.shape[0]), level='debug')

                # compute time needed to take measurement and subtract it from interval
                # between two sequence run (= sequence_delay)
                measuring_time = time.time() - t0
                sleep_time = self.pardict["sequence_delay"] - measuring_time
                
                if sleep_time < 0:
                    # it means that the measuring time took longer than the sequence delay
                    sleep_time = 0
                    self.log_msg('The measuring time is longer than the sequence delay. Increase the sequence delay',
                                 level='warn')

                # sleeping time between sequence
                if self.pardict["nbr_meas"] > 1:
                    time.sleep(sleep_time)  # waiting for next measurement (time-lapse)
            self.status = 'idle'
        self.thread = threading.Thread(target=func)
        self.thread.start()

    def stop(self):
        """Stop the acquisition.
        """
        self.run = False
        if self.thread is not None:
            self.thread.join()
        self.log_msg('status = ' + self.status)


# for testing
if __name__ == "__main__":
    ohmpi = OhmPi(config='ohmpi_param.json')
    ohmpi.measure()
    time.sleep(4)
    ohmpi.stop()
