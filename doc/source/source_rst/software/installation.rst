.. warning::
    **OhmPi is a participative project open to all, it requires skills in electronics and to respect the safety rules. OhmPi must be assembled in a professional context and by people competent in electronics. The OhmPi team cannot be held responsible for any material or human damage which would be associated with the use or the assembly of OHMPI. The OhmPi team cannot be held responsible if the equipment does not work after assembly.**


.. _Getting-started:

Software installation
*********************

Step 1: Set up the Raspberry Pi
===============================
First, install an operating system on the Raspberry Pi by following the official `instructions <https://www.raspberrypi.com/documentation/computers/getting-started.html#install-an-operating-system>`_

Then connect to the Raspberry Pi either via ssh or using an external monitor.

For all questions related to Raspberry Pi operations, please refer to the official `documentation <https://www.raspberrypi.com/documentation/>`_

In the "Raspberry Pi Configuration" (graphically: start button > Preferences > Raspberry Pi Configuration; in command line: `raspi-config` ), in the 'Interfaces' tab, make sure **I2C is enabled**. That will allow the Pi to communicate with the OhmPi measurement board.

Step 2: Clone the OhmPi project
===============================

You need to clone the OhmPi repository on the Raspberry Pi with the following command:

.. code-block:: bash

   git clone https://gitlab.com/ohmpi/ohmpi.git

Note that the project moved from the Gitlab IRSTEA to gitlab.com in January 2024. The Gitlab IRSTEA is synced as a read-only clone from the gitlab.com.

Step 3: Run the installation script
===================================

Simply navigate to the OhmPi folder:

.. code-block:: bash

   cd ohmpi

And run the following command on the terminal:

.. code-block:: bash

   ./install.sh

The install script:

- creates an **python virtual environment** called "ohmpy" in which all dependencies will be installed;
- installs all **dependencies** specified in requirements.txt;
- installs a **local MQTT broker** which will be used to centralize all the communication between the hardware, the software and the interfaces;
- configures the **I2C buses** on the Raspberry Pi.


Step 4: Activate the *ohmpy* virtual environment
================================================
Before operating the instrument, we need to activate the *ohmpy* virtual environment with the following command:

.. code-block:: bash

   source env.sh

The script env.sh will automatically activate the environment and set the PYTHONPATH variable to be able to find the OhmPi Python package.

You can also do these steps manually to activate the environment:

.. code-block:: bash

   cd ~/OhmPi
   source ohmpy/bin/activate

If you need to leave the virtual environment, simply type:

.. code-block:: bash
   
   deactivate

To automatically set the PYTHONPATH variable for each new terminal windows, you can edit the .bashrc file as follows:

.. code-block:: bash

   nano ~/.bashrc

And add the following line corresponding:

.. code-block:: bash

   export PYTHONPATH=$PYTHONPATH:/home/<username>/ohmpi

Replace *<username>* by your username on the Raspberry Pi (e.g.: /home/pi/ohmpi).

Following these steps, you are now ready to operate the OhmPi.