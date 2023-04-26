from OhmPi.config import HARDWARE_CONFIG
import os
from OhmPi.hardware_components import MuxAbstract
import adafruit_tca9548a  # noqa
from adafruit_mcp230xx.mcp23017 import MCP23017  # noqa
from digitalio import Direction  # noqa

MUX_CONFIG = HARDWARE_CONFIG['mux']

class Mux(MuxAbstract):
    def __init__(self, **kwargs):
        kwargs.update({'board_name': os.path.basename(__file__).rstrip('.py')})
        super().__init__(**kwargs)
        self.max_elec = MUX_CONFIG['max_elec']
        print(os.path.curdir)
        if self._addresses is None and 'addresses' in MUX_CONFIG.keys():
            self._get_addresses(MUX_CONFIG['addresses'])

    def reset(self):
        pass

    def switch_one(self, elec=None, role=None, state=None):
        MuxAbstract.switch_one(self, elec=elec, role=role, state=state)

        def set_relay_state(mcp, mcp_pin, state=True):
            pin_enable = mcp.get_pin(mcp_pin)
            pin_enable.direction = Direction.OUTPUT
            pin_enable.value = state

        d = self._addresses[elec, role]
        if d['TCA_address'] is None:
            tca = self.controller.bus
        else:
            tca = adafruit_tca9548a.TCA9548A(self.controller.bus, d['TCA_address'])[d['TCA_channel']]
        mcp = MCP23017(tca, address=d['MCP_address'])
        if state == 'on':
            print('opening gpio nr', d['MCP_GPIO'])
            print('opening electrode nr', elec)
            print('opening role', role)
            print('opening MCP', d['MCP_address'])
            set_relay_state(mcp, d['MCP_GPIO'], True)
        if state == 'off':
            set_relay_state(mcp, d['MCP_GPIO'], False)

        # self.tca = adafruit_tca9548a.TCA9548A(i2c, self.addresses[role])
        # # find I2C address of the electrode and corresponding relay
        # # considering that one MCP23017 can cover 16 electrodes
        # i2c_address = 7 - (elec - 1) // 16  # quotient without rest of the division
        # relay = (elec - 1) - ((elec - 1) // 16) * 16
        #
        # if i2c_address is not None:
        #     # select the MCP23017 of the selected MUX board
        #     mcp = MCP23017(self.tca[i2c_address])
        #     mcp.get_pin(relay - 1).direction = digitalio.Direction.OUTPUT
        #     if state == 'on':
        #         mcp.get_pin(relay - 1).value = True
        #     else:
        #         mcp.get_pin(relay - 1).value = False
        #     # exec_logger.debug(f'Switching relay {relay} '
        #     #                        f'({str(hex(self.addresses[role]))}) on:{on} for electrode {elec}')
        # else:
        #     raise ValueError('No I2C address found for the electrode'
        #                      ' {:d} on board {:s}'.format(elec, self.addresses[role]))
        #     # exec_logger.warning(f'Unable to address electrode nr {elec}')

    def test(self, *args):
        MuxAbstract.test(self, *args)