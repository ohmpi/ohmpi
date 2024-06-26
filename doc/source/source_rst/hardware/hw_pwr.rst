.. warning::
    **OhmPi is a participative project open to all, it requires skills in electronics and to respect the safety rules. OhmPi must be assembled in a professional context and by people competent in electronics. The OhmPi team cannot be held responsible for any material or human damage which would be associated with the use or the assembly of OHMPI. The OhmPi team cannot be held responsible if the equipment does not work after assembly.**


Power supply
****************************

Two sources of power are available now:

- a 12V battery
- a regulated power supply (DPH5005)

12V battery
=================
When injecting, we actually connect the + and - of the battery to the A, B electrodes.
Hence, we can only inject 12V maximum. 

With the measurement board v2024, you can connect the Tx battery following the schematic below.

.. figure:: ../../img/pwr-battery.jpg
    :alt: wiring battery with mb2024
    :figclass: align-center


Digital power supply (DPH5005)
========================================
This alimentation enables us to inject up to 50 V and also to regulate the current.
It needs to be connected to a 12V battery and can be controlled using `modbus` by the raspberrypi.


.. figure:: ../../img/DPH_5005.png       
       :width: 400px
       :align: center
       :height: 300px
       :alt: DPH5005 image
       :figclass: align-center 

To assemble DPH5005, please follow the links:
 `DPH5005 manual <https://joy-it.net/files/files/Produkte/JT-DPH5005/JT-DPH5005-Manual.pdf>`_

 `DPH5005 case manual <https://joy-it.net/files/files/Produkte/JT-DPS-Case/JT-DPS-Case-Manual_20200220.pdf>`_

.. Note::
    **Change the Baudrate from 9600 to 19200**, press and maintain **SET**, and start DPH5005, you acces to a new menu change **BAUD** 


.. warning::
    **Only use DPH5005 with the measurement board v2024**

.. warning::
    **We sometimes refer to DPS (Digital Power Supply) as a general power supply different from the 12V battery. But this DOES NOT refer to the DPS5005 component (step down DC/DC). The component used in the documentation is the DPH5005 (boost DC/DC converter).**

Make sure to follow the setup as below (also to be seen in the assembly guide). The DPH5005 needs to be after the two relays of the measurement.

.. figure:: ../../img/pwr-dph5005.jpg
    :alt: wiring of DPH5005
    :figclass: align-center


Charging the batteries
======================

It is not recommended to measure with the OhmPi when the Rx or Tx battery is charging (from solar panel or the grid).
Indeed, the charger can introduce electronic noise (50/60 Hz) but also perturb the stabilisation of the DPH5005 that will have a harder time to maintain a constant voltage during the injection on-time.
We then recommend to disable the charger (using an electronic switch for example) when doing measuremetn with the OhmPi.
