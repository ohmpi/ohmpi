"""
23/08/2019
OHMPY_code is a program to control the low-cost and open source resistivity meter
OHMPY, it has been developed by Rémi CLEMENT, Nicolas FORQUET (IRSTEA) and Yannick FARGIER (IFSTTAR).
Version 1.00 23/08/2019 modified by Remi CLEMENT
multiplexer development for electrode selection for each quadripole
from the quadripole file ABMN.txt
"""

#!/usr/bin/python
import RPi.GPIO as GPIO
import time
import board
import busio
import numpy
import os
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
print('Import library')

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
 
#i2c = busio.I2C(board.SCL, board.SDA)
# Create the ADC object using the I2C bus
#ads = ADS.ADS1115(i2c)
#chan = AnalogIn(ads, ADS.P0)
"""
Initialization of multiplexer channels
"""
pinList = [12,16,20,21,26,18,23,24,25,19] # List of GPIOs enabled for relay cards (electrodes)
for i in pinList: 
    GPIO.setup(i, GPIO.OUT) 
    GPIO.output(i, GPIO.HIGH)
"""
Measurement settings
"""
injection_time = 1 # Current injection time in second
nbr_meas= 900 # Number of times the quadrupole sequence is repeated
sequence_delay= 30 # Delay in Second between 2 sequences
stack= 1 # repetition of the current injection for each quadrupole

"""
Reading the quadrupole file
"""
N=numpy.loadtxt("ABMN3.txt", delimiter=" ",dtype=int) # load quadripole file
M=open("ABMN3.txt",'r') # open quadripole file
listM=list(M) # Transform M as a list
M.close() # Close M

