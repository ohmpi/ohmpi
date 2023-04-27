from OhmPi.config import HARDWARE_CONFIG
import os
import numpy as np
from OhmPi.hardware_components import MuxAbstract
import adafruit_tca9548a  # noqa
from adafruit_mcp230xx.mcp23017 import MCP23017  # noqa
from digitalio import Direction  # noqa

MUX_CONFIG = HARDWARE_CONFIG['mux']
MUX_CONFIG['default_mux_cabling'] = {(elec, role) : ('mux_1', elec) for role in ['A', 'B', 'M', 'N'] for elec in range(1,9)} # 4 roles cabling electrodes from 1 to 8

inner_cabling ={'4_roles' : {(1, 'X'): {'MCP': 0, 'MCP_GPIO': 0},
                 (2, 'X'): {'MCP': 0, 'MCP_GPIO': 1},
                 (3, 'X'): {'MCP': 0, 'MCP_GPIO': 2},
                 (4, 'X'): {'MCP': 0, 'MCP_GPIO': 3},
                 (5, 'X'): {'MCP': 0, 'MCP_GPIO': 4},
                 (6, 'X'): {'MCP': 0, 'MCP_GPIO': 5},
                 (7, 'X'): {'MCP': 0, 'MCP_GPIO': 6},
                 (8, 'X'): {'MCP': 0, 'MCP_GPIO': 7},
                 (1, 'Y'): {'MCP': 0, 'MCP_GPIO': 8},
                 (2, 'Y'): {'MCP': 0, 'MCP_GPIO': 9},
                 (3, 'Y'): {'MCP': 0, 'MCP_GPIO': 10},
                 (4, 'Y'): {'MCP': 0, 'MCP_GPIO': 11},
                 (5, 'Y'): {'MCP': 0, 'MCP_GPIO': 12},
                 (6, 'Y'): {'MCP': 0, 'MCP_GPIO': 13},
                 (7, 'Y'): {'MCP': 0, 'MCP_GPIO': 14},
                 (8, 'Y'): {'MCP': 0, 'MCP_GPIO': 15},
                 (8, 'XX'): {'MCP': 1, 'MCP_GPIO': 0},
                 (7, 'XX'): {'MCP': 1, 'MCP_GPIO': 1},
                 (6, 'XX'): {'MCP': 1, 'MCP_GPIO': 2},
                 (5, 'XX'): {'MCP': 1, 'MCP_GPIO': 3},
                 (4, 'XX'): {'MCP': 1, 'MCP_GPIO': 4},
                 (3, 'XX'): {'MCP': 1, 'MCP_GPIO': 5},
                 (2, 'XX'): {'MCP': 1, 'MCP_GPIO': 6},
                 (1, 'XX'): {'MCP': 1, 'MCP_GPIO': 7},
                 (8, 'YY'): {'MCP': 1, 'MCP_GPIO': 8},
                 (7, 'YY'): {'MCP': 1, 'MCP_GPIO': 9},
                 (6, 'YY'): {'MCP': 1, 'MCP_GPIO': 10},
                 (5, 'YY'): {'MCP': 1, 'MCP_GPIO': 11},
                 (4, 'YY'): {'MCP': 1, 'MCP_GPIO': 12},
                 (3, 'YY'): {'MCP': 1, 'MCP_GPIO': 13},
                 (2, 'YY'): {'MCP': 1, 'MCP_GPIO': 14},
                 (1, 'YY'): {'MCP': 1, 'MCP_GPIO': 15}},
        '2_roles': {(1, 'X'): {'MCP': 0, 'MCP_GPIO': 0},  # TODO: WARNING check 2_roles table, it has not been verified yet !!!
                 (2, 'X'): {'MCP': 0, 'MCP_GPIO': 1},
                 (3, 'X'): {'MCP': 0, 'MCP_GPIO': 2},
                 (4, 'X'): {'MCP': 0, 'MCP_GPIO': 3},
                 (5, 'X'): {'MCP': 0, 'MCP_GPIO': 4},
                 (6, 'X'): {'MCP': 0, 'MCP_GPIO': 5},
                 (7, 'X'): {'MCP': 0, 'MCP_GPIO': 6},
                 (8, 'X'): {'MCP': 0, 'MCP_GPIO': 7},
                 (9, 'Y'): {'MCP': 0, 'MCP_GPIO': 8},
                 (10, 'Y'): {'MCP': 0, 'MCP_GPIO': 9},
                 (11, 'Y'): {'MCP': 0, 'MCP_GPIO': 10},
                 (12, 'Y'): {'MCP': 0, 'MCP_GPIO': 11},
                 (13, 'Y'): {'MCP': 0, 'MCP_GPIO': 12},
                 (14, 'Y'): {'MCP': 0, 'MCP_GPIO': 13},
                 (15, 'Y'): {'MCP': 0, 'MCP_GPIO': 14},
                 (16, 'Y'): {'MCP': 0, 'MCP_GPIO': 15},
                 (8, 'X'): {'MCP': 1, 'MCP_GPIO': 0},
                 (7, 'X'): {'MCP': 1, 'MCP_GPIO': 1},
                 (6, 'X'): {'MCP': 1, 'MCP_GPIO': 2},
                 (5, 'X'): {'MCP': 1, 'MCP_GPIO': 3},
                 (4, 'X'): {'MCP': 1, 'MCP_GPIO': 4},
                 (3, 'X'): {'MCP': 1, 'MCP_GPIO': 5},
                 (2, 'X'): {'MCP': 1, 'MCP_GPIO': 6},
                 (1, 'X'): {'MCP': 1, 'MCP_GPIO': 7},
                 (16, 'Y'): {'MCP': 1, 'MCP_GPIO': 8},
                 (15, 'Y'): {'MCP': 1, 'MCP_GPIO': 9},
                 (14, 'Y'): {'MCP': 1, 'MCP_GPIO': 10},
                 (13, 'Y'): {'MCP': 1, 'MCP_GPIO': 11},
                 (12, 'Y'): {'MCP': 1, 'MCP_GPIO': 12},
                 (11, 'Y'): {'MCP': 1, 'MCP_GPIO': 13},
                 (10, 'Y'): {'MCP': 1, 'MCP_GPIO': 14},
                 (9, 'Y'): {'MCP': 1, 'MCP_GPIO': 15}}}


