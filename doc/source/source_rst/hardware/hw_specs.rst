Boards specifications
*********************

Measurement board
=================

This section introduces the OhmPi measurement boards. Starting from this year, it has been possible to use any measurement board with the latest OhmPi code.
Consequently, the OhmPi group provides a variety of board options tailored to your technical needs (e.g., laboratory measurement, field measurement), budget, and electronic skills.

The characteristics of each measurement board are described in the following table:


Recognize the version of the measurement board
----------------------------------------------

   +-----------------------------------------------------------------+
   |   .. image:: ../../img/v2023.x.x/step_n_2/a/24_mes_board.jpg    |
   |      :width: 900px                                              |
   +-----------------------------------------------------------------+
   |**Measurement board V2023.0.1**                                  |
   +-----------------------------------------------------------------+
   |   .. image:: ../../img/mb.2024.x.x/31.jpg                       |
   |      :width: 900px                                              |
   +-----------------------------------------------------------------+
   |**Measurement board V2024.0.2**                                  |
   +-----------------------------------------------------------------+  

Specifications
--------------

.. table::
   :align: center

   +----------------------------------+-----------------------+-----------------------+-----------+
   | **Parameters**                   |**v2023.0.1**          |       **v2024.0.2**   | Units     |
   +==================================+=======================+=======================+===========+
   |Vmn number of channels            |1                      |1                      |-          |
   +----------------------------------+-----------------------+-----------------------+-----------+
   |Operating temperature             |0 to 50                |-25 to 50              |°C         |
   +----------------------------------+-----------------------+-----------------------+-----------+
   |Max. permissible Vab              |24                     |200                    |vdc        |
   +----------------------------------+-----------------------+-----------------------+-----------+
   |Power supply                      |12                     |12                     |vdc        |
   +----------------------------------+-----------------------+-----------------------+-----------+
   |Current with 2 ohms shunt resistor|0.11 to 40             |0.11 to 500            |mA         |
   +----------------------------------+-----------------------+-----------------------+-----------+
   |Min pulse duration                |50                     |50                     |ms         |
   +----------------------------------+-----------------------+-----------------------+-----------+
   |Max pulse duration                |15                     |15                     |second     |
   +----------------------------------+-----------------------+-----------------------+-----------+
   |Vmn input impedance               |80                     |1000                   |MOhm       |
   +----------------------------------+-----------------------+-----------------------+-----------+
   |Vmn range                         |-/+ 5                  | -/+5                  |volt       |
   +----------------------------------+-----------------------+-----------------------+-----------+


Assemble measurement board (MB)
------------------------------- 

- :ref:`mb2023-build`
- :ref:`mb2024-build`


Multiplexer board
=================

Measurement board are limited to four electrodes (A, B, M and N).
Multiplexer board are composed or electrical relay (electronic switches) that enable to route the signal
from A, B, M or N from the measurement board towards the specified electrodes. Multiplexer boards are needed for a 
multi-electrode system.

Recognize the version of the MUX boards
---------------------------------------

   +-----------------------------------------------------------------+
   |   .. image:: ../../img/v2023.x.x/step_n_3/a /MUX_00.jpg         |
   |      :width: 900px                                              |
   +-----------------------------------------------------------------+
   |**Measurement board V2023.0.1**                                  |
   +-----------------------------------------------------------------+
   |   .. image:: ../../img/mux.2024.0.x/1.jpg                       |
   |      :width: 900px                                              |
   +-----------------------------------------------------------------+
   |**Measurement board V2024.0.2**                                  |
   +-----------------------------------------------------------------+  

Specifications
--------------

.. table::
   :align: center

   +----------------------------------+------------------------+----------------------+
   | **Parameters**                   |**v2023.X.X**           |       **v2024.X.X**  |
   +==================================+========================+======================+
   |Number of electrodes per board    |    64                  |  16 (or 8)           |
   +----------------------------------+------------------------+----------------------+
   |Number of roles (A, B, M or N)    |                        |  2 roles (or 4)      |
   |per board                         |   1                    |                      |
   +----------------------------------+------------------------+----------------------+
   |Power supply                      | 12 V                   | 12V (or 5V)          |
   +----------------------------------+------------------------+----------------------+


Assemble multiplexer board (MUX)
--------------------------------

- :ref:`mux2023-build`
- :ref:`mux2024-build`
   