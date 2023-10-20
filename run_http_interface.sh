export PYTHONPATH=`pwd`
source $PYTHONPATH/ohmpy/bin/activate
python dev/start_mqtt_html.py &  # run ohmpi.py to capture the commands
python -m http.server  # run web GUI

