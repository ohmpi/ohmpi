"""
created on January 6, 2020
Update april 2021
Ohmpi.py is a program to control a low-cost and open hardward resistivity meter OhmPi that has been developed by Rémi CLEMENT(INRAE),Vivien DUBOIS(INRAE),Hélène GUYARD(IGE), Nicolas FORQUET (INRAE), and Yannick FARGIER (IFSTTAR).
"""

print('\033[1m'+'\033[31m'+' ________________________________')
print('|  _  | | | ||  \/  || ___ \_   _|')
print('| | | | |_| || .  . || |_/ / | |' ) 
print('| | | |  _  || |\/| ||  __/  | |')  
print('\ \_/ / | | || |  | || |    _| |_') 
print(' \___/\_| |_/\_|  |_/\_|    \___/ ')
print('\033[0m')
print('OhmPi start' )
print('Vers: 1.51')
print('Import library')



import time , board, busio, numpy, os, sys, json, glob,os.path,adafruit_tca9548a
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from pandas import DataFrame
from datetime import datetime
from adafruit_mcp230xx.mcp23008 import MCP23008
from adafruit_mcp230xx.mcp23017 import MCP23017
import digitalio
from digitalio import Direction
from gpiozero import CPUTemperature
current_time = datetime.now()
print(current_time.strftime("%Y-%m-%d %H:%M:%S"))
"""
Hardware parameters
"""
R_shunt = 0.2# reference resistance value in ohm
Imax=4800/50/2
print(colored('The maximum current cannot be higher than 48 mA', 'red'))
coef_p2 = 2.50# slope for current conversion for ADS.P2, measurement in V/V
coef_p3 = 2.50 # slope for current conversion for ADS.P3, measurement in V/V
offset_p2= 0
offset_p3= 0
integer=10
meas=numpy.zeros((3,integer))

"""
Import parameters
"""

with open('ohmpi_param.json') as json_file:
    pardict = json.load(json_file)


i2c = busio.I2C(board.SCL, board.SDA) #activation du protocle I2C
mcp = MCP23008(i2c, address=0x20) #connexion I2C MCP23008, injection de courant
ads_current = ADS.ADS1115(i2c, gain=16,data_rate=860, address=0X48)# connexion ADS1115, pour la mesure de courant
ads_voltage = ADS.ADS1115(i2c, gain=2/3,data_rate=860, address=0X49)# connexion ADS1115, pour la mesure de courant
#initialisation desvoie pour la polarité
pin0 = mcp.get_pin(0)
pin0.direction = Direction.OUTPUT
pin1 = mcp.get_pin(1)
pin1.direction = Direction.OUTPUT
pin0.value = False
pin1.value = False


# Initialisation MUX
Elec_A= adafruit_tca9548a.TCA9548A(i2c, 0X76)
Elec_B= adafruit_tca9548a.TCA9548A(i2c, 0X71)
Elec_M= adafruit_tca9548a.TCA9548A(i2c, 0X74)
Elec_N= adafruit_tca9548a.TCA9548A(i2c, 0X70)
    


"""
functions
"""
# function swtich_mux select the right channels for the multiplexer cascade for electrodes A, B, M and N.
def switch_mux_on(quadripole):
    elec_adress=[0x76,0X71,0x74,0x70]
      
    for i in range(0,4):
        tca= adafruit_tca9548a.TCA9548A(i2c, elec_adress[i]) #choose MUX A B M or N
        
        if quadripole[i] < 17:
            nb_i2C=7
            a=quadripole[i]
        elif quadripole[i] > 16 and quadripole[i] < 33:    
            nb_i2C=6
            a=quadripole[i]-16
        elif quadripole[i] > 32 and quadripole[i] < 49:    
            nb_i2C=5
            a=quadripole[i]-32
        elif quadripole[i] > 48 and quadripole[i] < 65:    
            nb_i2C=4
            a=quadripole[i]-48
              
        mcp2 = MCP23017(tca[nb_i2C])     
        mcp2.get_pin(a-1).direction=digitalio.Direction.OUTPUT
        mcp2.get_pin(a-1).value=True
 
def switch_mux_off(quadripole):
    elec_adress=[0x76,0X71,0x74,0x70]
      
    for i in range(0,4):
        tca= adafruit_tca9548a.TCA9548A(i2c, elec_adress[i]) #choose MUX A B M or N
        
        if quadripole[i] < 17:
            nb_i2C=7
            a=quadripole[i]
        elif quadripole[i] > 16 and quadripole[i] < 33:    
            nb_i2C=6
            a=quadripole[i]-16
        elif quadripole[i] > 32 and quadripole[i] < 49:    
            nb_i2C=5
            a=quadripole[i]-32
        elif quadripole[i] > 48 and quadripole[i] < 65:    
            nb_i2C=4
            a=quadripole[i]-48
              
        mcp2 = MCP23017(tca[nb_i2C])     
        mcp2.get_pin(a-1).direction=digitalio.Direction.OUTPUT
        mcp2.get_pin(a-1).value=False
       

#function to switch  off mux
def ZERO_mux(nb_elec):
    elec_adress=[0x76,0X71,0x74,0x70]
    for i in range(0,4):
        tca= adafruit_tca9548a.TCA9548A(i2c, elec_adress[i]) #choose MUX A B M or N
        for y in range(0,nb_elec):
            qd=y+1
            if qd < 17:
                nb_i2C=7
                a=qd
            elif qd > 16 and qd < 33:    
                nb_i2C=6
                a=qd-16
            elif qd > 32 and qd < 49:    
                nb_i2C=5
                a=qd-32
            elif qd > 48 and qd < 65:    
                nb_i2C=4
                a=qd-48
                  
            mcp2 = MCP23017(tca[nb_i2C])     
            mcp2.get_pin(a-1).direction=digitalio.Direction.OUTPUT
            mcp2.get_pin(a-1).value= False

