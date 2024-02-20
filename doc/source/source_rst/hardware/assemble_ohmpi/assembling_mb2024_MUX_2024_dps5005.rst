
.. warning::
    **OhmPi is a participative project open to all, it requires skills in electronics and to respect the safety rules. OhmPi must be assembled in a professional context and by people competent in electronics. The OhmPi team cannot be held responsible for any material or human damage which would be associated with the use or the assembly of OHMPI. The OhmPi team cannot be held responsible if the equipment does not work after assembly.**


Assembling the 32-electrode OhmPi system (OhmPi Lite: 1 mb2024 + 4 mux2024 + 1 DSP5005)
*****************************************************************************************

Here, we present how to build a 32-electrode OhmPi system using 1 mb.2024, 4 MUX.2024 and 1 DPS5005.
This tutorial aims to illustrate one way of assembling a system. It provides a working base on which users can rely.
Any idea to improve this design is welcome.

In this set-up, the MUX 2024 boards are configured in 2-role modes (see :ref:`2_roles`), so one should make sure that the MUX board are properly configured before going any further.
Mounting a system with MUX 2024 boards set-up in 4-role modes imply cabling the boards differently as to what is illustrated in this tutorial.

It is also best to having tested each MUX board individually before mounting them together.


.. table::
   :align: center
   :widths: 10 30
   
   +---+--------------------------------------------------------------------------------------------------------+
   |1  |   .. image:: ../../../img/mux.2024.0.x/9.jpg                                                           |
   +---+--------------------------------------------------------------------------------------------------------+
   |2  |   .. image:: ../../../img/mux.2024.0.x/10.jpg                                                          |
   +---+--------------------------------------------------------------------------------------------------------+
   |3  |   .. image:: ../../../img/mux.2024.0.x/11.jpg                                                          |
   +---+--------------------------------------------------------------------------------------------------------+
   |4  |   .. image:: ../../../img/mux.2024.0.x/12.jpg                                                          |
   +---+--------------------------------------------------------------------------------------------------------+
   |5  |   .. image:: ../../../img/mux.2024.0.x/13.jpg                                                          |
   +---+--------------------------------------------------------------------------------------------------------+
   |6  |   .. image:: ../../../img/mux.2024.0.x/14.jpg                                                          |
   +---+--------------------------------------------------------------------------------------------------------+
   |7  |   .. image:: ../../../img/mux.2024.0.x/15.jpg                                                          |
   +---+--------------------------------------------------------------------------------------------------------+
   |8  |   .. image:: ../../../img/mux.2024.0.x/16.jpg                                                          |
   +---+--------------------------------------------------------------------------------------------------------+
   |9  |   .. image:: ../../../img/mux.2024.0.x/17.jpg                                                          |
   +---+--------------------------------------------------------------------------------------------------------+
   |10 |   .. image:: ../../../img/mux.2024.0.x/18.jpg                                                          |
   +---+--------------------------------------------------------------------------------------------------------+
   |11 |   .. image:: ../../../img/mux.2024.0.x/19.jpg                                                          |
   +---+--------------------------------------------------------------------------------------------------------+
   |12 |   .. image:: ../../../img/mux.2024.0.x/20.jpg                                                          |
   +---+--------------------------------------------------------------------------------------------------------+

.. warning::
      At this point in the build, we consider that you have followed the instructions in :ref:`Getting-started` section


Please connect both 12 V Battery for RX and TX.

For direct use of Raspberry Pi Connect Screen, mouse and keybord, for remote control use SSH or VNC.

Now it is possible to carry out the first test on a reference circuit. See :ref:`first_steps` for more details.
