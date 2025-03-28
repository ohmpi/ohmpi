#!/bin/bash

echo "=========== OhmPi installation script v1.0.0 =========="

echo "--------- Installing additional libraries via apt --------"

# ensure that the libatlas-base-dev library is installed
sudo apt-get install -y libatlas-base-dev libopenblas-dev python3-dev libjpeg-dev zlib1g-dev libpng-dev

echo "----------- Creating virtual python environment ----------"

# Create the virtual environment
python3 -m venv ohmpy

# Activate it
source ohmpy/bin/activate || exit 1  # NOTE: Added || exit to avoid installing requirements in system python if the virtual environment can't be loaded

# Solve issues associated to storage allocation
export CFLAGS=-fcommon

# install all required packages in the virtual environment.
pip install -r requirements.txt

echo "----------- Setting RPi parameters (I2C, GPIO, ...) --------"

# enable I2C
sudo raspi-config nonint do_i2c 0

# install a second i2c bus
sudo apt-get install -y i2c-tools
echo "Setting up second I2C bus for old RPi OS versions... This might not work for newer RPi OS versions..."
echo -e "[all]\ndtoverlay=i2c-gpio,bus=4,i2c_gpio_delay_us=1,i2c_gpio_sda=22,i2c_gpio_scl=23" | sudo tee -a /boot/config.txt
echo "Setting up second I2C bus for newer RPi OS versions... This might not work for older RPi OS versions..."
echo -e "[all]\ndtoverlay=i2c-gpio,bus=4,i2c_gpio_delay_us=1,i2c_gpio_sda=22,i2c_gpio_scl=23" | sudo tee -a /boot/firmware/config.txt

echo "-------------- Install local MQTT broker --------------"

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

# create default password for mqtt user
echo -e "\n${txtgrn}>>> Creating default MQTT user and password...${txtdef}"
echo "mqtt_user:mqtt_password" | sudo tee -a "/etc/mosquitto/pwfile.txt"
sudo mosquitto_passwd -U /etc/mosquitto/pwfile.txt

echo -e "\n${txtgrn}>>> Updating configuration to allow anonymous remote connections and websockets...${txtdef}"
echo "listener 1883" | sudo tee -a /etc/mosquitto/mosquitto.conf
echo "listener 9001" | sudo tee -a /etc/mosquitto/mosquitto.conf
echo "protocol websockets" | sudo tee -a /etc/mosquitto/mosquitto.conf
echo "socket_domain ipv4" | sudo tee -a /etc/mosquitto/mosquitto.conf
echo "allow_anonymous false" | sudo tee -a /etc/mosquitto/mosquitto.conf
echo "password_file /etc/mosquitto/pwfile.txt" | sudo tee -a /etc/mosquitto/mosquitto.conf
echo -e "\n${txtgrn}>>> Current configuration stored in /etc/mosquitto/mosquitto.conf is displayed below${txtdef}" 

echo "adding a symbolic link to data" | ln -s ./ohmpi/data data
echo "adding symbolic links to logs" | ln -s ./ohmpi/logs logs

cat /etc/mosquitto/mosquitto.conf

echo "------------- Create config.py file -----------"

python setup_config.py

echo "---------- RESTARTING is recommended to use the web interface ----------"
