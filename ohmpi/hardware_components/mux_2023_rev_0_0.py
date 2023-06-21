import time

from ohmpi.config import HARDWARE_CONFIG
import os
import numpy as np
from ohmpi.hardware_components import MuxAbstract
import adafruit_tca9548a  # noqa
from adafruit_mcp230xx.mcp23017 import MCP23017  # noqa
from digitalio import Direction  # noqa

MUX_CONFIG = HARDWARE_CONFIG['mux'].pop('default', {})
MUX_CONFIG.update({'voltage_max': 50., 'current_max': 3.})  # board default values that overwrite system default values
MUX_CONFIG.update({'activation_delay': 0.01, 'release_delay': 0.005})  # s
default_mux_cabling = {(elec, role) : ('mux_1', elec) for role in ['A', 'B', 'M', 'N'] for elec in range(1,9)} # defaults to 4 roles cabling electrodes from 1 to 8


inner_cabling = {'1_role' : {(1, 'X'): {'MCP': 0, 'MCP_GPIO': 0},
                             (2, 'X'): {'MCP': 0, 'MCP_GPIO': 1},
                             (3, 'X'): {'MCP': 0, 'MCP_GPIO': 2},
                             (4, 'X'): {'MCP': 0, 'MCP_GPIO': 3},
                             (5, 'X'): {'MCP': 0, 'MCP_GPIO': 4},
                             (6, 'X'): {'MCP': 0, 'MCP_GPIO': 5},
                             (7, 'X'): {'MCP': 0, 'MCP_GPIO': 6},
                             (8, 'X'): {'MCP': 0, 'MCP_GPIO': 7},
                             (9, 'X'): {'MCP': 0, 'MCP_GPIO': 8},
                             (10, 'X'): {'MCP': 0, 'MCP_GPIO': 9},
                             (11, 'X'): {'MCP': 0, 'MCP_GPIO': 10},
                             (12, 'X'): {'MCP': 0, 'MCP_GPIO': 11},
                             (13, 'X'): {'MCP': 0, 'MCP_GPIO': 12},
                             (14, 'X'): {'MCP': 0, 'MCP_GPIO': 13},
                             (15, 'X'): {'MCP': 0, 'MCP_GPIO': 14},
                             (16, 'X'): {'MCP': 0, 'MCP_GPIO': 15},
                             (17, 'X'): {'MCP': 1, 'MCP_GPIO': 0},
                             (18, 'X'): {'MCP': 1, 'MCP_GPIO': 1},
                             (19, 'X'): {'MCP': 1, 'MCP_GPIO': 2},
                             (20, 'X'): {'MCP': 1, 'MCP_GPIO': 3},
                             (21, 'X'): {'MCP': 1, 'MCP_GPIO': 4},
                             (22, 'X'): {'MCP': 1, 'MCP_GPIO': 5},
                             (23, 'X'): {'MCP': 1, 'MCP_GPIO': 6},
                             (24, 'X'): {'MCP': 1, 'MCP_GPIO': 7},
                             (25, 'X'): {'MCP': 1, 'MCP_GPIO': 8},
                             (26, 'X'): {'MCP': 1, 'MCP_GPIO': 9},
                             (27, 'X'): {'MCP': 1, 'MCP_GPIO': 10},
                             (28, 'X'): {'MCP': 1, 'MCP_GPIO': 11},
                             (29, 'X'): {'MCP': 1, 'MCP_GPIO': 12},
                             (30, 'X'): {'MCP': 1, 'MCP_GPIO': 13},
                             (31, 'X'): {'MCP': 1, 'MCP_GPIO': 14},
                             (32, 'X'): {'MCP': 1, 'MCP_GPIO': 15},
                             (33, 'X'): {'MCP': 2, 'MCP_GPIO': 0},
                             (34, 'X'): {'MCP': 2, 'MCP_GPIO': 1},
                             (35, 'X'): {'MCP': 2, 'MCP_GPIO': 2},
                             (36, 'X'): {'MCP': 2, 'MCP_GPIO': 3},
                             (37, 'X'): {'MCP': 2, 'MCP_GPIO': 4},
                             (38, 'X'): {'MCP': 2, 'MCP_GPIO': 5},
                             (39, 'X'): {'MCP': 2, 'MCP_GPIO': 6},
                             (40, 'X'): {'MCP': 2, 'MCP_GPIO': 7},
                             (41, 'X'): {'MCP': 2, 'MCP_GPIO': 8},
                             (42, 'X'): {'MCP': 2, 'MCP_GPIO': 9},
                             (43, 'X'): {'MCP': 2, 'MCP_GPIO': 10},
                             (44, 'X'): {'MCP': 2, 'MCP_GPIO': 11},
                             (45, 'X'): {'MCP': 2, 'MCP_GPIO': 12},
                             (46, 'X'): {'MCP': 2, 'MCP_GPIO': 13},
                             (47, 'X'): {'MCP': 2, 'MCP_GPIO': 14},
                             (48, 'X'): {'MCP': 2, 'MCP_GPIO': 15},
                             (49, 'X'): {'MCP': 3, 'MCP_GPIO': 0},
                             (50, 'X'): {'MCP': 3, 'MCP_GPIO': 1},
                             (51, 'X'): {'MCP': 3, 'MCP_GPIO': 2},
                             (52, 'X'): {'MCP': 3, 'MCP_GPIO': 3},
                             (53, 'X'): {'MCP': 3, 'MCP_GPIO': 4},
                             (54, 'X'): {'MCP': 3, 'MCP_GPIO': 5},
                             (55, 'X'): {'MCP': 3, 'MCP_GPIO': 6},
                             (56, 'X'): {'MCP': 3, 'MCP_GPIO': 7},
                             (57, 'X'): {'MCP': 3, 'MCP_GPIO': 8},
                             (58, 'X'): {'MCP': 3, 'MCP_GPIO': 9},
                             (59, 'X'): {'MCP': 3, 'MCP_GPIO': 10},
                             (60, 'X'): {'MCP': 3, 'MCP_GPIO': 11},
                             (61, 'X'): {'MCP': 3, 'MCP_GPIO': 12},
                             (62, 'X'): {'MCP': 3, 'MCP_GPIO': 13},
                             (63, 'X'): {'MCP': 3, 'MCP_GPIO': 14},
                             (64, 'X'): {'MCP': 3, 'MCP_GPIO': 15}
}}

