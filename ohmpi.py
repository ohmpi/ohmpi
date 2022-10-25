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
import minimalmodbus  # for programmable power supply

# from mqtt_setup import mqtt_client_setup

# finish import (done only when class is instantiated as some libs are only available on arm64 platform)
try:
    import board  # noqa
    import busio  # noqa
    import adafruit_tca9548a  # noqa
    import adafruit_ads1x15.ads1115 as ads  # noqa
    from adafruit_ads1x15.analog_in import AnalogIn  # noqa
    from adafruit_mcp230xx.mcp23008 import MCP23008  # noqa
    from adafruit_mcp230xx.mcp23017 import MCP23017  # noqa
    import digitalio  # noqa
    from digitalio import Direction  # noqa
    from gpiozero import CPUTemperature  # noqa

    arm64_imports = True
except ImportError as error:
    print(colored(f'Import error: {error}', 'yellow'))
    arm64_imports = False
except Exception as error:
    print(colored(f'Unexpected error: {error}', 'red'))
    exit()


class OhmPi(object):
    """Create the main OhmPi object.

    Parameters
    ----------
    config : str, optional
        Path to the .json configuration file.
    sequence : str, optional
        Path to the .txt where the sequence is read. By default, a 1 quadrupole
        sequence: 1, 2, 3, 4 is used.
    """

    def __init__(self, config=None, sequence=None, mqtt=False, on_pi=None, idps=False):
        # flags and attributes
        if on_pi is None:
            _, on_pi = OhmPi.get_platform()
        self.sequence = sequence
        self.on_pi = on_pi  # True if run from the RaspberryPi with the hardware, otherwise False for random data
        self.status = 'idle'  # either running or idle
        self.run = False  # flag is True when measuring
        self.thread = None  # contains the handle for the thread taking the measurement
        self.path = 'data/'  # where to save the .csv

        # set loggers
        config_exec_logger, _, config_data_logger, _, _ = setup_loggers(mqtt=mqtt)  # TODO: add SOH
        self.data_logger = config_data_logger
        self.exec_logger = config_exec_logger
        self.soh_logger = None
        print('Loggers:')
        print(colored(f'Exec logger {self.exec_logger.handlers if self.exec_logger is not None else "None"}', 'blue'))
        print(colored(f'Data logger {self.data_logger.handlers if self.data_logger is not None else "None"}', 'blue'))
        print(colored(f'SOH logger {self.soh_logger.handlers if self.soh_logger is not None else "None"}', 'blue'))

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

        self.exec_logger.debug('Initialized with configuration:' + str(self.pardict))

        # read quadrupole sequence
        if sequence is None:
            self.sequence = np.array([[1, 2, 3, 4]])
        else:
            self.read_quad(sequence)

        self.idps = idps  # flag to use dps for injection or not
        
        # connect to components on the OhmPi board
        if self.on_pi:
            # activation of I2C protocol
            self.i2c = busio.I2C(board.SCL, board.SDA)  # noqa

            # I2C connexion to MCP23008, for current injection
            self.mcp = MCP23008(self.i2c, address=0x20)

            # ADS1115 for current measurement (AB)
            self.ads_current = ads.ADS1115(self.i2c, gain=2 / 3, data_rate=128, address=0x49)

            # ADS1115 for voltage measurement (MN)
            self.ads_voltage = ads.ADS1115(self.i2c, gain=2 / 3, data_rate=128, address=0x48)

            # current injection module
            if self.idps:
                self.DPS = minimalmodbus.Instrument(port='/dev/ttyUSB0', slaveaddress=1) # port name, slave address (in decimal)
                self.DPS.serial.baudrate = 9600                      # Baud rate 9600 as listed in doc
                self.DPS.serial.bytesize = 8                         # 
                self.DPS.serial.timeout  = 1                         # greater than 0.5 for it to work
                self.DPS.debug           = False                     # 
                self.DPS.serial.parity   = 'N'                       # No parity
                self.DPS.mode            = minimalmodbus.MODE_RTU    # RTU mode
                self.DPS.write_register(0x0001, 40, 0)   # max current allowed (36 mA for relays)
                # (last number) 0 is for mA, 3 is for A
            
            # injection courant and measure (TODO check if it works, otherwise back in run_measurement())
            self.pin0 = self.mcp.get_pin(0)
            self.pin0.direction = Direction.OUTPUT
            self.pin0.value = False
            self.pin1 = self.mcp.get_pin(1)
            self.pin1.direction = Direction.OUTPUT
            self.pin1.value = False


    def _read_acquisition_parameters(self, config):
        """Read acquisition parameters.
        Parameters can be:
            - nb_electrodes (number of electrode used, if 4, no MUX needed)
            - injection_duration (in seconds)
            - nbr_meas (total number of times the sequence will be run)
            - sequence_delay (delay in second between each sequence run)
            - nb_stack (number of stack for each quadrupole measurement)
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
        self.exec_logger.debug('Acquisition parameters updated: ' + str(self.pardict))


    def _read_hardware_parameters(self):
        """Read hardware parameters from config.py
        """
        from config import OHMPI_CONFIG
        self.id = OHMPI_CONFIG['id']  # ID of the OhmPi
        self.r_shunt = OHMPI_CONFIG['R_shunt']  # reference resistance value in ohm
        self.Imax = OHMPI_CONFIG['Imax']  # maximum current
        self.exec_logger.warning(f'The maximum current cannot be higher than {self.Imax} mA')
        self.coef_p2 = OHMPI_CONFIG['coef_p2']  # slope for current conversion for ads.P2, measurement in V/V
        self.coef_p3 = OHMPI_CONFIG['coef_p3']  # slope for current conversion for ads.P3, measurement in V/V
        # self.offset_p2 = OHMPI_CONFIG['offset_p2'] parameter removed
        # self.offset_p3 = OHMPI_CONFIG['offset_p3'] parameter removed
        self.nb_samples = OHMPI_CONFIG['integer']  # number of samples measured for each stack
        self.version = OHMPI_CONFIG['version']  # hardware version
        self.max_elec = OHMPI_CONFIG['max_elec']  # maximum number of electrodes
        self.board_address = OHMPI_CONFIG['board_address']
        self.exec_logger.debug(f'OHMPI_CONFIG = {str(OHMPI_CONFIG)}')


    @staticmethod
    def find_identical_in_line(quads):
        """Find quadrupole which where A and B are identical.
        If A and B are connected to the same relay, the Pi burns (short-circuit).
        
        Parameters
        ----------
        quads : numpy.ndarray
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


    @staticmethod
    def get_platform():
        """Get platform name and check if it is a raspberry pi
        Returns
        =======
        str, bool
            name of the platform on which the code is running, boolean that is true if the platform is a raspberry pi"""

        platform = 'unknown'
        on_pi = False
        try:
            with io.open('/sys/firmware/devicetree/base/model', 'r') as f:
                platform = f.read().lower()
            if 'raspberry pi' in platform:
                on_pi = True
        except FileNotFoundError:
            pass
        return platform, on_pi


    def read_quad(self, filename):
        """Read quadrupole sequence from file.

        Parameters
        ----------
        filename : str
            Path of the .csv or .txt file with A, B, M and N electrodes.
            Electrode index start at 1.

        Returns
        -------
        output : numpy.ndarray
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
                self.exec_logger.error(f'An electrode index at line {str(test_index_elec[0, i] + 1)} '
                                       f'exceeds the maximum number of electrodes')
            # sys.exit(1)
            output = None
        elif len(test_same_elec) != 0:
            for i in range(len(test_same_elec)):
                self.exec_logger.error(f'An electrode index A == B detected at line {str(test_same_elec[i] + 1)}')
            # sys.exit(1)
            output = None

        if output is not None:
            self.exec_logger.debug('Sequence of {:d} quadrupoles read.'.format(output.shape[0]))

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
            relay_nr = electrode_nr - (electrode_nr // 16) * 16
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
                mcp2.get_pin(relay_nr - 1).direction = digitalio.Direction.OUTPUT

                if state == 'on':
                    mcp2.get_pin(relay_nr - 1).value = True
                else:
                    mcp2.get_pin(relay_nr - 1).value = False

                self.exec_logger.debug(f'Switching relay {relay_nr} {state} for electrode {electrode_nr}')
            else:
                self.exec_logger.warning(f'Unable to address electrode nr {electrode_nr}')


    def switch_mux_on(self, quadrupole):
        """ Switch on multiplexer relays for given quadrupole.
        
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
            self.exec_logger.error('A == B -> short circuit risk detected!')

    def switch_mux_off(self, quadrupole):
        """ Switch off multiplexer relays for given quadrupole.
        
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
        self.exec_logger.debug('All MUX switched off.')


    def gain_auto(self, channel):
        """ Automatically set the gain on a channel

        Parameters
        ----------
        channel:

        Returns
        -------
            float
        """
        gain = 2 / 3
        if (abs(channel.voltage) < 2.040) and (abs(channel.voltage) >= 1.023):
            gain = 2
        elif (abs(channel.voltage) < 1.023) and (abs(channel.voltage) >= 0.508):
            gain = 4
        elif (abs(channel.voltage) < 0.508) and (abs(channel.voltage) >= 0.250):
            gain = 8
        elif abs(channel.voltage) < 0.256:
            gain = 16
        self.exec_logger.debug(f'Setting gain to {gain}')
        return gain


    def compute_tx_volt(self, best_tx_injtime=1):
        """Compute best voltage to inject to be in our range of Vmn 
        (10 mV - 4500 mV) and current (2 - 45 mA)
        """
        # inferring best voltage for injection Vab
        # we guess the polarity on Vmn by trying both cases. once found
        # we inject a starting voltage of 5V and measure our Vmn. Based
        # on the data we then compute a multiplifcation factor to inject
        # a voltage that will fall right in the measurable range of Vmn
        # (10 - 4500 mV) and current (45 mA max)
        
        # select a polarity to start with
        self.pin0.value = True
        self.pin1.value = False
        self.DPS.write_register(0x09, 1) # DPS5005 on

        tau = np.nan
        # voltage optimization
        for volt in range(2, 10, 2):
            print('trying with v:', volt)
            self.DPS.write_register(0x0000,volt,2) # fixe la voltage pour la mesure à 5V
            time.sleep(best_tx_injtime) # inject for 1 s at least on DPS5005
            
            # autogain
            self.ads_current = ads.ADS1115(self.i2c, gain=2/3, data_rate=128, address=0x49)
            self.ads_voltage = ads.ADS1115(self.i2c, gain=2/3, data_rate=128, address=0x48)
            print('current P0', AnalogIn(self.ads_current, ads.P0).voltage)
            print('voltage P0', AnalogIn(self.ads_voltage, ads.P0).voltage)
            print('voltage P2', AnalogIn(self.ads_voltage, ads.P2).voltage)
            gain_current = self.gain_auto(AnalogIn(self.ads_current, ads.P0))
            gain_voltage0 = self.gain_auto(AnalogIn(self.ads_voltage, ads.P0))
            gain_voltage2 = self.gain_auto(AnalogIn(self.ads_voltage, ads.P2))
            gain_voltage = np.min([gain_voltage0, gain_voltage2])
            print('gain current: {:.3f}, gain voltage: {:.3f}'.format(gain_current, gain_voltage))
            self.ads_current = ads.ADS1115(self.i2c, gain=gain_current, data_rate=128, address=0x49)
            self.ads_voltage = ads.ADS1115(self.i2c, gain=gain_voltage, data_rate=128, address=0x48)
            
            # we measure the voltage on both A0 and A2 to guess the polarity
            I = (AnalogIn(self.ads_current, ads.P0).voltage) * 1000/50/2 # measure current
            U0 = AnalogIn(self.ads_voltage, ads.P0).voltage * 1000 # measure voltage
            U2 = AnalogIn(self.ads_voltage, ads.P2).voltage * 1000
            print('I (mV)', I*50*2)
            print('I (mA)', I)
            print('U0 (mV)', U0)
            print('U2 (mV)', U2)
            
            # check polarity
            polarity = 1  # by default, we guessed it right
            if U0 < 0: # we guessed it wrong, let's use a correction factor
                polarity = -1
            print('polarity', polarity)
            # TODO (edge case) if PS is negative and greater than Vmn, it can 
            # potentially cause two negative values so none above 0
                
            # check if we can actually measure smth
            ok = True
            if I > 2 and I <= 45:
                if (((U0 < 4500) and (polarity > 0)) 
                or ((2 < 4500) and (polarity < 0))):
                    if (((U0 > 10) and (polarity > 0)) 
                    or ((U2 > 10) and (polarity < 0))):
                        # ok, we compute tau
                        # inferring polarity and computing best voltage to inject
                        # by hardware design we can measure 10-4500 mV and 2-45 mA
                        # we will decide on the Vab to fall within this range
                        if U0 > 0: # we guessed the polarity right, let's keep that
                            tauI = 45 / I # compute ratio to maximize measuring range of I
                            tauU = 4500 / U0 # compute ratio to maximize measuring range of U
                        elif U0 < 0: # we guessed it wrong, let's use a correction factor
                            tauI = 45 / I
                            tauU = 4500 / U2
                         
                        # let's be careful and avoid saturation by taking only 90% of 
                        # the smallest factor      
                        if tauI < tauU:
                            tau = tauI * 0.9
                        elif tauI > tauU:
                            tau = tauU * 0.9
                        print('tauI', tauI)
                        print('tauU', tauU)
                        print('best tau is', tau)
                        break
                    else:
                        # too weak, but let's try with a higher voltage
                        pass  # we'll come back to the loop with higher voltage
                else:
                    print('voltage out of range, max 4500 mV')
                    # doesn't work, tau will be NaN
                    break
            else:
                if I <= 2:
                    # let's try again
                    pass
                else:
                    print('current out of range, max 45 mA')
                    # doesn't work, tau will be NaN
                    break
        if tau == np.nan:
            print('voltage out of range')
            self.DPS.write_register(0x09, 0) # DPS5005 off
        # we keep DPS5005 on if we computed a tau successfully
        
        # turn off Vab
        self.pin0.value = False
        self.pin1.value = False
            
        return tau*volt, polarity
        

    def run_measurement(self, quad=[1, 2, 3, 4], nb_stack=None, injection_duration=None,
                        best_tx=True, tx_volt=0, autogain=True, best_tx_injtime=1):
        """Do a 4 electrode measurement and measure transfer resistance obtained.

        Parameters
        ----------
        quad : list of int
            Quadrupole to measure.
        nb_stack : int, optional
            Number of stacks. A stacl is considered two half-cycles (one
            positive, one negative).
        injection_duration : int, optional
            Injection time in seconds.
        best_tx : bool, optional
            If True, will attempt to find the best Tx voltage that fill
            within our measurement range. If it cannot find it, it will
            return NaN as measurement. If False, it will make the
            measurement with whatever it has as voltage and never returns
            NaN. Finding the best tx voltage can take some time before
            each quadrupole.
        tx_volt : float, optional
            If specified, voltage will be imposed disregarding the value
            of best_tx argument.
        autogain : bool, optional
            If True, will adapt the gain of the ADS1115 to maximize the
            resolution of the reading.
        """
        # check arguments
        if nb_stack is None:
            nb_stack = self.pardict['nb_stack']
        if injection_duration is None:
            injection_duration = self.pardict['injection_duration']

        start_time = time.time()

        # inner variable initialization
        sum_i = 0
        sum_vmn = 0
        sum_ps = 0

        self.exec_logger.debug('Starting measurement')
        self.exec_logger.info('Waiting for data')

        # get best voltage to inject
        if self.idps and tx_volt == 0:
            tx_volt, polarity = self.compute_tx_volt(best_tx_injtime=best_tx_injtime)
            print('tx volt V:', tx_volt)
        else:
            polarity = 1
        
        # first reset the gain to 2/3 before trying to find best gain
        self.ads_current = ads.ADS1115(self.i2c, gain=2 / 3, data_rate=128, address=0x49)
        self.ads_voltage = ads.ADS1115(self.i2c, gain=2 / 3, data_rate=128, address=0x48)
        
        # turn on the power supply
        oor = False
        if self.idps:
            if tx_volt != np.nan:
                self.DPS.write_register(0x0000, tx_volt, 2) # set tx voltage in V
                self.DPS.write_register(0x09, 1) # DPS5005 on
            else:
                print('no best voltage found, will not take measurement')
                oor = True
                
        if oor == False:
            if autogain:
                # compute autogain
                self.pin0.value = True
                self.pin1.value = False
                time.sleep(injection_duration)
                gain_current = self.gain_auto(AnalogIn(self.ads_current, ads.P0))
                if polarity > 0:
                    gain_voltage = self.gain_auto(AnalogIn(self.ads_voltage, ads.P0))
                else:
                    gain_voltage = self.gain_auto(AnalogIn(self.ads_voltage, ads.P2))
                self.pin0.value = False
                self.pin1.value = False
                print('gain current: {:.3f}, gain voltage: {:.3f}'.format(gain_current, gain_voltage))
                self.ads_current = ads.ADS1115(self.i2c, gain=gain_current, data_rate=128, address=0x49)
                self.ads_voltage = ads.ADS1115(self.i2c, gain=gain_voltage, data_rate=128, address=0x48)

            # one stack = 2 half-cycles (one positive, one negative)
            pinMN = 0 if polarity > 0 else 2
            for n in range(0, nb_stack * 2):  # for each half-cycles
                # current injection
                if (n % 2) == 0:
                    self.pin0.value = True
                    self.pin1.value = False
                else:
                    self.pin0.value = False
                    self.pin1.value = True  # current injection nr2
                    
                start_delay = time.time()  # stating measurement time
                time.sleep(injection_duration)  # delay depending on current injection duration

                # measurement of current i and voltage u
                # sampling for each stack at the end of the injection
                meas = np.zeros((self.nb_samples, 2))
                for k in range(0, self.nb_samples):
                    # reading current value on ADS channel A0
                    meas[k, 0] = (AnalogIn(self.ads_current, ads.P0).voltage * 1000) / (50 * self.r_shunt)
                    if pinMN == 0:
                        meas[k, 1] = AnalogIn(self.ads_voltage, ads.P0).voltage * 1000
                    else:
                        meas[k, 1] = AnalogIn(self.ads_voltage, ads.P2).voltage * 1000 *-1
                print(meas)
                
                # we alternate on which ADS1115 pin we measure because of sign of voltage
                if pinMN == 0:
                    pinMN = 2
                else:
                    pinMN = 0
                
                # stop current injection
                self.pin0.value = False
                self.pin1.value = False
                end_delay = time.time()

                # take average from the samples per stack, then sum them all
                # average for all stack is done outside the loop
                sum_i = sum_i + (np.mean(meas[:, 0]))
                vmn1 = np.mean(meas[:, 1])
                if (n % 2) == 0:
                    sum_vmn = sum_vmn - vmn1
                    sum_ps = sum_ps + vmn1
                else:
                    sum_vmn = sum_vmn + vmn1
                    sum_ps = sum_ps + vmn1

                # TODO get battery voltage and warn if battery is running low
                # TODO send a message on SOH stating the battery level
                end_calc = time.time()

                # TODO I am not sure I understand the computation below
                # wait twice the actual injection time between two injection
                # so it's a 50% duty cycle right?
                time.sleep(2 * (end_delay - start_delay) - (end_calc - start_delay))
                
            if self.idps:
                self.DPS.write_register(0x0000, 0, 2)  # reset to 0 volt
                self.DPS.write_register(0x09, 0) # DPS5005 off
        else:
            sum_i = np.nan
            sum_vmn = np.nan
            sum_ps = np.nan

        # create a dictionary and compute averaged values from all stacks
        d = {
            "time": datetime.now().isoformat(),
            "A": quad[0],
            "B": quad[1],
            "M": quad[2],
            "N": quad[3],
            "inj time [ms]": (end_delay - start_delay) * 1000,
            "Vmn [mV]": sum_vmn / (2 * nb_stack),
            "I [mA]": sum_i / (2 * nb_stack),
            "R [ohm]": sum_vmn / sum_i,
            "Ps [mV]": sum_ps / (2 * nb_stack),
            "nbStack": nb_stack,
            "CPU temp [degC]": CPUTemperature().temperature,
            "Time [s]": (-start_time + time.time()),
            "Nb samples [-]": self.nb_samples
        }
        print(d)
        
        # round number to two decimal for nicer string output
        output = [f'{k}\t' for k in d.keys()]
        output = str(output)[:-1] + '\n'
        for k in d.keys():
            if isinstance(d[k], float):
                val = np.round(d[k], 2)
            else:
                val = d[k]
                output += f'{val}\t'
        output = output[:-1]
        self.exec_logger.debug(output)

        return d


    def rs_check(self):
        """ Check contact resistance.
        """
        # create custom sequence where MN == AB
        # we only check the electrodes which are in the sequence (not all might be connected)
        elec = np.sort(np.unique(self.sequence.flatten())) # assumed order
        quads = np.vstack([
            elec[:-1],
            elec[1:],
            elec[:-1],
            elec[1:],
        ]).T
        
        # create filename to store RS
        export_path_rs = self.pardict['export_path'].replace('.csv', '') \
                      + '_' + datetime.now().strftime('%Y%m%dT%H%M%S') + '_rs.csv'

        # perform RS check
        self.run = True
        self.status = 'running'
        
        # make sure all mux are off to start with
        self.reset_mux()

        # measure all quad of the RS sequence
        for i in range(0, quads.shape[0]):
            quad = quads[i, :]  # quadrupole
            self.switch_mux_on(quad)  # put before raising the pins (otherwise conflict i2c)
            d = self.run_measurement(quad=quad, nb_stack=1, injection_duration=0.5, tx_volt=5, autogain=True)
            
            # NOTE (GB): I'd use the self.run_measurement() for all this middle part so we an make use of autogain and so ...
            # call the switch_mux function to switch to the right electrodes
            #self.switch_mux_on(quad)

            # run a measurement
            #current_measurement = self.run_measurement(quad, 1, 0.25)
            
            # switch mux off
            #self.switch_mux_off(quad)

            # save data and print in a text file
            #self.append_and_save(export_path_rs, current_measurement)
            
            # current injection
            # self.pin0 = self.mcp.get_pin(0)
            # self.pin0.direction = Direction.OUTPUT
            # self.pin1 = self.mcp.get_pin(1)
            # self.pin1.direction = Direction.OUTPUT
            # self.pin0.value = False
            # self.pin1.value = False

            # # call the switch_mux function to switch to the right electrodes
           
            # self.ads_current = ads.ADS1115(self.i2c, gain=2 / 3, data_rate=860, address=0x48)
            # # ADS1115 for voltage measurement (MN)
            # self.ads_voltage = ads.ADS1115(self.i2c, gain=2 / 3, data_rate=860, address=0x49)
            # self.pin1.value = True  # inject from pin1 to self.pin0
            # self.pin0.value = False
            # time.sleep(0.5)
            
            # # measure current and voltage
            # current = AnalogIn(self.ads_current, ads.P0).voltage / (50 * self.r_shunt)
            # voltage = -AnalogIn(self.ads_voltage, ads.P0, ADS.P2).voltage * 2.5
            # resistance = voltage / current
            current = d['R [ohm]']
            voltage = d['Vmn [mV]']
            current = d['I [mA]']
            print(str(quad) + '> I: {:>10.3f} mA, V: {:>10.3f} mV, R: {:>10.3f} Ohm'.format(
                current, voltage, resistance))
            
            # compute resistance measured (= contact resistance)
            resist = abs(resistance / 1000)
            msg = 'Contact resistance {:s}: {:.3f} kOhm'.format(
                str(quad), resist)
            #print(msg)
            self.exec_logger.debug(msg)
            
            
            # if contact resistance = 0 -> we have a short circuit!!
            if resist < 1e-5:
                msg = '!!!SHORT CIRCUIT!!! {:s}: {:.3f} kOhm'.format(
                    str(quad), resist)
                self.exec_logger.warning(msg)
                print(msg)
                
            # save data and print in a text file
            self.append_and_save(export_path_rs, {
                'A': quad[0],
                'B': quad[1],
                'RS [kOhm]': resist,
            })
            
            # close mux path and put pin back to GND
            self.switch_mux_off(quad)
            #self.pin0.value = False
            #self.pin1.value = False
            
        self.reset_mux()
        self.status = 'idle'
        self.run = False

    #
    #         # TODO if interrupted, we would need to restore the values
    #         # TODO or we offer the possiblity in 'run_measurement' to have rs_check each time?

    @staticmethod
    def append_and_save(filename, last_measurement):
        """Append and save last measurement dataframe.

        Parameters
        ----------
        filename : str
            filename to save the last measurement dataframe
        last_measurement : dict
            Last measurement taken in the form of a python dictionary
        """

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
                # last_measurement.to_csv(f, header=True)

    def measure(self):
        """Run the sequence in a separate thread. Can be stopped by 'OhmPi.stop()'.
        """
        self.run = True
        self.status = 'running'
        self.exec_logger.debug(f'Status: {self.status}')

        def func():
            for g in range(0, self.pardict["nbr_meas"]):  # for time-lapse monitoring
                if self.run is False:
                    self.exec_logger.warning('Data acquisition interrupted')
                    break
                t0 = time.time()

                # create filename with timestamp
                filename = self.pardict["export_path"].replace('.csv',
                                                               f'_{datetime.now().strftime("%Y%m%dT%H%M%S")}.csv')
                self.exec_logger.debug(f'Saving to {filename}')

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
                        current_measurement = self.run_measurement(quad, self.pardict["nb_stack"],
                                                                   self.pardict["injection_duration"])
                    else:  # for testing, generate random data
                        current_measurement = {
                            'A': [quad[0]], 'B': [quad[1]], 'M': [quad[2]], 'N': [quad[3]],
                            'R [ohm]': np.abs(np.random.randn(1))
                        }

                    # switch mux off
                    self.switch_mux_off(quad)

                    # log data to the data logger
                    self.data_logger.info(f'{current_measurement}')
                    # save data and print in a text file
                    self.append_and_save(filename, current_measurement)
                    self.exec_logger.debug('{:d}/{:d}'.format(i + 1, self.sequence.shape[0]))

                # compute time needed to take measurement and subtract it from interval
                # between two sequence run (= sequence_delay)
                measuring_time = time.time() - t0
                sleep_time = self.pardict["sequence_delay"] - measuring_time

                if sleep_time < 0:
                    # it means that the measuring time took longer than the sequence delay
                    sleep_time = 0
                    self.exec_logger.warning('The measuring time is longer than the sequence delay. '
                                             'Increase the sequence delay')

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
        self.exec_logger.debug(f'Status: {self.status}')


VERSION = '2.1.0'

print(colored(r' ________________________________' + '\n' +
              r'|  _  | | | ||  \/  || ___ \_   _|' + '\n' +
              r'| | | | |_| || .  . || |_/ / | |' + '\n' +
              r'| | | |  _  || |\/| ||  __/  | |' + '\n' +
              r'\ \_/ / | | || |  | || |    _| |_' + '\n' +
              r' \___/\_| |_/\_|  |_/\_|    \___/ ', 'red'))
print('OhmPi start')
print('Version:', VERSION)
platform, on_pi = OhmPi.get_platform()
if on_pi:
    print(colored(f'Running on {platform} platform', 'green'))
    # TODO: check model for compatible platforms (exclude Raspberry Pi versions that are not supported...)
    #       and emit a warning otherwise
    if not arm64_imports:
        print(colored(f'Warning: Required packages are missing.\n'
                      f'Please run ./env.sh at command prompt to update your virtual environment\n', 'yellow'))
else:
    print(colored(f'Not running on the Raspberry Pi platform.\nFor simulation purposes only...', 'yellow'))

current_time = datetime.now()
print(current_time.strftime("%Y-%m-%d %H:%M:%S"))

# for testing
if __name__ == "__main__":
    ohmpi = OhmPi(config='ohmpi_param.json')
    ohmpi.run_measurement()
    #ohmpi.measure()
    #ohmpi.read_quad('breadboard.txt')
    #ohmpi.measure()
    #time.sleep(20)
    #ohmpi.stop()
