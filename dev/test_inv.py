
#
from ohmpi.utils import change_config
change_config('../configs/config_mb_2023.py', verbose=False)

from ohmpi.ohmpi import OhmPi
k = OhmPi()
k.run_inversion(['measurement_20220206T194552.csv'])


# restore default config
change_config('../configs/config_default.py', verbose=False)
