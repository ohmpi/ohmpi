**************
OhmPi V 1.01 
************** 

OS installation on a Raspberry Pi 
****************************************** 

The first step is to start up the Raspberry Pi board, including installation of an OS (operating system). 
For this step, the installation instructions are well described on the Raspberry website 
https://www.raspberrypi.org/help/noobs-setup/2/). The authors recommend installing the latest 
stable and complete version of Raspbian by using NOOBS (a simple-to-use operating system installer). 
Once the OS has been installed, the 1-wire option and GPIO remote option must be deactivated via the
Raspbian GUI settings menu. Failure to carry out this task may cause damage to the relay shield cards during measurements.


Construction of the measurement board and connection to the Raspberry 
************************************************************************** 
The measurement board must be printed using the PCB file (Source file repository), with components soldered onto it by following the steps described below and illustrated in the following figure :


* Step no. 1: installation of the 1-Kohm resistors with an accuracy of ± 1%. 
* Step no. 2: installation of the 1.5-Kohm resistors with an accuracy of ± 1%. 
* Step no. 3: installation of both the black female 1 x 10 header and the 7-blue screw terminal blocks 
* Step no. 4: installation of the 50-Ohm reference resistor ± 0.1% 
* Step no. 5: addition of both the ADS115 directly onto the header (pins must be plugged according to the figure) and the LM358N operational amplifiers (pay attention to the direction).

1-Kohm and 1.5-Kohm resistors apply to the divider bridge. If, for example, you prefer using a weaker or stronger power supply, it would be possible to adjust the divider bridge value by simply modifying these resistors. Once all the components have been soldered together, the measurement board can be connected to the Raspberry Pi and the battery terminal, according to Figure 9. Between the battery and the TX+ terminal of the measurement board, remember to place a fuse holder with a 1.5-A fuse for safety purposes.
