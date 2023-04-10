# definition of hardware level functions
import numpy as np
import time

# global variable

from config import OHMPI_CONFIG


class Alimentation():
    def __init__(self, address=0x20, tx_voltage=12):
        self.mcp = {address: address}
        self.tx_voltage = tx_voltage
        self.polarity = True
        self.on = False
        self.pinA = 0
        self.pinB = 1
        self.pin0 = False
        self.pin1 = False

        # setup DPS
        self.DPS = {'dps': True}

    def turn_on(self):
        if self.on is False:
            self.on = True

    def turn_off(self):
        self.on = False

    def start_injection(self, polarity=True):
        # injection courant and measure (TODO check if it works, otherwise back in run_measurement())
        self.polarity = polarity
        if self.polarity:
            self.pin0 = True
            self.pin1 = False
        else:
            self.pin0 = False
            self.pin1 = True

    def stop_injection(self):
        self.pin0 = False
        self.pin1 = False
       
    def set_polarity(self, polarity=True):
        self.polarity = polarity
       
    def set_tx_voltage(self, tx_voltage=12):
       if tx_voltage >= 0:
            self.tx_voltage = tx_voltage
       else:
          raise ValueError('Voltage needs to be >= 0 V')
       

class ADS():  # analog to digital converter ADS1115
    def __init__(self, address=0x48, gain=2/3, data_rate=820, mode=1):
        self.ads = {gain: gain, data_rate: data_rate, address: address, mode: mode}
        self.gain = gain
        self.data_rate = data_rate
        self.mode = mode
        self.pins = {
            0: 'P0',
            1: 'P1',
            2: 'P2',
            3: 'P3',
        }
        self.vmin = 0.01  # volts
        self.vmax = 4.5  # volts

    def read_single(self, pin=0):
        return np.abs(np.random.randn(1))[0]*4.5
    
    def read_diff(self, pins='01'):
        if pins == '01':
            return np.abs(np.random.randn(1))[0]*4.5
        elif pins == '23':
            return np.abs(np.random.randn(1))[0]*4.5

    def set_gain(self, gain=2/3):
        self.gain = gain
        # TODO maybe there is already a set_gain() function in the library? check that
        
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
        voltage = self.read_single(channel)  
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
        self.relays = {'A': [], 'B': [], 'M': [], 'N': []}

    def switch_one(self, elec, role, state='off'):
        # find I2C address of the electrode and corresponding relay
        # considering that one MCP23017 can cover 16 electrodes
        i2c_address = 7 - (elec - 1) // 16  # quotient without rest of the division
        relay = (elec-1) - ((elec-1) // 16) * 16

        if i2c_address is not None:
            # select the MCP23017 of the selected MUX board
            if state == 'on':
                self.relays[role].append(elec)
            else:
                if elec in self.relays[role]:
                    self.relays[role].remove(elec)
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

            



