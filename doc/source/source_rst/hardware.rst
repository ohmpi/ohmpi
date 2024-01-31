.. warning::
    **OhmPi is a participative project open to all, it requires skills in electronics and to respect the safety rules. OhmPi must be assembled in a professional context and by people competent in electronics. The OhmPi team cannot be held responsible for any material or human damage which would be associated with the use or the assembly of OHMPI. The OhmPi team cannot be held responsible if the equipment does not work after assembly.**


Hardware
********

This section contains the documentation needed to build an OhmPi.
The OhmPi is composed of different modules:

- a measurements board (``mb``): that measures the current and voltage and modulates the injected current
- 0, 1, ... or n multiplexer boards (``mux``): that address different electrodes
- a power supply (``pwr``): either a 12V battery or a more advanced power supply where we can control the voltage/current
- a general controller (``ctrl``): to control the measurement board, multiplexer boards and power supply (=raspberrypi)

These module exists in different versions and can be combined using a configuration file.
You can then upgrade your measurement board or power supply for specific applications.

.. toctree:: 
   :maxdepth: 2 

   hardware/hw_info
   hardware/hw_mb
   hardware/hw_mux
   hardware/hw_pwr
   hardware/hw_rpi
   hardware/hw_ohmpi


  
