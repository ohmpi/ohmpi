import os
import numpy as np
import datetime
from ohmpi.hardware_components import MuxAbstract
import adafruit_tca9548a  # noqa
from adafruit_mcp230xx.mcp23017 import MCP23017  # noqa
from digitalio import Direction  # noqa
from busio import I2C  # noqa
from ohmpi.utils import enforce_specs

# TODO: manage the case when a tca is added to handle more mux_2023 boards

# hardware characteristics and limitations
SPECS = {'model': {'default': os.path.basename(__file__).rstrip('.py')},
         'id': {'default': 'mux_??'},
         'voltage_max': {'default': 50.},
         'current_max': {'default': 3.},
         'activation_delay': {'default': 0.01},
         'release_delay': {'default': 0.005},
         'mux_tca_address': {'default': 0x70},
         # 'i2c_ext_tca_address': {'default': None},
         # 'i2c_ext_tca_channel': {'default': 0},
         }

# defaults to role 'A' cabling electrodes from 1 to 64
default_mux_cabling = {(elec, role): ('mux_1', elec) for role in ['A'] for elec in range(1, 64)}

inner_cabling = {'1_role': {(1, 'X'): {'MCP': 0, 'MCP_GPIO': 0}, (2, 'X'): {'MCP': 0, 'MCP_GPIO': 1},
                            (3, 'X'): {'MCP': 0, 'MCP_GPIO': 2}, (4, 'X'): {'MCP': 0, 'MCP_GPIO': 3},
                            (5, 'X'): {'MCP': 0, 'MCP_GPIO': 4}, (6, 'X'): {'MCP': 0, 'MCP_GPIO': 5},
                            (7, 'X'): {'MCP': 0, 'MCP_GPIO': 6}, (8, 'X'): {'MCP': 0, 'MCP_GPIO': 7},
                            (9, 'X'): {'MCP': 0, 'MCP_GPIO': 8}, (10, 'X'): {'MCP': 0, 'MCP_GPIO': 9},
                            (11, 'X'): {'MCP': 0, 'MCP_GPIO': 10}, (12, 'X'): {'MCP': 0, 'MCP_GPIO': 11},
                            (13, 'X'): {'MCP': 0, 'MCP_GPIO': 12}, (14, 'X'): {'MCP': 0, 'MCP_GPIO': 13},
                            (15, 'X'): {'MCP': 0, 'MCP_GPIO': 14}, (16, 'X'): {'MCP': 0, 'MCP_GPIO': 15},
                            (17, 'X'): {'MCP': 1, 'MCP_GPIO': 0}, (18, 'X'): {'MCP': 1, 'MCP_GPIO': 1},
                            (19, 'X'): {'MCP': 1, 'MCP_GPIO': 2}, (20, 'X'): {'MCP': 1, 'MCP_GPIO': 3},
                            (21, 'X'): {'MCP': 1, 'MCP_GPIO': 4}, (22, 'X'): {'MCP': 1, 'MCP_GPIO': 5},
                            (23, 'X'): {'MCP': 1, 'MCP_GPIO': 6}, (24, 'X'): {'MCP': 1, 'MCP_GPIO': 7},
                            (25, 'X'): {'MCP': 1, 'MCP_GPIO': 8}, (26, 'X'): {'MCP': 1, 'MCP_GPIO': 9},
                            (27, 'X'): {'MCP': 1, 'MCP_GPIO': 10}, (28, 'X'): {'MCP': 1, 'MCP_GPIO': 11},
                            (29, 'X'): {'MCP': 1, 'MCP_GPIO': 12}, (30, 'X'): {'MCP': 1, 'MCP_GPIO': 13},
                            (31, 'X'): {'MCP': 1, 'MCP_GPIO': 14}, (32, 'X'): {'MCP': 1, 'MCP_GPIO': 15},
                            (33, 'X'): {'MCP': 2, 'MCP_GPIO': 0}, (34, 'X'): {'MCP': 2, 'MCP_GPIO': 1},
                            (35, 'X'): {'MCP': 2, 'MCP_GPIO': 2}, (36, 'X'): {'MCP': 2, 'MCP_GPIO': 3},
                            (37, 'X'): {'MCP': 2, 'MCP_GPIO': 4}, (38, 'X'): {'MCP': 2, 'MCP_GPIO': 5},
                            (39, 'X'): {'MCP': 2, 'MCP_GPIO': 6}, (40, 'X'): {'MCP': 2, 'MCP_GPIO': 7},
                            (41, 'X'): {'MCP': 2, 'MCP_GPIO': 8}, (42, 'X'): {'MCP': 2, 'MCP_GPIO': 9},
                            (43, 'X'): {'MCP': 2, 'MCP_GPIO': 10}, (44, 'X'): {'MCP': 2, 'MCP_GPIO': 11},
                            (45, 'X'): {'MCP': 2, 'MCP_GPIO': 12}, (46, 'X'): {'MCP': 2, 'MCP_GPIO': 13},
                            (47, 'X'): {'MCP': 2, 'MCP_GPIO': 14}, (48, 'X'): {'MCP': 2, 'MCP_GPIO': 15},
                            (49, 'X'): {'MCP': 3, 'MCP_GPIO': 0}, (50, 'X'): {'MCP': 3, 'MCP_GPIO': 1},
                            (51, 'X'): {'MCP': 3, 'MCP_GPIO': 2}, (52, 'X'): {'MCP': 3, 'MCP_GPIO': 3},
                            (53, 'X'): {'MCP': 3, 'MCP_GPIO': 4}, (54, 'X'): {'MCP': 3, 'MCP_GPIO': 5},
                            (55, 'X'): {'MCP': 3, 'MCP_GPIO': 6}, (56, 'X'): {'MCP': 3, 'MCP_GPIO': 7},
                            (57, 'X'): {'MCP': 3, 'MCP_GPIO': 8}, (58, 'X'): {'MCP': 3, 'MCP_GPIO': 9},
                            (59, 'X'): {'MCP': 3, 'MCP_GPIO': 10}, (60, 'X'): {'MCP': 3, 'MCP_GPIO': 11},
                            (61, 'X'): {'MCP': 3, 'MCP_GPIO': 12}, (62, 'X'): {'MCP': 3, 'MCP_GPIO': 13},
                            (63, 'X'): {'MCP': 3, 'MCP_GPIO': 14}, (64, 'X'): {'MCP': 3, 'MCP_GPIO': 15}
                            }
                 }


