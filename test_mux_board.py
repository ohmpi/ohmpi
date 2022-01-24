"""
Created on Tue Dec  7 06:39:33 2021 
Code for testing switch MUX for ohmpi 2 
@author: remi.clement 
"""

import time , board, busio,adafruit_tca9548a 
from adafruit_mcp230xx.mcp23017 import MCP23017 
import digitalio
from digitalio import Direction


address=0X70# choose the mux board address 

activation_time=1 # choose your activation time in second 


i2c = busio.I2C(board.SCL, board.SDA) #activation du protocle I2C 
def switch_mux_on(electrode,address):
    tca= adafruit_tca9548a.TCA9548A(i2c, address)
    if electrode < 17: 
        nb_i2C=7 
        a=electrode 
    elif electrode > 16 and electrode< 33:     
        nb_i2C=6 
        a=electrode-16 
    elif electrode > 32 and electrode < 49:     
        nb_i2C=5 
        a=electrode-32 
    elif electrode > 48 and electrode < 65:     
        nb_i2C=4 
        a=electrode-48 
               
    mcp2 = MCP23017(tca[nb_i2C]) 
    mcp2.get_pin(a-1).direction=Direction.OUTPUT 
    mcp2.get_pin(a-1).value=True 
  
def switch_mux_off(electrode,address): 
    tca= adafruit_tca9548a.TCA9548A(i2c, address) 
    if electrode < 17: 
        nb_i2C=7 
        a=electrode 
    elif electrode > 16 and electrode < 33:     
        nb_i2C=6 
        a=electrode-16 
    elif electrode > 32 and electrode < 49:     
        nb_i2C=5
        
        a=electrode-32 
    elif electrode > 48 and electrode < 65:     
        nb_i2C=4 
        a=electrode-48 
           
    mcp2 = MCP23017(tca[nb_i2C])      
    mcp2.get_pin(a-1).direction=digitalio.Direction.OUTPUT 
    mcp2.get_pin(a-1).value=False 
 
a=input(' if vous want try 1 channel choose 1, if you want try all channel choose 2!') 
 
if a=='1': 
    b=0 
    print ("run channel by channel test") 
    electrode=int(input(' Choose your electrode number (integer):')) 
    switch_mux_on(electrode,address) 
    print('electrode:',electrode,' activate' ) 
    time.sleep(activation_time) 
    switch_mux_off(electrode,address) 
    print('electrode:',electrode,' deactivate' ) 
     
if a== '2': 
    for electrode in range(1, 65): 
        switch_mux_on(electrode,address) 
        print('electrode:',electrode,' activate' ) 
        time.sleep(activation_time) 
        switch_mux_off(electrode,address) 
        print('electrode:',electrode,' deactivate' ) 

        time.sleep(activation_time) 

if a not in ['1', '2']: 
    print ("Wrong choice !") 
