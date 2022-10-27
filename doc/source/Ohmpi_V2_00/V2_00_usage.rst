
.. warning::
	**Ohmpi is a participative project open to all, it requires skills in electronics and to respect the safety rules. Ohmpi must be assembled in a professional context and by people competent in electronics. The Ohmpi team cannot be held responsible for any material or human damage which would be associated with the use or the assembly of OHMPI. The Ohmpi team cannot be held responsible if the equipment does not work after assembly.**






**Usage** Interfaces and applications
****************************************************

Different interfaces can be used to communicated with the OhmPi.

*** Web interface ***

The raspberrypi of the OhmPi is used as a Wifi Access Point (AP) and run
a small webserver to serve the 'index.html' interface. Using a laptop or
a mobile phone connected to the wifi of the Raspberry Pi, one can see this
interface, upload sequence, change parameters, run sequence and download data.

To configure the Raspberry Pi to act as an access point and run
the webserver automatically on start, see instructions in 'runOnStart.sh'.

Once configure, the webserver should start by itself on start and once
connected to the Pi, the user can go to `10.3.141.1:8080<http://10.3.141.1:8080>`
 to access the interface.
 
 
TODO add screenshot of interface
 


*** Python interface***

By importing the `OhmPi` class from the ohmpi.py, one can controle the OhmPi using interactive IPython.
Typically, it involves using the Thonny on the Raspberry Pi or the Terminal. Once can also connect using 
ssh and run the Python interface (see PuTTY on Windows or ssh command on macOS/Linux).

To access the Python API, make sure the file ohmpi.py is in the same
directory as where you run the commands/script. The file ohmpi.py can
be found on the OhmPi gitlab repository. We recommend downloading the 
entire repository as ohmpi.py import other .py files and default configuration
files (.json and .py).


.. codeblock:: python
   :caption: Example of using the Python API to control OhmPi


   from ohmpi import OhmPi
   k = OhmPi(idps=True)  # if V3.0 make sure to set idps to True
   # the DPS5005 is used in V3.0 to inject higher voltage
   
   # default parameters are stored in the pardict argument
   # they can be manually changed
   k.pardict['injection_duration'] = 0.5  # injection time in seconds
   k.pardict['nb_stack'] = 1  # one stack is two half-cycles
   k.pardict['nbr_meas'] = 1  # number of time the sequence is repeated
   
   # without multiplexer, one can simple measure using
   out = k.run_measurement()
   # out contains information about the measurement and can be save as
   k.append_and_save('out.csv', out)
   
   # custom or adaptative argument (see help of run_measurement())
   k.run_measurement(nb_stack=4,  # do 4 stacks (8 half-cycles)
                     injection_duration=2,  # inject for 2 seconds
                     autogain=True,  # adapt gain of ADS to get good resolution
                     strategy='vmin',  # inject min voltage for Vab (v3.0)
                     tx_volt=5)  # vab for finding vmin or vab injectected
                     # if 'strategy' is 'constant'
   
   # if a multiplexer is connected, we can also manually switch it
   k.reset_mux()  # check that all mux are closed (do this FIRST)
   k.switch_mux_on([1, 4, 2, 3])
   k.run_measurement()
   k.switch_mux_off([1, 4, 2, 3])  # don't forget this! risk of short-circuit
   
   # import a sequence
   k.read_quad('sequence.txt')  # four columns, no header, space as separator
   print(k.sequence)  # where the sequence is stored
   
   # rs check
   k.rs_check()  # run an RS check (check contact resistances) for all
   # electrodes of the given sequence
   
   # run a sequence
   k.measure()  # measure accept same arguments as run_measurement()
   # NOTE: this is an asynchronous command that runs in a separate thread
   # after executing the command, the prompt will return immediately
   # the asynchronous thread can be stopped during execution using
   k.stop()
   # otherwise, it will exit by itself at the end of the sequence
   # if multiple measurement are to be taken, the sequence will be repeated
   


   
***MQTT interface***

Interface to communicate with the Pi designed for the Internet of Things (IoT).
   
