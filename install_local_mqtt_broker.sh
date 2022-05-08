txtred='\e[0;31m' # Red
txtgrn='\e[0;32m' # Green
txtylw='\e[0;33m' # Yellow
txtdef='\e[0;0m'  # Default

echo -e "${txtgrn}>>> Updating system and installing MQTT broker...${txtdef}"
sudo apt update && sudo apt upgrade
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