class Mux(MuxAbstract):
    def __init__(self, **kwargs):
        if 'id' in kwargs.keys():
            MUX_CONFIG.update(HARDWARE_CONFIG['mux']['boards'][kwargs['id']])
        kwargs.update({'board_name': os.path.basename(__file__).rstrip('.py')})
        if 'cabling' not in kwargs.keys() or kwargs['cabling']=={}:
            kwargs.update({'cabling': default_mux_cabling})
        if 'activation_delay' not in kwargs:
            kwargs.update({'activation_delay': MUX_CONFIG['activation_delay']})
        if 'release_delay' not in kwargs:
            kwargs.update({'release_delay': MUX_CONFIG['release_delay']})
        super().__init__(**kwargs)
        self.exec_logger.debug(f'configuration: {MUX_CONFIG}')
        tca_address = kwargs.pop('tca_address', 0x70)
        # tca_channel = kwargs.pop('tca_channel', 0)
        self._roles = kwargs.pop('roles', None)
        if self._roles is None:
            self._roles = {'A': 'X'}  # NOTE: defaults to 4-roles
        if np.alltrue([j in self._roles.values() for j in set([i[1] for i in list(inner_cabling['1_role'].keys())])]):
            self._mode = '1_role'
        else:
            self.exec_logger.error(f'Invalid role assignment for {self.board_name}: {self._roles} !')
            self._mode = ''
        self._tca = [adafruit_tca9548a.TCA9548A(self.ctl.bus, tca_address)[i] for i in np.arange(7,3,-1)]
        # self._mcp_addresses = (kwargs.pop('mcp', '0x20'))  # TODO: add assert on valid addresses..
        self._mcp = [None, None, None, None]
        self.reset()
        if self.addresses is None:
            self._get_addresses()
        self.exec_logger.debug(f'{self.board_id} addresses: {self.addresses}')

    def _get_addresses(self):
        """ Converts inner cabling addressing into (electrodes, role) addressing """
        ic = inner_cabling[self._mode]
        self.addresses = {}
        d = {}
        for k, v in self.cabling.items():
            d.update({k: ic[(v[0], self._roles[k[1]])]})
        self.addresses = d

    def reset(self):
        self._mcp[0] = MCP23017(self._tca[0])
        self._mcp[1] = MCP23017(self._tca[1])
        self._mcp[2] = MCP23017(self._tca[2])
        self._mcp[3] = MCP23017(self._tca[3])

    def switch_one(self, elec=None, role=None, state=None):
        MuxAbstract.switch_one(self, elec=elec, role=role, state=state)

        def activate_relay(mcp, mcp_pin, value=True):
            pin_enable = mcp.get_pin(mcp_pin)
            pin_enable.direction = Direction.OUTPUT
            pin_enable.value = value

        d = self.addresses[elec, role]
        if state == 'on':
            activate_relay(self._mcp[d['MCP']], d['MCP_GPIO'], True)
            # time.sleep(MUX_CONFIG['activation_delay'])  # NOTE: moved to MuxAbstract switch
        if state == 'off':
            activate_relay(self._mcp[d['MCP']], d['MCP_GPIO'], False)
            # time.sleep(MUX_CONFIG['release_delay'])  # NOTE: moved to MuxAbstract switch
