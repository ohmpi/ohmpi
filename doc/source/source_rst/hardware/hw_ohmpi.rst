.. warning::
    **OhmPi is a participative project open to all, it requires skills in electronics and to respect the safety rules. OhmPi must be assembled in a professional context and by people competent in electronics. The OhmPi team cannot be held responsible for any material or human damage which would be associated with the use or the assembly of OHMPI. The OhmPi team cannot be held responsible if the equipment does not work after assembly.**

*******************************************
Build your Ohmpi 
*******************************************

In previous sections, we described the various components that compose Ohmpi.
Today, version 1.0x is no longer maintained, but all boards from V2023 upwards are compatible with each other. This is the major innovation of 2024.
Depending on your needs and applications, you can choose the board you're going to use.


Recommanded configurations
******************************

+------------------------------+--------------------------------+--------------------+------------------------+--------------------------+------------------------+
|Applications                  |measurement Board               |Mux                 | RPI                    | Power supply             |Config file name        |
+------------------------------+--------------------------------+--------------------+------------------------+--------------------------+------------------------+
|4 electrodes-soil sample      |mb v2023                        |None                |Raspberry pi 3 Model B  | 12V BAtterie             |                        |
|laboratory (only Rhoa)        |                                |                    |                        |                          |                        |
+------------------------------+--------------------------------+--------------------+------------------------+--------------------------+------------------------+
|4 electrodes soil sample      |mb v2024                        |None                |Raspberry pi 3 Model B  | 12V BAtterie             |                        |
|laboratory (Rhoa and IP)      |                                |                    |                        |                          |                        |
+------------------------------+--------------------------------+--------------------+------------------------+--------------------------+------------------------+
|4 electrodes concrete sample  |mb v2024                        |None                |Raspberry pi 3 Model B  | DSP5005                  |                        |
|Laboratory (Rhoa and IP)      |                                |                    |                        |                          |                        |
+------------------------------+--------------------------------+--------------------+------------------------+--------------------------+------------------------+
|Less than 32 electrodes for   |mb v2024                        |Mux v2024           |Raspberry pi 4 Model B  | 12V Batterie             |                        |
|laboratory monitoring         |                                |                    |                        |                          |                        |
+------------------------------+--------------------------------+--------------------+------------------------+--------------------------+------------------------+
|Less than 32 electrodes for   |mb v2024                        |Mux v2024           |Raspberry pi 4 Model B  | DSP5005                  |                        |
|field monitoring              |                                |                    |                        |                          |                        |
+------------------------------+--------------------------------+--------------------+------------------------+--------------------------+------------------------+
|more than 64 electrodes for   |mb v2024                        |Mux v2023           |Raspberry pi 4 Model B  | DSP5005                  |                        |
|field monitoring              |                                |                    |                        |                          |                        |
+------------------------------+--------------------------------+--------------------+------------------------+--------------------------+------------------------+

Another possible combination is to use MUX v2023 with MUX v2024 together.

Examples of OHMPI assembly in different versions.


.. toctree:: 
   :maxdepth: 1 

   assemble_ohmpi/assembling_mb2023_MUX_2023_12V.rst
   assemble_ohmpi/assembling_mb2024_MUX_2023_dps5005.rst


