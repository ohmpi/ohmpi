.. warning::
    **OhmPi is a participative project open to all, it requires skills in electronics and to respect the safety rules. OhmPi must be assembled in a professional context and by people competent in electronics. The OhmPi team cannot be held responsible for any material or human damage which would be associated with the use or the assembly of OHMPI. The OhmPi team cannot be held responsible if the equipment does not work after assembly.**


. _Getting started:

Getting started
***************

Step 1: Set up the Raspberry Pi
===============================
First, install an operating system on the Raspberry Pi by following the official `instructions <https://www.raspberrypi.com/documentation/computers/getting-started.html#install-an-operating-system>`_

Then connect to the Raspberry Pi either via ssh or using an external monitor.

For all questions related to Raspberry Pi operations, please refer to the official `ocumentation <https://www.raspberrypi.com/documentation/>`_

Step 2: Clone the OhmPi project
===============================

You need to clone the OhmPi repository on the Raspberry Pi with the following command:
.. code-block:: bash

   $ git clone https://gitlab.irstea.fr/reversaal/OhmPi.git

Step 3: Run the installation script
===================================

Simply navigate to the OhmPi folder and run the following command on the terminal:

.. code-block:: bash

   $ .install.sh

The install script first creates an python virtual environment called "ohmpy" in which all dependencies will be installed. Dependecies are specified in requirements.txt
When the installation is completed check that requirements are met using pip list.
It then installs a local MQTT broker which will be used to centralise all the communication between the hardware, software and interfaces.
It also properly configures the I2C buses on the raspberry Pi.

When the installation is performed, we need to add the OhmPi module to the environment by editing the PYTHONPATH or editing the .bashrc file as follows:

.. code-block:: bash

   $ nano ~/.bashrc

And add the following line:

.. code-block:: bash

   $export PYTHONPATH=$PYTHONPATH:/home/<username>/OhmPi

Step 4: Activate the ohmpy virtual environment
==============================================
Before operating the instrument, we need to activate the ohmpy virtual environment with the following command:

.. code-block:: bash

   $ cd ~/OhmPi
   $ source ohmpy/bin/activate

If you need to leave the virtual environment, simply type:

.. code-block:: bash
   
   $ deactivate

Following these steps, you are now ready to operate the OhmPi.