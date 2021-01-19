import RPi.GPIO as GPIO
import time , board, busio, numpy, os, sys, json, glob, statistics
from datetime import datetime
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import pandas as pd
import os.path
from gpiozero import CPUTemperature

i2c = busio.I2C(board.SCL, board.SDA) # I2C protocol setup


def gain_auto(channel):
    gain=2/3
    if ((abs(channel.voltage)<2.040) and (abs(channel.voltage)>=1.023)):
        gain=2
    elif ((abs(channel.voltage)<1.023) and (abs(channel.voltage)>=0.508)):
        gain=4
    elif ((abs(channel.voltage)<0.508) and (abs(channel.voltage)>=0.250)):
        gain=8
    elif abs(channel.voltage)<0.256:
        gain=16
    #print(gain)
    return gain 

ads = ADS.ADS1115(i2c, gain=2/3,data_rate=860) # I2C communication setup
t_gain=[gain_auto(AnalogIn(ads,ADS.P3))]
ads = ADS.ADS1115(i2c, gain=t_gain[0],data_rate=860)
print(t_gain)
print(AnalogIn(ads,ADS.P3).voltage)
print(AnalogIn(ads,ADS.P2).voltage)
