 .. _config:
Configuration
*************

The configuration of the OhmPi file `config.py` allows to configure the OhmPi.
A default version of `config.py` is provided in the repository.
This file should be edited to customize the configuration following the user's needs and preferences.
A series of default configuration files are available in the configs folder. A simple helper command can help you select the appropriate configuration file depending on your version of the meausurement board and type of MUX boards.
The helper will ask you a few questions and will select the right configuration for your case. It can be called in via the terminal as
.. code-block:: bash

   $ python setup_config.py

Still, is best practice to open the configuration file and check that the parameters are correctly configured.
Updating the configuration file manually is mandatory for custom systems combining different versions of the measurement and MUX boards.

The configuration is written in a python file structured in a series of dictionnaries related to:
1. OHMPI_CONFIG: the OhmPi instrument information (id of the instrument and default settings)
2. HARDWARE_CONFIG: the hardware system in which the five different modules 'ctl' (controller), 'tx' (transmitter), 'rx' (receiver), 'mux' (multiplexers), 'pwr' (power).
3. the logging dictionnaries divided in:
   - EXEC_LOGGING_CONFIG
   - DATA_LOGGING_CONFIG
   - SOH_LOGGING_CONFIG
4. the MQTT dictionnaries divided in:
   - MQTT_LOGGING_CONFIG
   - MQTT_CONTROL_CONFIG

.. toctree::
   :maxdepth: 2
   :caption: Contents:

.. automodule:: configs.config_default
    :members:
    :undoc-members:
    :show-inheritance:


One should make sure to understand the parameters before altering them. It is also recommended to keep a copy of the default configuration.