class Mux(MuxAbstract):
    def __init__(self, **kwargs):
        if 'model' not in kwargs.keys():
            for key in SPECS.keys():
                kwargs = enforce_specs(kwargs, SPECS, key)
            subclass_init = False
        else:
            subclass_init = True
        super().__init__(**kwargs)
        if not subclass_init:
            self.exec_logger.event(f'{self.model}: {self.board_id}\tmux_init\tbegin\t{datetime.datetime.utcnow()}')

        self._connection = kwargs['connection']
        self.connection = None
        assert isinstance(self._connection, I2C)
        self.exec_logger.debug(f'configuration: {kwargs}')
        kwargs.update({'roles': kwargs.pop('roles', None)})
        roles = kwargs['roles']

        if roles is None:
            roles = ['A'] # NOTE: defaults to 1-role
        elif isinstance(roles, str):
            roles = [roles]
        if isinstance(roles, dict): # roles if config are already formatted as {'A':'X'}
            self._roles = roles
        else:
            self._roles = {roles[0]:'X'}
        if np.alltrue([j in self._roles.values() for j in set([i[1] for i in list(inner_cabling['1_role'].keys())])]):
            self._mode = '1_role'
        else:
            self.exec_logger.error(f'Invalid role assignment for {self.model}: {self._roles} !')
            self._mode = ''
        kwargs.update({'cabling': kwargs.pop('cabling', None)})
        cabling = kwargs['cabling']
        kwargs.update({'electrodes': kwargs.pop('electrodes', None)})
        electrodes = kwargs['electrodes']
        self.cabling = {}
        if cabling is None:
            self.cabling = {(e, r): (i + 1, r) for r in roles for i, e in enumerate(electrodes)}
        else:
            for k, v in cabling.items():
                if v[0] == self.board_id:
                    self.cabling.update({k: (v[1], k[1])})
            electrodes = [k[0] for k in self.cabling.keys()]
        self.electrodes = np.array(electrodes)

        self._tca_address = kwargs['mux_tca_address']
        self._tca_channels = [i for i in np.arange(7, 3, -1)]
        kwargs.update({'i2c_ext_tca_address': kwargs.pop('i2c_ext_tca_address', None)})
        self._i2c_ext_tca_address = kwargs['i2c_ext_tca_address']
        kwargs.update({'i2c_ext_tca_channel': kwargs.pop('i2c_ext_tca_channel', 0)})
        self._i2c_ext_tca_channel = kwargs['i2c_ext_tca_channel']
        self._mcp_addresses = ['0x20'] * 4  # TODO: add assert on valid addresses..
        self._i2c_ext_tca = None
        self._tca = None
        self._mcp = [None, None, None, None]
        if self.connect:
            try:
                self.reset_i2c_ext_tca()
                self.reset_tca()
                self.reset()
                self.soh_logger.info(f'TCA9548A ({hex(self._tca_address)})...OK')
            except Exception as e:
                self.soh_logger.info(f'TCA9548A ({hex(self._tca_address)})...NOT FOUND')

        self.specs = kwargs
        if self.addresses is None:
            self._get_addresses()
        self.exec_logger.debug(f'{self.board_id} addresses: {self.addresses}')
        if not subclass_init:
            self.exec_logger.event(f'{self.model}: {self.board_id}\tmux_init\tend\t{datetime.datetime.utcnow()}')

    def _get_addresses(self):
        """ Converts inner cabling addressing into (electrodes, role) addressing """
        ic = inner_cabling[self._mode]
        self.addresses = {}
        d = {}
        for k, v in self.cabling.items():
            d.update({k: ic[(v[0], self._roles[k[1]])]})
        self.addresses = d

    def reset(self):
        if self._tca is None:
            self.reset_i2c_ext_tca()
            self.reset_tca()
        try:
            self._mcp[0] = MCP23017(self._tca[0])
            self.soh_logger.info(f'MCP23017 ')
        except Exception as e:
            pass

        self._mcp[1] = MCP23017(self._tca[1])
        self._mcp[2] = MCP23017(self._tca[2])
        self._mcp[3] = MCP23017(self._tca[3])

    def reset_one(self, which=0):
        self._mcp[which] = MCP23017(self._tca[which])

    def reset_i2c_ext_tca(self):
        if self._i2c_ext_tca_address is None:
            self.connection = self._connection
        else:
            self.connection = adafruit_tca9548a.TCA9548A(self._connection, self._i2c_ext_tca_address)[self._i2c_ext_tca_channel]

    def reset_tca(self):
        if self.connection is None:
            self.reset_i2c_ext_tca()
        self._tca = [adafruit_tca9548a.TCA9548A(self.connection, self._tca_address)[tca_channel] for tca_channel in self._tca_channels]

    def switch_one(self, elec=None, role=None, state=None):
        MuxAbstract.switch_one(self, elec=elec, role=role, state=state)

        def activate_relay(mcp, mcp_pin, value=True):
            pin_enable = mcp.get_pin(mcp_pin)
            pin_enable.direction = Direction.OUTPUT
            pin_enable.value = value

        d = self.addresses[elec, role]
        if state == 'on':
            activate_relay(self._mcp[d['MCP']], d['MCP_GPIO'], True)
        if state == 'off':
            activate_relay(self._mcp[d['MCP']], d['MCP_GPIO'], False)
