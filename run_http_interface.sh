#!bin/bash
export PYTHONPATH=/home/$USER/OhmPi
cd /home/$USER/OhmPi
source /home/$USER/OhmPi/ohmpy/bin/activate
python dev/start_mqtt_html.py &  # run ohmpi.py to capture the commands
python3 -m http.server  # run web GUI

