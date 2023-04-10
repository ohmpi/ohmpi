# definition of hardware level functions
import numpy as np

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
import minimalmodbus  # noqa
import time

# global variable
i2c = busio.I2C(board.SCL, board.SDA)

from config import OHMPI_CONFIG


class Alimentation():
    def __init__(self, address=0x20, tx_voltage=12):
        self.mcp = MCP23017(i2c, address=address)
        self.tx_voltage = tx_voltage
        self.polarity = True
        self.on = False
        self.pinA = 0
        self.pinB = 1

        # setup DPS
        self.DPS = minimalmodbus.Instrument(port='/dev/ttyUSB0', slaveaddress=1)  # port name, address (decimal)
        self.DPS.serial.baudrate = 9600  # Baud rate 9600 as listed in doc
        self.DPS.serial.bytesize = 8  #
        self.DPS.serial.timeout = 1  # greater than 0.5 for it to work
        self.DPS.debug = False  #
        self.DPS.serial.parity = 'N'  # No parity
        self.DPS.mode = minimalmodbus.MODE_RTU  # RTU mode
        self.DPS.write_register(0x0001, 40, 0)  # max current allowed (36 mA for relays)
        # (last number) 0 is for mA, 3 is for A
       
    def turn_on(self):
        if self.on is False:
            self.DPS.write_register(0x09, 1)  # DPS5005 on
            self.on = True

    def turn_off(self):
        self.DPS.write_register(0x09, 0)  # DPS5005 off
        self.on = False

    def start_injection(self, polarity=True):
        # injection courant and measure (TODO check if it works, otherwise back in run_measurement())
        self.polarity = polarity
        if self.polarity:
            self.pin0 = self.mcp.get_pin(self.pinA)
            self.pin0.direction = Direction.OUTPUT
            self.pin0.value = True
            self.pin1 = self.mcp.get_pin(self.pinB)
            self.pin1.direction = Direction.OUTPUT
            self.pin1.value = False
        else:
            self.pin0 = self.mcp.get_pin(self.pinA)
            self.pin0.direction = Direction.OUTPUT
            self.pin0.value = False
            self.pin1 = self.mcp.get_pin(self.pinB)
            self.pin1.direction = Direction.OUTPUT
            self.pin1.value = True

    def stop_injection(self):
        self.pin0 = self.mcp.get_pin(self.pinA)
        self.pin0.direction = Direction.OUTPUT
        self.pin0.value = False
        self.pin1 = self.mcp.get_pin(self.pinB)
        self.pin1.direction = Direction.OUTPUT
        self.pin1.value = False
       
    def set_polarity(self, polarity=True):
        self.polarity = polarity
       
    def set_tx_voltage(self, tx_voltage=12):
       if tx_voltage >= 0:
            self.tx_voltage = tx_voltage
            # set voltage for test
            self.DPS.write_register(0x0000, tx_voltage, 2)
            self.DPS.write_register(0x09, 1)  # DPS5005 on
       else:
          raise ValueError('Voltage needs to be >= 0 V')
       

class ADS():  # analog to digital converter ADS1115
    def __init__(self, address=0x48, gain=2/3, data_rate=820, mode=1):
        self.ads = ads.ADS1115(i2c, gain=gain, data_rate=data_rate, address=address, mode=mode)
        self.gain = gain
        self.data_rate = data_rate
        self.mode = mode
        self.pins = {
            0: self.ads.P0,
            1: self.ads.P1,
            2: self.ads.P2,
            3: self.ads.P3,
        }
        self.vmin = 0.01  # volts
        self.vmax = 4.5  # volts

    def read_single(self, pin=0):
        return AnalogIn(self.ads, self.pins[pin]).voltage
    
    def read_diff(self, pins='01'):
        if pins == '01':
            return AnalogIn(self.ads, self.ads.P0, self.ads.P1).voltage
        elif pins == '23':
            return AnalogIn(self.ads, self.ads.P2, self.ads.P3).voltage

    def set_gain(self, gain=2/3):
        self.gain = gain
        # TODO maybe there is already a set_gain() function in the library? check that
        self.ads = ads.ADS1115(
            i2c, gain=self.gain, data_rate=self.data_rate,
            address=self.address, mode=self.mode)
        
    def get_best_gain(self, channel=0):
        """Automatically sets the gain on a channel

        Parameters
        ----------
        channel : ads.ADS1x15
            Instance of ADS where voltage is measured.

        Returns
        -------
        gain : float
            Gain to be applied on ADS1115.
        """
        voltage = self.read_singl(channel)  
        gain = 2 / 3
        if (abs(voltage) < 2.040) and (abs(voltage) >= 1.023):
            gain = 2
        elif (abs(voltage) < 1.023) and (abs(voltage) >= 0.508):
            gain = 4
        elif (abs(voltage) < 0.508) and (abs(voltage) >= 0.250):
            gain = 8
        elif abs(voltage) < 0.256:
            gain = 16
        #self.exec_logger.debug(f'Setting gain to {gain}')
        return gain
    
    def set_best_gain(self, channel=0):
        gain = self.get_best_gain(channel)
        self.set_gain(gain)
        

