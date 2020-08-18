*****************************************
OhmPi V 1.01 (limited to 32 electrodes)
***************************************** 

The philosophy of Ohmpi 
****************************************** 
The philosophy of Ohmpi V1.01 is to offer a multi electrode resistivity meter, from a set of commercially available electronic cards it is a resistivity meter limited to 32 electrodes only. It is limited to low-current injection, but suitable for small laboratory experiments and small field time monitoring



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

.. figure:: measurement_board.jpg
   :width: 800px
   :align: center
   :height: 400px
   :alt: alternate text
   :figclass: align-center

   Measurement circuit board assembly: a) printed circuit board, b) adding the 1-Kohm resistors ± 1%, c)adding the 1.5-Kohm resistors ± 1%, d) adding the black female 1 x 10 header and the 7-blue screw terminal block(2 pin, 3.5-mm pitch), e) adding the 50-ohm reference resistor ± 0.1%, and f) adding the ADS1115 and the LM358N low-power dual operational amplifiers
   
.. figure:: measurement_board-2.jpg
   :width: 800px
   :align: center
   :height: 700px
   :alt: alternate text
   :figclass: align-center
   
   Measurement board installation with Raspberry Pi
   
Current injection 
******************

To carry out the electrical resistivity measurement, the first step consists of injecting current into the ground.
In our case, a simple 12-V lead-acid battery is used to create an electrical potential difference that results 
in current circulating into the ground. The current is injected through electrodes A and B (see Fig. 2). This 
injection is controlled via a 4-channel relay module board connected to the Raspberry Pi. The mechanical relay
module board is shown in Figure 4. Relays 1 and 2 serve to switch on the current source. The common contacts 
of relays 1 and 2 are connected to the positive and negative battery poles, respectively. The normally open 
contacts of both relays are connected to the common contacts of relays 3 and 4. Relays 1 and 2 are connected 
to the GPIO 7 on the Raspberry Pi and therefore activate simultaneously. The role of relays 3 and 4 is to reverse 
the polarity at electrodes A and B. Thus, when relays 3 and 4 are energized by the GPIO 8 in the open position, 
the positive battery pole is connected to electrode A and the negative pole to electrode B. When not energized, 
they remain in the normally closed position. This set-up offers a simple and robust solution to inject current.

.. figure:: current_board.jpg
   :width: 800px
   :align: center
   :height: 400px
   :alt: alternate text
   :figclass: align-center
   
   Wiring of the 4-channel relay module board for current injection management
   
Electrical resistivity measurements
************************************   

To measure electrical resistivity with Raspberry Pi, an ADS1115 was introduced, as proposed by Florsch [7]. The ADS1115 is a 16-bit ADC (Analog-to-Digital Converter), with an adaptable gain. Its value has been set at 1 in this study. The input signal value could lie between - to + 6.114 V. The ADS1115 is mounted on a board adapted from an in-house design. Figure 5 shows the general diagram for the electronic measurement board developed. This figure also displays the test circuit used to test the board in the laboratory, which mimics the behavior of a soil subjected to current injection. In this test circuit, resistance R11 represents the soil resistance.
Soil resistance R11 is connected to electrodes A and B for the current injection. Resistors R10 and R12 constitute the contact resistances between soil and electrodes; they are typically made of stainless steel. The battery, which allows for direct current injection, is connected in series with resistors R10, R11 and R12. In this part of the board, resistance R9 has been added to measure the current flowing between electrodes A and B. This resistance value has been set at 50 ohms in order to ensure:
•	a precise resistance,
•	a resistance less than the sum of resistors R10, R11 and R12; indeed, R10 and R12 generally lie between 100 and 5,000 ohms.
To measure the current intensity between A and B, the electrical potential difference at the pole of the reference resistor (R9) is measured. The intensity (in mA) is calculated by inserting the resulting value into the following: ?
To measure the potential difference needed to measure current intensity, the ADS 1115 is connected to the ground of the circuit. In our case, the ground reference is electrode B. The analog inputs A1 and A0 of the ADS1115 are connected to each pole of the reference resistor (R9). In order to increase input impedance and adapt the signal gain, tracking amplifiers have been included and completed by a divider bridge (R5, R8, R6 and R7) located between the two amplifiers. The resistance of the divider bridge ensures that the signal remains between 0 and 5 V, in accordance with the ADS1115 signal gain. To measure the potential difference, the M and N electrodes are connected to analog inputs A2 and A3 of the ADS 1115. Between the ADC and the electrodes, two tracking amplifiers and a divider bridge have been positioned so as to obtain a potential lying within the 0-5 V range at the analog input of the ADS 1115.
Let's note that the potential difference value would equal the potential measured with ADS1115 multiplied by the voltage reduction value of the divider bridge (see Section 5.2). Despite the use of high-resolution resistance (i.e. accurate to within 1%), it is still necessary to calibrate the divider bridge using a precision voltmeter. For this purpose, the input and output potentials of the divider bridge must be measured using an equivalent circuit for various electrical potential values. These values serve to calculate the gain. With this electronic board, it is possible to measure the potential and intensity without disturbing the electric field in the ground, with the total input impedance value being estimated at 36 mega-ohms.
A shortcut between Electrodes A and B will generate excessive currents, whose intensities depend on the type of battery used. A lithium ion battery or automobile-type lead-acid battery can deliver a strong enough current to damage the board and, as such, constitutes a potential hazard. We therefore recommend adding a 1.5-A fuse between the battery and resistor R9.

.. figure:: schema_measurement_board.jpg
   :width: 800px
   :align: center
   :height: 400px
   :alt: alternate text
   :figclass: align-center
   
   Measurement board
   
Multiplexer implentation
*************************
The resistivity measurement is conducted on four terminals (A, B, M and N). The user could perform each measurement 
by manually plugging four electrodes into the four channel terminals. In practice, ERT requires several tens or thousands 
of measurements conducted on different electrode arrays. A multiplexer is therefore used to connect each channel to one of 
the 32 electrodes stuck into the ground, all of which are connected to the data logger.


We will describe below how to assemble the four multiplexers (MUX), one per terminal. 
A multiplexer consists of 2 relay modules with 16 channels each. On the first board, on each MUX, 15 relays out of the 16 available will be used. Please note that the suggested configuration enables making smaller multiplexers (8 or 16 electrodes only). On the other hand, if you prefer upping to 64 electrodes, which is entirely possible, a GPIO channel multiplier will have to be used. To prepare the multiplexer, the channels of the two relay boards must be connected according to the wiring diagram shown in Figure 11. For this purpose, 0.5-mm² cables with end caps are used and their length adjusted for each connection in order to produce a clean assembly. The length was adjusted so that the distance between the two points to be connected could be directly measured on the board once they had been assembled one above the other, in adding an extra 3 cm. The wires at the ends need to be stripped and the end caps added. As a final step, connect the cables to the correct connectors. This operation must be repeated in order to carry out all the wiring shown in Figure 11.

 