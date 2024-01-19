.. _config:
Configuration
*************

The configuration file `config.py` defines how the OhmPi system is assembled and expected to behave. It tells the software how the hardware is set up, cabled and configured.
In certain cases, it also allows you to define hardware specifications, such as the maximum voltage that a specific MUX board can handle.
For general purpose, most specifications can be left on default values.

.. warning::
  Not to be confused with :ref:`settings`. One configuration specified in a config.py file can handle multiple combinations of acquisition settings.

Default configuration
---------------------

A default version of `config.py` is provided in the repository.
This file should be edited to customize the configuration following the user's needs and preferences.
A series of default configuration files are available in the configs folder. A simple helper command can help you select the appropriate configuration file depending on your version of the meausurement board and type of MUX boards.
The helper will ask you a few questions and will select the right configuration for your case. It can be called in via the terminal as
.. code-block:: bash

   $ python setup_config.py

Still, it is best practice to open the configuration file and check that the parameters are correctly configured.
Updating the configuration file manually is mandatory for custom systems combining different versions of the measurement and MUX boards.

.. warning::
   One should make sure to understand the parameters before altering them. It is also recommended to keep a copy of the default configuration.

Configuration file structure
----------------------------

.. code-block:: python
  :caption: Config file header

    import logging
    from ohmpi.utils import get_platform

    from paho.mqtt.client import MQTTv31  # noqa

    _, on_pi = get_platform()
    # DEFINE THE ID OF YOUR OhmPi
    ohmpi_id = '0001' if on_pi else 'XXXX'
    # DEFINE YOUR MQTT BROKER (DEFAULT: 'localhost')
    mqtt_broker = 'localhost' if on_pi else 'NAME_YOUR_BROKER_WHEN_IN_SIMULATION_MODE_HERE'
    # DEFINE THE SUFFIX TO ADD TO YOUR LOGS FILES
    logging_suffix = ''


The configuration is written in a python file structured in a series of dictionaries related to:

#. OHMPI_CONFIG: the OhmPi instrument information (id of the instrument and default settings).

.. code-block:: python
  :caption: OHMPI_CONFIG: Dictionary containing basic informations about the OhmPi instrument

  # OhmPi configuration
  OHMPI_CONFIG = {
      'id': ohmpi_id,  # Unique identifier of the OhmPi board (string), default = '0001'
      'settings': 'ohmpi_settings.json',  # INSERT YOUR FAVORITE SETTINGS FILE HERE
  }


#. HARDWARE_CONFIG: the hardware system in which the five different modules 'ctl' (controller), 'tx' (transmitter), 'rx' (receiver), 'mux' (multiplexers), 'pwr' (power).


+----------+----------------+----------------------------------------------------------------------------------------------------------------------+
| Main Key | Module Key     |                                                    Value                                                             |
|          |                +=============================================+=================+======================================================+
|          |                | Description                                 | Expected Value  | Value description                                    |
+==========+================+=============================================+=================+======================================================+
| ctl      | model          | Controller of the OhmPi system.             | raspberry_pi    | Defines a Raspberry Pi as controller.                |
+----------+----------------+---------------------------------------------+-----------------+------------------------------------------------------+
| pwr      | model          | Type of power unit.                         | pwr_batt        | Defines an external battery as power unit.           |
|          |                |                                             |-----------------+------------------------------------------------------+
|          |                |                                             | pwr_dps5005     | Defines an external DPS 5005 as power unit           |
|          +----------------+---------------------------------------------+-----------------+------------------------------------------------------+
|          | voltage        |  Defines default output voltage in V.       | float) e.g. 12. | Sets 12 V as default voltage.                        |
|          +----------------+---------------------------------------------+-----------------+------------------------------------------------------+
|          | interface_name | Interface used for communication            |                 |                                                      |
|          |                | with controller.                            | none            | Sets no software communication (e.g. for 'pwr_batt') |
|          |                |                                             |-----------------+------------------------------------------------------+
|          |                |                                             | modbus          | Sets a modubs connection                             |
+----------+----------------+---------------------------------------------+-----------------+------------------------------------------------------+


.. autodata:: configs.config_example.HARDWARE_CONFIG

