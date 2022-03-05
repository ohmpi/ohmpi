sudo apt update && sudo apt upgrade
sudo apt install -y mosquitto mosquitto-clients
sudo systemctl enable mosquitto.service
echo "Broker is intalled. Starting now..."
mosquitto -v
 
