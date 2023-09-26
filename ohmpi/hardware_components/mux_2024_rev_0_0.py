from ohmpi.config import HARDWARE_CONFIG
import os
import numpy as np
from ohmpi.hardware_components import MuxAbstract
import adafruit_tca9548a  # noqa
from adafruit_mcp230xx.mcp23017 import MCP23017  # noqa
from digitalio import Direction  # noqa
from busio import I2C
# import time

# hardware characteristics and limitations
SPECS = {'voltage_max': 50., 'current_max': 3., 'activation_delay': 0.01, 'release_delay': 0.005}

# defaults to 4 roles cabling electrodes from 1 to 8
default_mux_cabling = {(elec, role) : ('mux_1', elec) for role in ['A', 'B', 'M', 'N'] for elec in range(1,9)}

inner_cabling = {'4_roles' : {(1, 'X'): {'MCP': 0, 'MCP_GPIO': 0}, (1, 'Y'): {'MCP': 0, 'MCP_GPIO': 8},
                             (2, 'X'): {'MCP': 0, 'MCP_GPIO': 1}, (2, 'Y'): {'MCP': 0, 'MCP_GPIO': 9},
                             (3, 'X'): {'MCP': 0, 'MCP_GPIO': 2}, (3, 'Y'): {'MCP': 0, 'MCP_GPIO': 10},
                             (4, 'X'): {'MCP': 0, 'MCP_GPIO': 3}, (4, 'Y'): {'MCP': 0, 'MCP_GPIO': 11},
                             (5, 'X'): {'MCP': 0, 'MCP_GPIO': 4}, (5, 'Y'): {'MCP': 0, 'MCP_GPIO': 12},
                             (6, 'X'): {'MCP': 0, 'MCP_GPIO': 5}, (6, 'Y'): {'MCP': 0, 'MCP_GPIO': 13},
                             (7, 'X'): {'MCP': 0, 'MCP_GPIO': 6}, (7, 'Y'): {'MCP': 0, 'MCP_GPIO': 14},
                             (8, 'X'): {'MCP': 0, 'MCP_GPIO': 7}, (8, 'Y'): {'MCP': 0, 'MCP_GPIO': 15},
                             (1, 'XX'): {'MCP': 1, 'MCP_GPIO': 7}, (1, 'YY'): {'MCP': 1, 'MCP_GPIO': 15},
                             (2, 'XX'): {'MCP': 1, 'MCP_GPIO': 6}, (2, 'YY'): {'MCP': 1, 'MCP_GPIO': 14},
                             (3, 'XX'): {'MCP': 1, 'MCP_GPIO': 5}, (3, 'YY'): {'MCP': 1, 'MCP_GPIO': 13},
                             (4, 'XX'): {'MCP': 1, 'MCP_GPIO': 4}, (4, 'YY'): {'MCP': 1, 'MCP_GPIO': 12},
                             (5, 'XX'): {'MCP': 1, 'MCP_GPIO': 3}, (5, 'YY'): {'MCP': 1, 'MCP_GPIO': 11},
                             (6, 'XX'): {'MCP': 1, 'MCP_GPIO': 2}, (6, 'YY'): {'MCP': 1, 'MCP_GPIO': 10},
                             (7, 'XX'): {'MCP': 1, 'MCP_GPIO': 1}, (7, 'YY'): {'MCP': 1, 'MCP_GPIO': 9},
                             (8, 'XX'): {'MCP': 1, 'MCP_GPIO': 0}, (8, 'YY'): {'MCP': 1, 'MCP_GPIO': 8}},
                '2_roles':  # TODO: WARNING check 2_roles table, it has not been verified yet !!!
                            {(1, 'X'): {'MCP': 0, 'MCP_GPIO': 0}, (1, 'Y'): {'MCP': 0, 'MCP_GPIO': 8},
                             (2, 'X'): {'MCP': 0, 'MCP_GPIO': 1}, (2, 'Y'): {'MCP': 0, 'MCP_GPIO': 9},
                             (3, 'X'): {'MCP': 0, 'MCP_GPIO': 2}, (3, 'Y'): {'MCP': 0, 'MCP_GPIO': 10},
                             (4, 'X'): {'MCP': 0, 'MCP_GPIO': 3}, (4, 'Y'): {'MCP': 0, 'MCP_GPIO': 11},
                             (5, 'X'): {'MCP': 0, 'MCP_GPIO': 4}, (5, 'Y'): {'MCP': 0, 'MCP_GPIO': 12},
                             (6, 'X'): {'MCP': 0, 'MCP_GPIO': 5}, (6, 'Y'): {'MCP': 0, 'MCP_GPIO': 13},
                             (7, 'X'): {'MCP': 0, 'MCP_GPIO': 6}, (7, 'Y'): {'MCP': 0, 'MCP_GPIO': 14},
                             (8, 'X'): {'MCP': 0, 'MCP_GPIO': 7}, (8, 'Y'): {'MCP': 0, 'MCP_GPIO': 15},
                             (16, 'X'): {'MCP': 1, 'MCP_GPIO': 7}, (16, 'Y'): {'MCP': 1, 'MCP_GPIO': 15},
                             (15, 'X'): {'MCP': 1, 'MCP_GPIO': 6}, (15, 'Y'): {'MCP': 1, 'MCP_GPIO': 14},
                             (14, 'X'): {'MCP': 1, 'MCP_GPIO': 5}, (14, 'Y'): {'MCP': 1, 'MCP_GPIO': 13},
                             (13, 'X'): {'MCP': 1, 'MCP_GPIO': 4}, (13, 'Y'): {'MCP': 1, 'MCP_GPIO': 12},
                             (12, 'X'): {'MCP': 1, 'MCP_GPIO': 3}, (12, 'Y'): {'MCP': 1, 'MCP_GPIO': 11},
                             (11, 'X'): {'MCP': 1, 'MCP_GPIO': 2}, (11, 'Y'): {'MCP': 1, 'MCP_GPIO': 10},
                             (10, 'X'): {'MCP': 1, 'MCP_GPIO': 1}, (10, 'Y'): {'MCP': 1, 'MCP_GPIO': 9},
                             (9, 'X'): {'MCP': 1, 'MCP_GPIO': 0}, (9, 'Y'): {'MCP': 1, 'MCP_GPIO': 8}}
                }


