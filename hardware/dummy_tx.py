from OhmPi.config import HARDWARE_CONFIG
import time
import os
import numpy as np
from OhmPi.hardware import TxAbstract

TX_CONFIG = HARDWARE_CONFIG['tx']

# hardware limits
voltage_min = 10.  # mV
voltage_max = 4500.

TX_CONFIG['current_min'] = voltage_min / (TX_CONFIG['R_shunt'] * 50)  # mA
TX_CONFIG['current_max'] = voltage_max / (TX_CONFIG['R_shunt'] * 50)
TX_CONFIG['default_voltage'] = 5.  # V
TX_CONFIG['voltage_max'] = 50.  # V
TX_CONFIG['dps_switch_on_warm_up'] = 4. # 4 seconds

class Tx(TxAbstract):
    def inject(self, state='on'):
        pass

    def __init__(self, **kwargs):
        kwargs.update({'board_name': os.path.basename(__file__).rstrip('.py')})
        super().__init__(**kwargs)
        self._voltage = kwargs.pop('voltage', TX_CONFIG['default_voltage'])

        self._adc_gain = 1

        self.polarity = 0
        self.turn_on()
        time.sleep(TX_CONFIG['dps_switch_on_warm_up'])
        self.exec_logger.info(f'TX battery: {self.tx_bat:.1f} V')
        self.turn_off()

    @property
    def adc_gain(self):
        return self._adc_gain

    @adc_gain.setter
    def adc_gain(self, value):
        self._adc_gain = value
        self.exec_logger.debug(f'Setting TX ADC gain to {value}')

    def adc_gain_auto(self):
        gain = 1.
        self.exec_logger.debug(f'Setting TX ADC gain automatically to {gain}')
        self.adc_gain = gain

    def current_pulse(self, **kwargs):
        super().current_pulse(**kwargs)
        self.exec_logger.warning(f'Current pulse is not implemented for the {TX_CONFIG["model"]} board')

    @property
    def current(self):
        """ Gets the current IAB in Amps
        """
        current = np.abs(np.random.normal(0.7, 0.2))
        self.exec_logger.debug(f'Reading random current on TX. Returning {current} A')
        return current

    @ current.setter
    def current(self, value):
        assert TX_CONFIG['current_min'] <= value <= TX_CONFIG['current_max']
        self.exec_logger.warning(f'Current pulse is not implemented for the {TX_CONFIG["model"]} board')

    @property
    def voltage(self):
        return self._voltage
    @voltage.setter
    def voltage(self, value):
        if value > TX_CONFIG['voltage_max']:
            self.exec_logger.warning(f'Sorry, cannot inject more than {TX_CONFIG["voltage_max"]} V, '
                                     f'set it back to {TX_CONFIG["default_voltage"]} V (default value).')
            value = TX_CONFIG['default_voltage']
        if value < 0.:
            self.exec_logger.warning(f'Voltage should be given as a positive number. '
                                     f'Set polarity to -1 to reverse voltage...')
            value = np.abs(value)


    @property
    def tx_bat(self):
        tx_bat = np.random.uniform(10.9, 13.4)
        if tx_bat < 12.:
            self.soh_logger.debug(f'Low TX Battery: {tx_bat:.1f} V')
        return tx_bat

    def voltage_pulse(self, voltage=TX_CONFIG['default_voltage'], length=None, polarity=None):
        """ Generates a square voltage pulse

        Parameters
        ----------
        voltage: float, optional
            Voltage to apply in volts, tx_v_def is applied if omitted.
        length: float, optional
            Length of the pulse in seconds
        polarity: 1,0,-1
            Polarity of the pulse
        """

        if length is None:
            length = self.inj_time
        if polarity is None:
            polarity = self.polarity
        self.polarity = polarity
        self.voltage = voltage
        self.exec_logger.debug(f'Voltage pulse of {polarity*voltage:.3f} V for {length:.3f} s')
        self.inject(state='on')
        time.sleep(length)
        self.inject(state='off')
