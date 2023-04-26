import time
from utils import change_config
change_config('config_ohmpi_card_3_15.py', verbose=False)
from OhmPi.hardware_components.mux_2024_rev_0_0 import Mux, MUX_CONFIG
from OhmPi.hardware_components import raspberry_pi as controller_module

MUX_CONFIG['controller'] = controller_module.Controller()
mux = Mux(**MUX_CONFIG)
mux.switch_one(elec=1, role='M', state='on')
time.sleep(2)
mux.switch_one(elec=1, role='M', state='off')
change_config('config_default.py', verbose=False)
