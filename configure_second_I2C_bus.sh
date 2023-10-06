sudo apt-get install -y i2c-tools
echo -e "[all]\ndtoverlay=i2c-gpio,bus=4,i2c_gpio_delay_us=1,i2c_gpio_sda=22,i2c_gpio_scl=23" | sudo tee -a /boot/config.txt
