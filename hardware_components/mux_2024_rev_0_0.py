from OhmPi.config import HARDWARE_CONFIG
import os
import numpy as np
from OhmPi.hardware_components import MuxAbstract
import adafruit_tca9548a  # noqa
from adafruit_mcp230xx.mcp23017 import MCP23017  # noqa
from digitalio import Direction  # noqa

MUX_CONFIG = HARDWARE_CONFIG['mux']

# d = {(1, 'A'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 34, 'MCP_GPIO': 0},
#      (2, 'A'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 34, 'MCP_GPIO': 1},
#      (3, 'A'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 34, 'MCP_GPIO': 2},
#      (4, 'A'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 34, 'MCP_GPIO': 3},
#      (5, 'A'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 34, 'MCP_GPIO': 4},
#      (6, 'A'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 34, 'MCP_GPIO': 5},
#      (7, 'A'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 34, 'MCP_GPIO': 6},
#      (8, 'A'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 34, 'MCP_GPIO': 7},
#      (1, 'B'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 34, 'MCP_GPIO': 8},
#      (2, 'B'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 34, 'MCP_GPIO': 9},
#      (3, 'B'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 34, 'MCP_GPIO': 10},
#      (4, 'B'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 34, 'MCP_GPIO': 11},
#      (5, 'B'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 34, 'MCP_GPIO': 12},
#      (6, 'B'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 34, 'MCP_GPIO': 13},
#      (7, 'B'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 34, 'MCP_GPIO': 14},
#      (8, 'B'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 34, 'MCP_GPIO': 15},
#      (8, 'M'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 35, 'MCP_GPIO': 0},
#      (7, 'M'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 35, 'MCP_GPIO': 1},
#      (6, 'M'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 35, 'MCP_GPIO': 2},
#      (5, 'M'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 35, 'MCP_GPIO': 3},
#      (4, 'M'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 35, 'MCP_GPIO': 4},
#      (3, 'M'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 35, 'MCP_GPIO': 5},
#      (2, 'M'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 35, 'MCP_GPIO': 6},
#      (1, 'M'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 35, 'MCP_GPIO': 7},
#      (8, 'N'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 35, 'MCP_GPIO': 8},
#      (7, 'N'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 35, 'MCP_GPIO': 9},
#      (6, 'N'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 35, 'MCP_GPIO': 10},
#      (5, 'N'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 35, 'MCP_GPIO': 11},
#      (4, 'N'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 35, 'MCP_GPIO': 12},
#      (3, 'N'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 35, 'MCP_GPIO': 13},
#      (2, 'N'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 35, 'MCP_GPIO': 14},
#      (1, 'N'): {'TCA_address': None, 'TCA_channel': 0, 'MCP_address': 35, 'MCP_GPIO': 15}}

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
        '2_roles': {(1, 'X'): {'MCP': 0, 'MCP_GPIO': 0},  # TODO: check 2_roles table !!!
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
                 (8, 'X'): {'MCP': 1, 'MCP_GPIO': 0},
                 (7, 'X'): {'MCP': 1, 'MCP_GPIO': 1},
                 (6, 'X'): {'MCP': 1, 'MCP_GPIO': 2},
                 (5, 'X'): {'MCP': 1, 'MCP_GPIO': 3},
                 (4, 'X'): {'MCP': 1, 'MCP_GPIO': 4},
                 (3, 'X'): {'MCP': 1, 'MCP_GPIO': 5},
                 (2, 'X'): {'MCP': 1, 'MCP_GPIO': 6},
                 (1, 'X'): {'MCP': 1, 'MCP_GPIO': 7},
                 (8, 'Y'): {'MCP': 1, 'MCP_GPIO': 8},
                 (7, 'Y'): {'MCP': 1, 'MCP_GPIO': 9},
                 (6, 'Y'): {'MCP': 1, 'MCP_GPIO': 10},
                 (5, 'Y'): {'MCP': 1, 'MCP_GPIO': 11},
                 (4, 'Y'): {'MCP': 1, 'MCP_GPIO': 12},
                 (3, 'Y'): {'MCP': 1, 'MCP_GPIO': 13},
                 (2, 'Y'): {'MCP': 1, 'MCP_GPIO': 14},
                 (1, 'Y'): {'MCP': 1, 'MCP_GPIO': 15}}}


class Mux(MuxAbstract):
    def __init__(self, **kwargs):
        kwargs.update({'board_name': os.path.basename(__file__).rstrip('.py')})
        super().__init__(**kwargs)
        self.exec_logger.debug(f'configuration: {MUX_CONFIG}')
        self._tca_address = kwargs.pop('tca_address', None)
        self._tca_channel = kwargs.pop('tca_channel', 0)
        self._roles = kwargs.pop('roles', None)
        if self._roles is None:
            self._roles = {'X': 'A', 'Y': 'B', 'XX': 'M', 'YY': 'N'}
        if np.alltrue([j in self._roles for j in set([i[1] for i in list(inner_cabling['4_roles'].keys())])]):
            self._mode = '4_roles'
        elif np.alltrue([j in self._roles for j in set([i[1] for i in list(inner_cabling['2_roles'].keys())])]):
            self._mode = '2_roles'
        else:
            self.exec_logger.error(f'Invalid role assignment for {self.board_name}: {self._roles} !')
            self._mode = ''
        self._mcp = [0, 0]
        self._mcp[0] = int(kwargs.pop('mcp_0', '0x22'), 16)  # TODO add assert on valid addresses..
        self._mcp[1] = int(kwargs.pop('mcp_1', '0x23'), 16)
        if self.addresses is None:
            self._get_addresses()
        self.exec_logger.debug(f'addresses: {self.addresses}')

    def _get_addresses(self):
        d = inner_cabling[self._mode]
        self.addresses = {}
        for k, v in d.items():
            self.addresses.update({(k[0], self._roles[k[1]]): v.update({'MCP': self._mcp[v['MCP']]})})
        print(f'addresses: {self.addresses}')

    # def _get_addresses(self, addresses_file):  TODO : delete me
    #     self.exec_logger.debug('Getting addresses...')
    #     with open(addresses_file, 'r') as f:
    #         x = json.load(f)
    #
    #     self.addresses = {}
    #     for k, v in x.items():
    #         y = k.strip('(').strip(')').split(', ')
    #         if v['TCA_address'] is not None:
    #             v['TCA_address'] = int(v['TCA_address'], 16)
    #         if v['MCP_address'] is not None:
    #             v['MCP_address'] = int(x[k]['MCP_address'], 16)
    #         self.addresses.update({(int(y[0]), y[1]): v})

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
        self.exec_logger.debug(f'switching {state} electrode {elec} with role {role} on TCA {d["TCA_address"]}, channel '
                               f'{d["TCA_channel"]}, MCP {d["MCP_address"]}, gpio {d["MCP_GPIO"]}')
        if state == 'on':
            set_relay_state(mcp, d['MCP_GPIO'], True)
        if state == 'off':
            set_relay_state(mcp, d['MCP_GPIO'], False)

    def test(self, *args):
        MuxAbstract.test(self, *args)