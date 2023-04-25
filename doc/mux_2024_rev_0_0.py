from OhmPi.config import HARDWARE_CONFIG
import os
from OhmPi.hardware_components import MuxAbstract
MUX_CONFIG = HARDWARE_CONFIG['mux']

class Mux(MuxAbstract):
    def __init__(self, **kwargs):
        kwargs.update({'board_name': os.path.basename(__file__).rstrip('.py')})
        super().__init__(**kwargs)
        self.max_elec = MUX_CONFIG['max_elec']

    def switch_one(self, elec, role, state='off'):
        self.tca = adafruit_tca9548a.TCA9548A(i2c, self.addresses[role])
        # find I2C address of the electrode and corresponding relay
        # considering that one MCP23017 can cover 16 electrodes
        i2c_address = 7 - (elec - 1) // 16  # quotient without rest of the division
        relay = (elec - 1) - ((elec - 1) // 16) * 16

        if i2c_address is not None:
            # select the MCP23017 of the selected MUX board
            mcp = MCP23017(self.tca[i2c_address])
            mcp.get_pin(relay - 1).direction = digitalio.Direction.OUTPUT
            if state == 'on':
                mcp.get_pin(relay - 1).value = True
            else:
                mcp.get_pin(relay - 1).value = False
            # exec_logger.debug(f'Switching relay {relay} '
            #                        f'({str(hex(self.addresses[role]))}) on:{on} for electrode {elec}')
        else:
            raise ValueError('No I2C address found for the electrode'
                             ' {:d} on board {:s}'.format(elec, self.addresses[role]))
            # exec_logger.warning(f'Unable to address electrode nr {elec}')

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