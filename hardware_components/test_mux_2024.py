from OhmPi.hardware_components.mux_2024_rev_0_0 import Mux, MUX_CONFIG
import time

mux = Mux()
mux.switch_one(elec=1, role='M', state='on')
time.sleep(2)
mux.switch_one(elec=1, role='M', state='off')
