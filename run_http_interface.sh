#!bin/bash
#USER="pi"  # change if other username
cd /home/$USER/OhmPi
source /home/$USER/OhmPi/ohmpy/bin/activate
python ohmpi.py &  # run ohmpi.py to capture the commands
python http_interface.py  # run http_interface to serve the web GUI

