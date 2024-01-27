Hardware
********

This section contains the documentation needed to build an OhmPi.
The OhmPi is composed of different modules:

- a measurements board ('mb'): that measures the current and voltage and modulates modulate the injected current
- 0, 1, ... or n multiplexer boards ('mux'): that addresse different electrodes
- a power supply ('pwr'): either a 12V battery or a more advanced power supply where we can control the voltage/current
- a general controller ('ctrl'): to control the measurements board and power supply (=raspberrypi)

These module exists in different versions and can be combined using a configuration file.
You can then upgrade your measurment board or power supply for specific applications.

.. toctree:: 
   :maxdepth: 2 

   hardware/hw_info
   hardware/mb
   hardware/mux
   hardware/hw_pwr
   hardware/hw_rpi
   hardware/assembling_mb2023_MUX_2023_12V
   hardware/assembling_mb2024_MUX_2023_dps5005.rst

  