for g in range(0,nbr_mesure): # for time-lapse monitoring
  
    """
    Selection electrode activées pour chaque quadripole
    """
    for i in range(0,len(listM)): # boucle sur les quadripôles, qui tient compte du nombre de quadripole dans le fichier ABMN

        for j in range(0,3):
                if j=0: # electrode A
                    n1=12; n2=16; n3=20; n4=21; n5=26
                elif j=1: # electrode B
                    n1=18; n2=23; n3=24; n4=25; n5=19 # à modifier
                elif j=2: # electrode M
                    n1=2; n2=3; n3=4; n4=17; n5=27 # à modifier
                elif j=3: # electrode N
                    n1=22; n2=10; n3=9; n4=11; n5=5 # à modifier


                if N[i][j]==1:
                 GPIO.output(n1, GPIO.HIGH);GPIO.output(n2, GPIO.HIGH);GPIO.output(n3, GPIO.HIGH); GPIO.output(n4, GPIO.LOW); GPIO.output(n5, GPIO.LOW);   
                elif N[i][j]==2:            
                GPIO.output(n1, GPIO.HIGH);GPIO.output(n2, GPIO.HIGH);GPIO.output(n3, GPIO.HIGH); GPIO.output(n4, GPIO.LOW); GPIO.output(n5, GPIO.HIGH);       
                elif N[i][j]==3:            
                GPIO.output(n1, GPIO.HIGH);GPIO.output(n2, GPIO.HIGH);GPIO.output(n3, GPIO.HIGH); GPIO.output(n4, GPIO.HIGH);GPIO.output(n5, GPIO.LOW);    
                elif N[i][j]==4:
                GPIO.output(n1, GPIO.HIGH);GPIO.output(n2, GPIO.HIGH);GPIO.output(n3, GPIO.HIGH); GPIO.output(n4, GPIO.HIGH);GPIO.output(n5, GPIO.HIGH);    
                elif N[i][j]==5:
                GPIO.output(n1, GPIO.HIGH);GPIO.output(n2, GPIO.HIGH);GPIO.output(n3, GPIO.LOW); GPIO.output(n4, GPIO.LOW);GPIO.output(n5, GPIO.LOW);    
                elif N[i][j]==6:
                GPIO.output(n1, GPIO.HIGH);GPIO.output(n2, GPIO.HIGH);GPIO.output(n3, GPIO.LOW); GPIO.output(n4, GPIO.LOW);GPIO.output(n5, GPIO.HIGH);
                elif N[i][j]==7:
                GPIO.output(n1, GPIO.HIGH);GPIO.output(n2, GPIO.HIGH);GPIO.output(n3, GPIO.LOW); GPIO.output(n4, GPIO.HIGH);GPIO.output(n5, GPIO.LOW);
                elif N[i][j]==8:
                GPIO.output(n1, GPIO.HIGH);GPIO.output(n2, GPIO.HIGH);GPIO.output(n3, GPIO.LOW); GPIO.output(n4, GPIO.HIGH);GPIO.output(n5, GPIO.HIGH);    
                elif N[i][j]==9:
                GPIO.output(n1, GPIO.HIGH);GPIO.output(n2, GPIO.LOW);GPIO.output(n3, GPIO.HIGH); GPIO.output(n4, GPIO.LOW);GPIO.output(n5, GPIO.LOW);    
                elif N[i][j]==10:
                GPIO.output(n1, GPIO.HIGH);GPIO.output(n2, GPIO.LOW);GPIO.output(n3, GPIO.HIGH); GPIO.output(n4, GPIO.LOW);GPIO.output(n5, GPIO.HIGH);    
                elif N[i][j]==11:
                GPIO.output(n1, GPIO.HIGH);GPIO.output(n2, GPIO.LOW);GPIO.output(n3, GPIO.HIGH); GPIO.output(n4, GPIO.HIGH);GPIO.output(n5, GPIO.LOW);    
                elif N[i][j]==12:
                GPIO.output(n1, GPIO.HIGH);GPIO.output(n2, GPIO.LOW);GPIO.output(n3, GPIO.HIGH); GPIO.output(n4, GPIO.HIGH);GPIO.output(n5, GPIO.HIGH);    
                elif N[i][j]==13:
                GPIO.output(n1, GPIO.HIGH);GPIO.output(n2, GPIO.LOW);GPIO.output(n3, GPIO.LOW); GPIO.output(n4, GPIO.LOW);GPIO.output(n5, GPIO.LOW);   
                elif N[i][j]==14:
                GPIO.output(n1, GPIO.HIGH);GPIO.output(n2, GPIO.LOW);GPIO.output(n3, GPIO.LOW); GPIO.output(n4, GPIO.LOW);GPIO.output(n5, GPIO.HIGH);    
                elif N[i][j]==15:
                GPIO.output(n1, GPIO.HIGH);GPIO.output(n2, GPIO.LOW);GPIO.output(n3, GPIO.LOW); GPIO.output(n4, GPIO.HIGH);GPIO.output(n5, GPIO.LOW);    
                elif N[i][j]==16:
                GPIO.output(n1, GPIO.HIGH);GPIO.output(n2, GPIO.LOW);GPIO.output(n3, GPIO.LOW); GPIO.output(n4, GPIO.HIGH);GPIO.output(n5, GPIO.HIGH);    
                elif N[i][j]==17:
                GPIO.output(n1, GPIO.LOW);GPIO.output(n2, GPIO.HIGH);GPIO.output(n3, GPIO.HIGH); GPIO.output(n4, GPIO.LOW); GPIO.output(n5, GPIO.HIGH);    
                elif N[i][j]==18:
                GPIO.output(n1, GPIO.LOW);GPIO.output(n2, GPIO.HIGH);GPIO.output(n3, GPIO.HIGH); GPIO.output(n4, GPIO.LOW); GPIO.output(n5, GPIO.LOW);    
                elif N[i][j]==19:
                GPIO.output(n1, GPIO.LOW);GPIO.output(n2, GPIO.HIGH);GPIO.output(n3, GPIO.HIGH); GPIO.output(n4, GPIO.HIGH);GPIO.output(n5, GPIO.HIGH);    
                elif N[i][j]==20:
                GPIO.output(n1, GPIO.LOW);GPIO.output(n2, GPIO.HIGH);GPIO.output(n3, GPIO.HIGH); GPIO.output(n4, GPIO.HIGH);GPIO.output(n5, GPIO.LOW);    
                elif N[i][j]==21:
                GPIO.output(n1, GPIO.LOW);GPIO.output(n2, GPIO.HIGH);GPIO.output(n3, GPIO.LOW); GPIO.output(n4, GPIO.LOW);GPIO.output(n5, GPIO.HIGH);    
                elif N[i][j]==22:
                GPIO.output(n1, GPIO.LOW);GPIO.output(n2, GPIO.HIGH);GPIO.output(n3, GPIO.LOW); GPIO.output(n4, GPIO.LOW);GPIO.output(n5, GPIO.LOW);    
                elif N[i][j]==23:
                GPIO.output(n1, GPIO.LOW);GPIO.output(n2, GPIO.HIGH);GPIO.output(n3, GPIO.LOW); GPIO.output(n4, GPIO.HIGH);GPIO.output(n5, GPIO.HIGH);    
                elif N[i][j]==24:
                GPIO.output(n1, GPIO.LOW);GPIO.output(n2, GPIO.HIGH);GPIO.output(n3, GPIO.LOW); GPIO.output(n4, GPIO.HIGH);GPIO.output(n5, GPIO.LOW);    
                elif N[i][j]==25:
                GPIO.output(n1, GPIO.LOW);GPIO.output(n2, GPIO.LOW);GPIO.output(n3, GPIO.HIGH); GPIO.output(n4, GPIO.LOW);GPIO.output(n5, GPIO.HIGH);    
                elif N[i][j]==26:
                GPIO.output(n1, GPIO.LOW);GPIO.output(n2, GPIO.LOW);GPIO.output(n3, GPIO.HIGH); GPIO.output(n4, GPIO.LOW);GPIO.output(n5, GPIO.LOW);    
                elif N[i][j]==27:
                GPIO.output(n1, GPIO.LOW);GPIO.output(n2, GPIO.LOW);GPIO.output(n3, GPIO.HIGH); GPIO.output(n4, GPIO.HIGH);GPIO.output(n5, GPIO.HIGH);    
                elif N[i][j]==28:
                GPIO.output(n1, GPIO.LOW);GPIO.output(n2, GPIO.LOW);GPIO.output(n3, GPIO.HIGH); GPIO.output(n4, GPIO.HIGH);GPIO.output(n5, GPIO.LOW);    
                elif N[i][j]==29:
                GPIO.output(n1, GPIO.LOW);GPIO.output(n2, GPIO.LOW);GPIO.output(n3, GPIO.LOW); GPIO.output(n4, GPIO.LOW);GPIO.output(n5, GPIO.HIGH);    
                elif N[i][j]==30:
                GPIO.output(n1, GPIO.LOW);GPIO.output(n2, GPIO.LOW);GPIO.output(n3, GPIO.LOW); GPIO.output(n4, GPIO.LOW);GPIO.output(n5, GPIO.LOW);   
                elif N[i][j]==31:
                GPIO.output(n1, GPIO.LOW);GPIO.output(n2, GPIO.LOW);GPIO.output(n3, GPIO.LOW); GPIO.output(n4, GPIO.HIGH);GPIO.output(n5, GPIO.HIGH);    
                elif N[i][j]==32:
                GPIO.output(n1, GPIO.LOW);GPIO.output(n2, GPIO.LOW);GPIO.output(n3, GPIO.LOW); GPIO.output(n4, GPIO.HIGH);GPIO.output(n5, GPIO.LOW);    
        
        time.sleep(injection_time);  
        n1=22; n2=10; n3=9; n4=11; n5=5 # à modifier
        GPIO.output(12, GPIO.HIGH); GPIO.output(16, GPIO.HIGH); GPIO.output(20, GPIO.HIGH); GPIO.output(21, GPIO.HIGH); GPIO.output(26, GPIO.HIGH)              
        GPIO.output(18, GPIO.HIGH); GPIO.output(23, GPIO.HIGH); GPIO.output(24, GPIO.HIGH); GPIO.output(25, GPIO.HIGH); GPIO.output(19, GPIO.HIGH) 
        GPIO.output(2, GPIO.HIGH); GPIO.output(3, GPIO.HIGH); GPIO.output(4, GPIO.HIGH); GPIO.output(17, GPIO.HIGH); GPIO.output(27, GPIO.HIGH)
        GPIO.output(22, GPIO.HIGH); GPIO.output(10, GPIO.HIGH); GPIO.output(9, GPIO.HIGH); GPIO.output(11, GPIO.HIGH); GPIO.output(5, GPIO.HIGH)
    
    time.sleep(sequence_delay);

'''
Showing results
'''


'''
Save result in txt file
'''

    GPIO.output(12, GPIO.HIGH)
    GPIO.output(16, GPIO.HIGH)
    GPIO.output(20, GPIO.HIGH)
    GPIO.output(21, GPIO.HIGH)
    GPIO.output(26, GPIO.HIGH)


    





