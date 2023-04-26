from OhmPi.config import HARDWARE_CONFIG
import os
import json
from OhmPi.hardware_components import MuxAbstract
import adafruit_tca9548a  # noqa
from adafruit_mcp230xx.mcp23017 import MCP23017  # noqa
from digitalio import Direction  # noqa

MUX_CONFIG = HARDWARE_CONFIG['mux']

class Mux(MuxAbstract):
    def __init__(self, **kwargs):
        kwargs.update({'board_name': os.path.basename(__file__).rstrip('.py')})
        super().__init__(**kwargs)
        self.exec_logger.debug(f'configuration: {MUX_CONFIG}')
        self.max_elec = MUX_CONFIG['max_elec']
        if self.addresses is None or 'addresses' in MUX_CONFIG.keys():
            self._get_addresses(MUX_CONFIG['addresses'])
            self.exec_logger.debug(f'Using {MUX_CONFIG["addresses"]} for {self.board_name}...')
        self.exec_logger.debug(f'addresses: {self.addresses}')

    def _get_addresses(self, addresses_file):
        self.exec_logger.debug('Getting addresses...')
        with open(addresses_file, 'r') as f:
            x = json.load(f)

        self.addresses = {}
        for k in x.keys():
            y = k.strip('(').strip(')').split(', ')
            self.addresses.update({(int(y[0]), y[1]): x[k]})

    def reset(self):
        pass

    def switch_one(self, elec=None, role=None, state=None):
        MuxAbstract.switch_one(self, elec=elec, role=role, state=state)

        def set_relay_state(mcp, mcp_pin, state=True):
            pin_enable = mcp.get_pin(mcp_pin)
            pin_enable.direction = Direction.OUTPUT
            pin_enable.value = state

        d = self.addresses[elec, role]
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

    def test(self, *args):
        MuxAbstract.test(self, *args)