class Voltage(ADS): # for MN
    def __init__(self):
        super().__init__()
    
    def read(self, pin=0):
        return self.read_single(self, pin=pin)
    
    def read_all(self, pins=[0, 2]):
        return [self.read_single(pin) for pin in pins]


class Current(ADS):  # for AB
    def __init__(self, address=0x48, gain=2/3, data_rate=820, mode=1, r_shunt=OHMPI_CONFIG['R_shunt']):
        super().__init__(address=address, gain=gain, data_rate=data_rate, mode=mode)
        self.r_shunt = r_shunt
        self.imin = self.vmin / (self.r_shunt * 50)
        self.imax = self.vmax / (self.r_shunt * 50)

    def read(self):
        U = self.read_single(pin=0)
        return U / 50 / self.r_shunt        


class Multiplexer():
    def __init__(self, addresses={
        'A': 0x70,
        'B': 0x71,
        'M': 0x72,
        'N': 0x73
        },
        nelec=64):
        #OHMPI_CONFIG['board_addresses']
        self.addresses = addresses
        self.nelec = nelec  # max number of electrodes per board

    def switch_one(self, elec, role, state='off'):
        self.tca = adafruit_tca9548a.TCA9548A(i2c, self.addresses[role])
        # find I2C address of the electrode and corresponding relay
        # considering that one MCP23017 can cover 16 electrodes
        i2c_address = 7 - (elec - 1) // 16  # quotient without rest of the division
        relay = (elec-1) - ((elec-1) // 16) * 16

        if i2c_address is not None:
            # select the MCP23017 of the selected MUX board
            mcp = MCP23017(self.tca[i2c_address])
            mcp.get_pin(relay - 1).direction = digitalio.Direction.OUTPUT
            if state == 'on':
                mcp.get_pin(relay - 1).value = True
            else:
                mcp.get_pin(relay - 1).value = False
            #exec_logger.debug(f'Switching relay {relay} '
            #                        f'({str(hex(self.addresses[role]))}) on:{on} for electrode {elec}')
        else:
            raise ValueError('No I2C address found for the electrode'
                             ' {:d} on board {:s}'.format(elec, self.addresses[role]))
            #exec_logger.warning(f'Unable to address electrode nr {elec}')

    def switch(self, elecdic={}, state='on'):
        """Switch a given list of electrodes with different roles.
        Electrodes with a value of 0 will be ignored.
        
        Parameters
        ----------
        elecdic : dictionary, optional
            Dictionnary of the form: role: [list of electrodes].
        state : str, optional
            Either 'on' or 'off'.
        """
        # check to prevent A == B (SHORT-CIRCUIT)
        if 'A' in elecdic and 'B' in elecdic:
            out = np.in1d(elecdic['A'], elecdic['B'])
            if out.any():
                raise ValueError('Some electrodes have A == B -> SHORT-CIRCUIT')
                return
            
        # check none of M and N are the same A or B
        # as to prevent burning the MN part which cannot take
        # the full voltage of the DPS
        if 'A' in elecdic and 'B' in elecdic and 'M' in elecdic and 'N' in elecdic:
            if (np.in1d(elecdic['M'], elecdic['A']).any()
                or np.in1d(elecdic['M'], elecdic['B']).any()
                or np.in1d(elecdic['N'], elecdic['A']).any()
                or np.in1d(elecdic['N'], elecdic['B']).any()):
                raise ValueError('Some electrodes M and N are on A and B -> cannot be with DPS')
                return
        
        # if all ok, then switch the electrodes
        for role in elecdic:
            for elec in elecdic[role]:
                if elec > 0:
                    self.switch_one(elec, role, state)

    def reset(self):
        for role in self.addresses:
            for elec in range(self.nelec):
                self.switch_one(elec, role, 'off')

    def test(self, role, activation_time=1):
        """Interactive method to test the multiplexer.

        Parameters
        ----------
        activation_time : float, optional
            Time in seconds during which the relays are activated.
        address : hex, optional
            Address of the multiplexer board to test (e.g. 0x70, 0x71, ...).
        """
        self.reset()

        # ask use some details on how to proceed
        a = input('If you want try 1 channel choose 1, if you want try all channels choose 2!')
        if a == '1':
            print('run channel by channel test')
            electrode = int(input('Choose your electrode number (integer):'))
            electrodes = [electrode]
        elif a == '2':
            electrodes = range(1, 65)
        else:
            print('Wrong choice !')
            return

            # run the test
        for elec in electrodes:
            self.switch_one(elec, role, 'on')
            print('electrode:', elec, ' activated...', end='', flush=True)
            time.sleep(activation_time)
            self.switch_one(elec, role, 'off')
            print(' deactivated')
            time.sleep(activation_time)
        print('Test finished.')

            