.. code-block:: python
  :caption: HARDWARE_CONFIG: Dictionary containing configuration of the hardware system and how it is assembled.
  r_shunt = 2. # Value of the shunt resistor in Ohm.
  HARDWARE_CONFIG = {
      'ctl': {'model': 'raspberry_pi'}, # contains informations related to controller unit, 'raspberry_pi' only implemented so far
      'pwr': {'model': 'pwr_batt', 'voltage': 12., 'interface_name': 'none'},
      'tx':  {'model': 'mb_2024_0_2',
               'voltage_max': 50.,  # Maximum voltage supported by the TX board [V]
               'current_max': 4.80/(50*r_shunt),  # Maximum voltage read by the current ADC on the TX board [A]
               'r_shunt': r_shunt,  # Shunt resistance in Ohms
               'interface_name': 'i2c'
              },
      'rx':  {'model': 'mb_2024_0_2',
               'latency': 0.010,  # latency in seconds in continuous mode
               'sampling_rate': 50,  # number of samples per second
               'interface_name': 'i2c'
              },
      'mux': {'boards':
                  {'mux_00':
                       {'model': 'mux_2024_0_X',
                        'electrodes': range(1, 17),
                        'roles': ['A', 'B', 'M', 'N'],
                        'tca_address': None,
                        'tca_channel': 0,
                        'addr1': 'down',
                        'addr2': 'down',
                        },
                   },
               'default': {'interface_name': 'i2c_ext',
                           'voltage_max': 50.,
                           'current_max': 3.}
              }
      }

#. the logging dictionaries divided in:

.. code-block:: python
  :caption: EXEC_LOGGING_CONFIG: dictionary configuring how the execution commands are being logged by the system. Useful for debugging.

  # SET THE LOGGING LEVELS, MQTT BROKERS AND MQTT OPTIONS ACCORDING TO YOUR NEEDS
  # Execution logging configuration
  EXEC_LOGGING_CONFIG = {
      'logging_level': logging.INFO,
      'log_file_logging_level': logging.DEBUG,
      'logging_to_console': True,
      'file_name': f'exec{logging_suffix}.log',
      'max_bytes': 262144,
      'backup_count': 30,
      'when': 'd',
      'interval': 1
  }


*
.. code-block:: python
  :caption: DATA_LOGGING_CONFIG: Dictionary configuring the data logging capabilities of the system

  # Data logging configuration
  DATA_LOGGING_CONFIG = {
      'logging_level': logging.INFO,
      'logging_to_console': True,
      'file_name': f'data{logging_suffix}.log',
      'max_bytes': 16777216,
      'backup_count': 1024,
      'when': 'd',
      'interval': 1
  }


.. code-block:: python
  :caption: SOH_LOGGING_CONFIG: Dictionary configuring how the state of health of the system is logged
  # State of Health logging configuration (For a future release)
  SOH_LOGGING_CONFIG = {
      'logging_level': logging.INFO,
      'log_file_logging_level': logging.DEBUG,
      'logging_to_console': True,
      'file_name': f'soh{logging_suffix}.log',
      'max_bytes': 16777216,
      'backup_count': 1024,
      'when': 'd',
      'interval': 1
  }



#. the MQTT dictionaries divided in:

.. code-block:: python
  :caption: MQTT_LOGGING_CONFIG

  # MQTT logging configuration parameters
  MQTT_LOGGING_CONFIG = {
      'hostname': mqtt_broker,
      'port': 1883,
      'qos': 2,
      'retain': False,
      'keepalive': 60,
      'will': None,
      'auth': {'username': 'mqtt_user', 'password': 'mqtt_password'},
      'tls': None,
      'protocol': MQTTv31,
      'transport': 'tcp',
      'client_id': f'{OHMPI_CONFIG["id"]}',
      'exec_topic': f'ohmpi_{OHMPI_CONFIG["id"]}/exec',
      'exec_logging_level': logging.DEBUG,
      'data_topic': f'ohmpi_{OHMPI_CONFIG["id"]}/data',
      'data_logging_level': DATA_LOGGING_CONFIG['logging_level'],
      'soh_topic': f'ohmpi_{OHMPI_CONFIG["id"]}/soh',
      'soh_logging_level': SOH_LOGGING_CONFIG['logging_level']
  }


.. code-block:: python
  :caption: MQTT_CONTROL_CONFIG

  # MQTT control configuration parameters
  MQTT_CONTROL_CONFIG = {
      'hostname': mqtt_broker,
      'port': 1883,
      'qos': 2,
      'retain': False,
      'keepalive': 60,
      'will': None,
      'auth': {'username': 'mqtt_user', 'password': 'mqtt_password'},
      'tls': None,
      'protocol': MQTTv31,
      'transport': 'tcp',
      'client_id': f'{OHMPI_CONFIG["id"]}',
      'ctrl_topic': f'ohmpi_{OHMPI_CONFIG["id"]}/ctrl'
  }

