"""
created on december, 2021
Update january 2022
Ohmpi_4elec.py is a program to control a low-cost and open hardware resistivity meter OhmPi that has been developed
 by Rémi CLEMENT(INRAE),Vivien DUBOIS(INRAE),Hélène GUYARD(IGE), Nicolas FORQUET (INRAE),
    Oliver KAUFMANN (UMONS) and Yannick FARGIER (IFSTTAR).
"""
from settings import OHMPI_CONFIG
try:
    import board, busio
    import adafruit_tca9548a
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
    from adafruit_mcp230xx.mcp23008 import MCP23008
    from adafruit_mcp230xx.mcp23017 import MCP23017
    import digitalio
    from digitalio import Direction
    from gpiozero import CPUTemperature
except:
    pass

# from pandas import DataFrame
from datetime import datetime
import time
import numpy as np
import sys
import json
# import glob
from os import path, statvfs
from threading import Thread
from logging_setup import setup_loggers
from mqtt_setup import mqtt_client_setup

# Initialization
version = "1.01"

print('\033[1m'+'\033[31m'+' ________________________________')
print('|  _  | | | ||  \/  || ___ \_   _|')
print('| | | | |_| || .  . || |_/ / | |' )
print('| | | |  _  || |\/| ||  __/  | |')
print('\ \_/ / | | || |  | || |    _| |_')
print(' \___/\_| |_/\_|  |_/\_|    \___/ ')
print('\033[0m')
print('OhmPi 4 elec MQTT start' )
print(f'Vers: {version}')

msg_logger, msg_log_filename, data_logger, data_log_filename, logging_level = setup_loggers()
mqtt_client, measurement_topic = mqtt_client_setup()

msg_logger.info(f'publishing mqtt to topic {measurement_topic}')

# Remaining initialization
status = True

"""
hardware parameters
"""
print(f'\033[1m \033[31m The maximum current cannot be higher than {OHMPI_CONFIG["Imax"]} mA \033[0m')
# offset_p2= 0
# offset_p3= 0
integer = 2  # Max value 10 TODO: explain this
nb_elec = 4  # TODO: Improve this
meas = np.zeros((3, integer))

"""
import parameters
"""

with open('ohmpi_param.json') as json_file:
    pardict = json.load(json_file)


i2c = busio.I2C(board.SCL, board.SDA) #activation du protocle I2C
mcp = MCP23008(i2c, address=0x20) #connexion I2C MCP23008, injection de courant
ads_current = ADS.ADS1115(i2c, gain=2/3,data_rate=860, address=0X48)# connexion ADS1115, pour la mesure de courant
ads_voltage = ADS.ADS1115(i2c, gain=2/3,data_rate=860, address=0X49)# connexion ADS1115, pour la mesure de voltage

#initialisation des voies pour la polarité
pin0 = mcp.get_pin(0)
pin0.direction = Direction.OUTPUT
pin1 = mcp.get_pin(1)
pin1.direction = Direction.OUTPUT
pin0.value = False
pin1.value = False


def switch_mux(electrode_nr, state, role):
    """select the right channel for the multiplexer cascade for a given electrode"""
    board_address = {'A': 0x76, 'B': 0X71, 'M': 0x74, 'N': 0x70}

    tca = adafruit_tca9548a.TCA9548A(i2c, board_address[role])  # choose MUX A B M or N
    i2c_address = None
    if electrode_nr < 17:
        i2c_address = 7
        relay_nr = electrode_nr
    elif 16 < electrode_nr < 33:
        i2c_address = 6
        relay_nr = electrode_nr - 16
    elif 32 < electrode_nr < 49:
        i2c_address = 5
        relay_nr = electrode_nr - 32
    elif 48 < electrode_nr < 65:
        i2c_address = 4
        relay_nr = electrode_nr - 48

    if i2c_address is not None:
        mcp2 = MCP23017(tca[i2c_address])
        mcp2.get_pin(relay_nr-1).direction=digitalio.Direction.OUTPUT
        if state == 'on':
            mcp2.get_pin(relay_nr-1).value = True
        else:
            mcp2.get_pin(relay_nr-1).value = False
        msg_logger.debug(f'Switching relay {relay_nr} {state} for electrode {electrode_nr}')
    else:
        msg_logger.warn(f'Unable to address electrode nr {electrode_nr}')


def switch_mux_on(quadrupole):
    """switch on multiplexer relays for quadrupole"""
    roles = ['A', 'B', 'M', 'N']
    for i in range(0, 4):
        switch_mux(quadrupole[i], 'on', roles[i])


def switch_mux_off(quadrupole):
    """switch off multiplexer relays for quadrupole"""
    roles = ['A', 'B', 'M', 'N']
    for i in range(0, 4):
        switch_mux(quadrupole[i], 'off', roles[i])


def reset_mux():
    """switch off all multiplexer relays"""
    global nb_elec
    roles = ['A', 'B', 'M', 'N']
    for i in range(0, 4):
        for j in range(1, nb_elec + 1):
            switch_mux(j, 'off', roles[i])

# function to find rows with identical values in different columns
def find_identical_in_line(array_object):
    output = []
    if array_object.ndim == 1:
        temp = np.zeros(4)
        for i in range(len(array_object)):
            temp[i] = np.count_nonzero(array_object == array_object[i])
        if any(temp > 1):
            output.append(0)
    else:
        for i in range(len(array_object[:,1])):
            temp = np.zeros(len(array_object[1,:]))
            for j in range(len(array_object[1,:])):
                temp[j] = np.count_nonzero(array_object[i,:] == array_object[i,j])
            if any(temp > 1):
                output.append(i)
    return output