# function to find rows with identical values in different columns
def find_identical_in_line(array_object):
    output = []
    if array_object.ndim == 1:
        temp = numpy.zeros(4)
        for i in range(len(array_object)):
            temp[i] = numpy.count_nonzero(array_object == array_object[i])
        if any(temp > 1):
            output.append(0)
    else:
        for i in range(len(array_object[:,1])):
            temp = numpy.zeros(len(array_object[1,:]))
            for j in range(len(array_object[1,:])):
                temp[j] = numpy.count_nonzero(array_object[i,:] == array_object[i,j])
            if any(temp > 1):
                output.append(i)
    return output
# 
# read quadripole file and apply tests
def read_quad(filename, nb_elec):
    output = numpy.loadtxt(filename, delimiter=" ",dtype=int) # load quadripole file
    # locate lines where the electrode index exceeds the maximum number of electrodes
    test_index_elec = numpy.array(numpy.where(output > nb_elec))
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

def run_measurement(nb_stack, injection_deltat, R_shunt, coefp2, coefp3, elec_array):
    start_time=time.time()
    # inner variable initialization
    sum_I=0
    sum_Vmn=0
    sum_Ps=0
    # injection courant and measure
    mcp = MCP23008(i2c, address=0x20)
    pin0 = mcp.get_pin(0)
    pin0.direction = Direction.OUTPUT
    pin1 = mcp.get_pin(1)
    pin1.direction = Direction.OUTPUT
    pin0.value = False
    pin1.value = False
    for n in range(0,3+2*nb_stack-1) :        
        # current injection
        
        if (n % 2) == 0:
            
            pin1.value = True
            pin0.value = False # current injection polarity n°1        
        else:
            pin0.value = True
            pin1.value = False# injection de courant polarity n°2
        start_delay=time.time()
        time.sleep(injection_deltat) # delay depending on current injection duration

       
        for k in range(0,integer):
          meas[0,k] = ((AnalogIn(ads_current,ADS.P0).voltage/50)/R_shunt)*1000 # reading current value on ADS channel A0
          meas[1,k] = AnalogIn(ads_voltage,ADS.P0).voltage * coefp2*1000
          meas[2,k] = AnalogIn(ads_voltage,ADS.P1).voltage * coefp3*1000 # reading voltage value on ADS channel A2
        pin1.value = False; pin0.value = False# stop current injection
        end_delay=time.time()
        sum_I=sum_I+(numpy.mean(meas[0,:]))
        Vmn1=((numpy.mean(meas[1,:]))-(numpy.mean(meas[2,:])))
        if (n % 2) == 0:
              sum_Vmn=sum_Vmn-Vmn1
              sum_Ps=sum_Ps+Vmn1
        else:
              sum_Vmn=sum_Vmn+Vmn1
              sum_Ps=sum_Ps+Vmn1
        end_calc=time.time()
        cpu = CPUTemperature()
        time.sleep((end_delay-start_delay)-(end_calc-end_delay)) 
    # return averaged values
#     cpu= CPUTemperature()
    output = DataFrame({
        "time":[datetime.now()],
        "A":elec_array[0],
        "B":elec_array[1],
        "M":elec_array[2],
        "N":elec_array[3],
        "Vmn [mV]":[(sum_Vmn/(3+2*nb_stack-1))],
        "I [mA]":[(sum_I/(3+2*nb_stack-1))],
        "R [ohm]":[( (sum_Vmn/(3+2*nb_stack-1)/(sum_I/(3+2*nb_stack-1))))],
#         "Rab [KOhm]":[(Tab*2.47)/(sum_I/(3+2*nb_stack-1))/1000],
#         "Tx [V]":[Tx*2.47],              
        "Ps [mV]":[(sum_Ps/(3+2*nb_stack-1))],
        "nbStack":[nb_stack],
        "CPU temp [°C]":[cpu.temperature],
#         "Hardware temp [°C]":[read_temp()-8],
        "Time [S]":[(-start_time+time.time())]
#         "Rcontact[ohm]":[Rc],
#         "Rsoil[ohm]":[Rsoil],
#         "Rab_theory [Ohm]":[(Rc*2+Rsoil)]
     
     
      # Dead time equivalent to the duration of the current injection pulse   
    })
    output=output.round(2)
    print(output.to_string())
    time.sleep(1)
    return output

# save data
def append_and_save(path, last_measurement):
    
    if os.path.isfile(path):
        # Load data file and append data to it
        with open(path, 'a') as f:
             last_measurement.to_csv(f, header=False)
    else:
        # create data file and add headers
        with open(path, 'a') as f:
             last_measurement.to_csv(f, header=True)


"""
Main loop
"""
N=read_quad("dd.txt",pardict.get("nb_electrodes")) # load quadripole file

if N.ndim == 1:
    N = N.reshape(1, 4)
ZERO_mux(pardict.get("nb_electrodes"))
for g in range(0,pardict.get("nbr_meas")): # for time-lapse monitoring

    for i in range(0,N.shape[0]): # loop over quadripoles
        # call the switch_mux function to switch to the right electrodes

        
        switch_mux_on(N[i,])
        # run a measurement
        current_measurement = run_measurement(pardict.get("stack"), pardict.get("injection_duration"), R_shunt, coef_p2, coef_p3, N[i,])
        switch_mux_off(N[i,])
        #save data and print in a text file
        append_and_save(pardict.get("export_path"), current_measurement)
        print(i+1,'/',N.shape[0])
    print('end of sequence')
    ZERO_mux(pardict.get("nb_electrodes"))
    time.sleep(pardict.get("sequence_delay")) #waiting next measurement (time-lapse)
