import RPi.GPIO as GPIO
import time , board, busio, numpy, os, sys, json, glob, statistics
from datetime import datetime
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import pandas as pd
import os.path
from gpiozero import CPUTemperature
i2c = busio.I2C(board.SCL, board.SDA) # I2C protocol setup
ads = ADS.ADS1115(i2c, gain=2/3,data_rate=860)
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(7, GPIO.OUT)
GPIO.setup(8, GPIO.OUT)
coef_p0 = 2.47 # slope for current conversion for ADS.P0, measurement in V/V
coef_p1 = 2.47# slope for current conversion for ADS.P1, measurement in V/V
coef_p2 = 2.4748 # slope for current conversion for ADS.P2, measurement in V/V
coef_p3 = 2.4748 # slope for current conversion for ADS.P3, measurement in V/V
integer=1000
meas=numpy.zeros((4,integer))
for i in range(0,100) :
    sum_I=0
    GPIO.output(8, GPIO.HIGH) # current injection
    time.sleep(4)
    for i in range(0,integer) :
     meas[0,i] = AnalogIn(ads,ADS.P0).voltage
    
    GPIO.output(8, GPIO.LOW)
    std=statistics.stdev(meas[0,:])
    mean=statistics.mean(meas[0,:])
    print(mean,std)
    #print(2.4653*mean+0.0073, std)
    time.sleep(4)
