
.. warning::
    **OhmPi is a participative project open to all, it requires skills in electronics and to respect the safety rules. OhmPi must be assembled in a professional context and by people competent in electronics. The OhmPi team cannot be held responsible for any material or human damage which would be associated with the use or the assembly of OHMPI. The OhmPi team cannot be held responsible if the equipment does not work after assembly.**


Assembling an OhmPi Lite (16 electrodes)
****************************************

1 :ref:`mb2024-build` + 2 :ref:`mux2024-build` + 1 :ref:`power-DPH5005`

Here, we present the schematics of a 16-electrode OhmPi system made of 1 mb.2024, 2 MUX.2024 and 1 DPH5005.
This tutorial aims to illustrate one way of assembling a system using the MUX 2024 boards.
For a detailed photo description of the cabling and assembling processes, please have a look at steps 2 to 7 and 14 to 17
of :ref:`ohmpi-lite-32` tutorial.

This particular assembling is done thanks to two plexiglass plates (DXF files: `base <../../../_static/base.dxf>`_, `top <../../../_static/top.dxf>`_) and different spacers.

.. warning::
  In this set-up, the MUX 2024 boards are configured in 2-role mode (see :ref:`2_roles`). This means that each MUX
  board addresses 2 roles (AB or MN) and 16 electrodes. So one needs at least two MUX boards to be able to make ABMN
  measurements. Mounting the MUX boards in 2-role mode allows to take advantage of the electrode IDC connectors to
  connect more easily reference circuits for lab testing. Mounting a system with MUX 2024 boards each set-up in 4-role
  mode (see :ref:`4_roles`) is also possible but implies cabling the boards differently as to what is illustrated in
  this tutorial. 4-role mode is mainly designed for 8-electrode systems, or for set up where users are only connecting
  electrode wires via the screw terminals.


  It is also most recommended to having tested each MUX board individually (see :ref:`mux2024-test`) before mounting
  them together.

.. table::
   :align: center
   
   +--------------------------------------------------------------------------------------------------------+
   |   .. image:: ../../../img/v2024.x.x/ohmpi_lite16/1.jpg                                                 |
   |      :width: 1100px                                                                                    |
   +--------------------------------------------------------------------------------------------------------+
   |   .. image:: ../../../img/v2024.x.x/ohmpi_lite16/2.jpg                                                 |
   |      :width: 1100px                                                                                    |
   +--------------------------------------------------------------------------------------------------------+
   |   .. image:: ../../../img/v2024.x.x/ohmpi_lite16/3.jpg                                                 |
   |      :width: 1100px                                                                                    |
   +--------------------------------------------------------------------------------------------------------+
   |   .. image:: ../../../img/v2024.x.x/ohmpi_lite16/4.jpg                                                 |
   |      :width: 1100px                                                                                    |
   +--------------------------------------------------------------------------------------------------------+
   |   .. image:: ../../../img/v2024.x.x/ohmpi_lite16/5.jpg                                                 |
   |      :width: 1100px                                                                                    |
   +--------------------------------------------------------------------------------------------------------+
   |   .. image:: ../../../img/v2024.x.x/ohmpi_lite16/6.jpg                                                 |
   |      :width: 1100px                                                                                    |
   +--------------------------------------------------------------------------------------------------------+
   |   .. image:: ../../../img/v2024.x.x/ohmpi_lite16/7.jpg                                                 |
   |      :width: 1100px                                                                                    |
   +--------------------------------------------------------------------------------------------------------+
   
.. warning::
   In MUX2024, the wiring of the electrodes from the IDC connector follows the order below (different from MUX2023).
   Take this into account if you wire your ribbon cable to further connectors or screw terminals.

   .. image:: ../../../img/mux2024-idc.jpg

.. warning::
      At this point in the build, we consider that you have followed the instructions in :ref:`Getting-started` section


Please connect both 12 V Battery for RX and TX.

For direct use of Raspberry Pi Connect Screen, mouse and keyboard, for remote control use SSH or VNC.

Now it is possible to carry out the first test on a reference circuit. See tests in :ref:`ohmpi_v2024` for more details.