class Mux(MuxAbstract):
    def __init__(self, **kwargs):
        kwargs.update({'board_name': os.path.basename(__file__).rstrip('.py')})
        kwargs.update({'cabling': kwargs.pop('cabling', default_mux_cabling)})
        kwargs.update({'activation_delay': max(kwargs.pop('activation_delay', SPECS['activation_delay']),
                                               SPECS['activation_delay'])})
        kwargs.update({'release_delay': max(kwargs.pop('release_delay', SPECS['release_delay']),
                                               SPECS['activation_delay'])})
        kwargs.update({'voltage_max': max(0., min(kwargs.pop('voltage_max', SPECS['voltage_max']),
                                                  SPECS['voltage_max']))})
        kwargs.update({'current_max': max(0., min(kwargs.pop('current_max', SPECS['current_max']),
                                                  SPECS['current_max']))})
        super().__init__(**kwargs)
        assert isinstance(self.io, I2C)
        self.exec_logger.debug(f'configuration: {kwargs}')
        tca_address = kwargs.pop('tca_address', None)
        tca_channel = kwargs.pop('tca_channel', 0)
        self._roles = kwargs.pop('roles', None)
        if self._roles is None:
            self._roles = {'A': 'X', 'B': 'Y', 'M': 'XX', 'N': 'YY'}  # NOTE: defaults to 4-roles
        if np.alltrue([j in self._roles.values() for j in set([i[1] for i in list(inner_cabling['4_roles'].keys())])]):
            self._mode = '4_roles'
        elif np.alltrue([j in self._roles.values() for j in set([i[1] for i in list(inner_cabling['2_roles'].keys())])]):
            self._mode = '2_roles'
        else:
            self.exec_logger.error(f'Invalid role assignment for {self.board_name}: {self._roles} !')
            self._mode = ''
        # self.io = self.ctl.connections[kwargs.pop('connection', ctl_connection)] -> to hardware_system
        if tca_address is None:
            self._tca = self.io
        else:
            self._tca = adafruit_tca9548a.TCA9548A(self.io, tca_address)[tca_channel]
        self._mcp_addresses = (kwargs.pop('mcp_0', '0x22'), kwargs.pop('mcp_1', '0x23'))  # TODO: add assert on valid addresses..
        self._mcp = [None, None]
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
        self._mcp[0] = MCP23017(self._tca, address=int(self._mcp_addresses[0], 16))
        self._mcp[1] = MCP23017(self._tca, address=int(self._mcp_addresses[1], 16))

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