class Mux(MuxAbstract):
    def __init__(self, **kwargs):
        kwargs.update({'board_name': os.path.basename(__file__).rstrip('.py')})
        if 'cabling' not in kwargs.keys():
            kwargs.update({'cabling': MUX_CONFIG['default_mux_cabling']})
        super().__init__(**kwargs)
        self.exec_logger.debug(f'configuration: {MUX_CONFIG}')
        tca_address = kwargs.pop('tca_address', None)
        tca_channel = kwargs.pop('tca_channel', 0)
        self._roles = kwargs.pop('roles', None)
        if self._roles is None:
            self._roles = {'A': 'X', 'B': 'Y', 'M' : 'XX', 'N' : 'YY'}
        if np.alltrue([j in self._roles.values() for j in set([i[1] for i in list(inner_cabling['4_roles'].keys())])]):
            self._mode = '4_roles'
        elif np.alltrue([j in self._roles.values() for j in set([i[1] for i in list(inner_cabling['2_roles'].keys())])]):
            self._mode = '2_roles'
        else:
            self.exec_logger.error(f'Invalid role assignment for {self.board_name}: {self._roles} !')
            self._mode = ''
        if tca_address is None:
            self._tca = self.controller.bus
        else:
            self._tca = adafruit_tca9548a.TCA9548A(self.controller.bus, tca_address)[tca_channel]
        self._mcp_addresses = (kwargs.pop('mcp_0', '0x22'), kwargs.pop('mcp_1', '0x23'))  # TODO add assert on valid addresses..
        self._mcp = [None, None]
        self.reset()
        if self.addresses is None:
            self._get_addresses()
        self.exec_logger.debug(f'addresses: {self.addresses}')

    def _get_addresses(self):
        """ Converts inner cabling addressing into (electrodes, role) addressing """
        ic = inner_cabling[self._mode]
        self.addresses = {}
        d = {}
        for k, v in self.cabling.items():
            d.update({k: ic[(v[0], self._roles[k[1]])]})
        self.addresses = d

    def reset(self):
        self._mcp[0] = MCP23017(self._tca, address=int(self._mcp_addresses[0], 16))
        self._mcp[1] = MCP23017(self._tca, address=int(self._mcp_addresses[1], 16))

    def switch_one(self, elec=None, role=None, state=None):
        MuxAbstract.switch_one(self, elec=elec, role=role, state=state)

        def set_relay_state(mcp, mcp_pin, state=True):
            pin_enable = mcp.get_pin(mcp_pin)
            pin_enable.direction = Direction.OUTPUT
            pin_enable.value = state

        d = self.addresses[elec, role]
        if state == 'on':
            set_relay_state(self._mcp[d['MCP']], d['MCP_GPIO'], True)
        if state == 'off':
            set_relay_state(self._mcp[d['MCP']], d['MCP_GPIO'], False)

    def test(self, *args):
        MuxAbstract.test(self, *args)