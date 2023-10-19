#!/bin/bash

# ensure that the libatlas-base-dev library is installed
sudo apt-get install -y libatlas-base-dev libopenblas-dev

# Create the virtual environment
python3 -m venv ohmpy

# Activate it
source ohmpy/bin/activate || exit 1  # NOTE: Added || exit to avoid installing requirements in system python if the virtual environment can't be loaded

# Solve issues associated to storage allocation
export CFLAGS=-fcommon

# install all required packages in the virtual environment.
pip install -r requirements.txt

# install a second i2c bus
sudo apt-get install -y i2c-tools
echo -e "[all]\ndtoverlay=i2c-gpio,bus=4,i2c_gpio_delay_us=1,i2c_gpio_sda=22,i2c_gpio_scl=23" | sudo tee -a /boot/config.txt

# install local mqtt broker
txtred='\e[0;31m' # Red
txtgrn='\e[0;32m' # Green
txtylw='\e[0;33m' # Yellow
txtdef='\e[0;0m'  # Default

echo -e "${txtgrn}>>> Updating system and installing MQTT broker...${txtdef}"
sudo apt install -y mosquitto mosquitto-clients
sudo systemctl enable mosquitto.service

echo -e "\n${txtgrn}>>> Broker is installed. Starting now...${txtdef}"
mosquitto -v 

echo -e "\n${txtgrn}>>> Updating configuration to allow anonymous remote connections...${txtdef}"
echo "listener 1883" | sudo tee -a /etc/mosquitto/mosquitto.conf
echo "allow_anonymous true" | sudo tee -a /etc/mosquitto/mosquitto.conf
echo -e "\n${txtgrn}>>> Current configuration stored in /etc/mosquitto/mosquitto.conf is displayed below${txtdef}" 
cat /etc/mosquitto/mosquitto.conf
echo -e "\n${txtylw}>>> Adapt it according to your needs!${txtdef}\n"
