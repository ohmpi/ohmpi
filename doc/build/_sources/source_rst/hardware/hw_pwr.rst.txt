Power supply
****************************

Two sources of power are available now:
- a 12V battery
- a regulated power supply (DPS5005)

12V battery
=================
When injecting, we actually connect the + and - of the battery to the A, B electrodes.
Hence, we can only inject 12V maximum.


Regulated power supply (DPS5005)
========================================
This alimentation enables us to inject up to 50 V and also to regulate the current.
It needs to be connected to a 12V battery and can be controlled using `modbus` by the raspberrypi.
