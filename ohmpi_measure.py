import RPi.GPIO as GPIO
import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in  import AnalogIn
# paramètres de mesure
nbr_stack=2 # défini le nombre de stack (1 stack une injection positive et negative
current_injection_time=0.5 # temps d'injection du courant en seconde
# paramètres liées à la carte de mesure
Rref=50 # valeur de la resistance de référence
som_I=0
som_Vmn=0
i2c = busio.I2C(board.SCL, board.SDA) # definition du protocole I2C
ads = ADS.ADS1115(i2c, gain=2/3) # activation de la connection I2C
#initialisation des gpio
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(7, GPIO.OUT)
GPIO.setup(8, GPIO.OUT)
# mesure de la resistance
for n in range(0,3+2*nbr_stack-1) :
    print(n+1)
    if (n % 2) == 0:
        GPIO.output(7, GPIO.HIGH) # polarité n°1
        print('positif')
    else:
        GPIO.output(7, GPIO.HIGH) # polarité n°1
        print('negatif')
    GPIO.output(8, GPIO.HIGH) # injection du courant
    time.sleep(current_injection_time) # delay fonction du temps d'injection
    Ia1 = AnalogIn(ads,ADS.P0).voltage # lecture de la voie A0
    Ib1 = AnalogIn(ads,ADS.P1).voltage # lecture de la voie A1
    Vm1 = AnalogIn(ads,ADS.P2).voltage # lecture de la voie A2
    Vn1 = AnalogIn(ads,ADS.P3).voltage # lecture de la voie A3
    GPIO.output(8, GPIO.LOW)# stop injection du courant
    I1= (Ia1 - Ib1)/Rref;
    som_I=som_I+I1;
    Vmn1= (Vm1 - Vn1);
    som_Vmn=som_Vmn-Vmn1;
    som_Ps=Vmn1;
#valeur à renvoyer
Vmn= som_Vmn/(3+2*nbr_stack-1)
I=som_I/(3+2*nbr_stack-1)
R=Vmn/I
Ps=som_Ps/(3+2*nbr_stack-1)
     
