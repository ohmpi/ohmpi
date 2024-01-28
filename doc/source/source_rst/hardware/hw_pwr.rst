.. warning::
    **OhmPi is a participative project open to all, it requires skills in electronics and to respect the safety rules. OhmPi must be assembled in a professional context and by people competent in electronics. The OhmPi team cannot be held responsible for any material or human damage which would be associated with the use or the assembly of OHMPI. The OhmPi team cannot be held responsible if the equipment does not work after assembly.**


Power supply
****************************

Two sources of power are available now:
- a 12V battery
- a regulated power supply (DPS5005)

12V battery
=================
When injecting, we actually connect the + and - of the battery to the A, B electrodes.
Hence, we can only inject 12V maximum. 


Digital power supply (DPH5005)
========================================
This alimentation enables us to inject up to 50 V and also to regulate the current.
It needs to be connected to a 12V battery and can be controlled using `modbus` by the raspberrypi.


.. figure:: ../../img/DPH_5005.png       
       :width: 400px
       :align: center
       :height: 300px
       :alt: DPH-5005 image
       :figclass: align-center 

To assemble DPS 5005, please follow the links:
 `DPH 5005 manuel <https://joy-it.net/files/files/Produkte/JT-DPH5005/JT-DPH5005-Manual.pdf>`_

 `DPH 5005 case manuel <https://joy-it.net/files/files/Produkte/JT-DPS-Case/JT-DPS-Case-Manual_20200220.pdf>`_

.. warning::
    **Only use DPS 5005 with the measurement board V2024