def read_quad(filename, nb_elec):
    """read quadripole file and apply tests"""
    output = np.loadtxt(filename, delimiter=" ",dtype=int) # load quadripole file
    # locate lines where the electrode index exceeds the maximum number of electrodes
    test_index_elec = np.array(np.where(output > nb_elec))
    # locate lines where an electrode is referred twice
    test_same_elec = find_identical_in_line(output)
    # if statement with exit cases (rajouter un else if pour le deuxième cas du ticket #2)
    if test_index_elec.size != 0:
        for i in range(len(test_index_elec[0,:])):
            print("Error: An electrode index at line "+ str(test_index_elec[0,i]+1)+" exceeds the maximum number of electrodes")
        sys.exit(1)
    elif len(test_same_elec) != 0:
        for i in range(len(test_same_elec)):
            print("Error: An electrode index is used twice at line " + str(test_same_elec[i]+1))
        sys.exit(1)
    else:
        return output


def run_measurement(nb_stack, injection_deltat, r_shunt, coefp2, coefp3):
    start_time=time.time()
    # inner variable initialization
    injection_current=0
    sum_vmn=0
    sum_ps=0
    # injection courant and measure
    mcp = MCP23008(i2c, address=0x20)
    pin0 = mcp.get_pin(0)
    pin0.direction = Direction.OUTPUT
    pin1 = mcp.get_pin(1)
    pin1.direction = Direction.OUTPUT
    pin0.value = False
    pin1.value = False
    for n in range(0, 3+2*nb_stack-1):
        # current injection
        if (n % 2) == 0:
            pin1.value = True
            pin0.value = False # current injection polarity nr1
        else:
            pin0.value = True
            pin1.value = False  # current injection nr2
        start_delay=time.time()   # stating measurement time
        time.sleep(injection_deltat)  # delay depending on current injection duration
        
    # mesureament of i and u
        for k in range(0, integer):
          meas[0,k] = (AnalogIn(ads_current,ADS.P0).voltage*1000)/(50*r_shunt) # reading current value on ADS channel A0
          meas[1,k] = AnalogIn(ads_voltage,ADS.P0).voltage*coefp2*1000
          meas[2,k] = AnalogIn(ads_voltage,ADS.P1).voltage*coefp3*1000  # reading voltage value on ADS channel A2
        # stop current injection
        pin1.value = False
        pin0.value = False
        end_delay = time.time()
        injection_current = injection_current + (np.mean(meas[0, :]))
        vmn1 = ((np.mean(meas[1, :]))-(np.mean(meas[2, :])))
        if (n % 2) == 0:
            sum_vmn = sum_vmn - vmn1
            sum_ps = sum_ps + vmn1
        else:
            sum_vmn = sum_vmn + vmn1
            sum_ps = sum_ps + vmn1
        
        cpu = CPUTemperature()
        
        end_calc = time.time()
        time.sleep(2*(end_delay-start_delay)-(end_calc-start_delay))
        #end_sleep2=time.time()
        #print(['sleep=',((end_sleep2-start_delay))])

        #print(['true delta=',((end_delay-start_delay)-injection_deltat)])
        #print(['time stop=',((2*(end_delay-start_delay)-(end_calc-start_delay)))])
    # return averaged values
#     cpu= CPUTemperature()
    output = {
        "time": datetime.now(),
        "A": (1),
        "B": (2),
        "M": (3),
        "N": (4),
        "inj time [ms]": (end_delay - start_delay) * 1000,
        "Vmn [mV]": (sum_vmn / (3 + 2 * nb_stack - 1)),
        "I [mA]": (injection_current / (3 + 2 * nb_stack - 1)),
        "R [ohm]": (sum_vmn / (3 + 2 * nb_stack - 1) / (injection_current / (3 + 2 * nb_stack - 1))),
        "Ps [mV]": (sum_ps / (3 + 2 * nb_stack - 1)),
        "nbStack": nb_stack,
        "CPU temp [°C]": cpu.temperature,
        "Time [s]": (-start_time + time.time()),
        "Integer [-]": integer}
    # output = output.round(2)
    print(output) # .to_string())
    time.sleep(1)
    return output


def append_and_save(data_path, last_measurement):
    """Save data"""
    if path.isfile(data_path):
        # Load data file and append data to it
        # with open(data_path, 'a') as f:
        #    last_measurement.to_csv(f, header=False)
        pass
    else:
        # create data file and add headers
        # with open(data_path, 'a') as f:
        #    last_measurement.to_csv(f, header=True)
        pass

"""
Main loop
"""
for g in range(0, pardict.get("nbr_meas")):  # for time-lapse monitoring
    current_measurement = run_measurement(pardict.get("stack"), pardict.get("injection_duration"), 
                                          OHMPI_CONFIG['R_shunt'], OHMPI_CONFIG['coef_p2'], OHMPI_CONFIG['coef_p3'])
    append_and_save(pardict.get("export_path"), current_measurement)
    msg = f'Resitivity: {current_measurement["R [ohm]"]:.2f} ohm'
    msg_logger.info(msg)
    mqtt_client.publish(measurement_topic, msg)
    time.sleep(pardict.get("sequence_delay"))  # waiting next measurement (time-lapse)
