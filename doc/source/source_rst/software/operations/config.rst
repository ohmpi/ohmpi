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
A series of default configuration files are available in the configs folder. A simple helper command can help you select the appropriate configuration file depending on your version of the measurement board and type of MUX boards.
The helper will ask you a few questions and will select the right configuration for your case. It can be called in via the terminal as

.. code-block:: bash

   python setup_config.py

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
  :caption: OHMPI_CONFIG: Dictionary containing basic information about the OhmPi instrument

  # OhmPi configuration
  OHMPI_CONFIG = {
      'id': ohmpi_id,  # Unique identifier of the OhmPi board (string), default = '0001'
      'settings': 'settings/default.json',  # INSERT YOUR FAVORITE SETTINGS FILE HERE
  }


#. HARDWARE_CONFIG: the hardware system in which the five different modules 'ctl' (controller), 'tx' (transmitter), 'rx' (receiver), 'mux' (multiplexers), 'pwr' (power).

.. _table_hardware_config:
.. table:: HARDWARE_CONFIG

    +----------+----------------+---------------------------------------------------------------------------------------------------------------------------------------+
    | Main Key | Module Key     |                                                         Value                                                                         |
    |          |                +--------------------------------------------------+------------------+-----------------------------------------------------------------+
    |          |                | Description                                      | Expected Value   | Value description                                               |
    +==========+================+==================================================+==================+=================================================================+
    | ctl      | model          | Controller of the OhmPi system.                  | raspberry_pi     | Defines a Raspberry Pi as controller.                           |
    +----------+----------------+--------------------------------------------------+------------------+-----------------------------------------------------------------+
    | pwr      | model          | Type of power unit.                              | pwr_batt         | Defines an external battery as power unit.                      |
    |          |                |                                                  +------------------+-----------------------------------------------------------------+
    |          |                |                                                  | pwr_dph5005      | Defines an external DPH5005 as power unit                       |
    |          +----------------+--------------------------------------------------+------------------+-----------------------------------------------------------------+
    |          | voltage        |  Defines default output voltage in V.            |*float*, e.g. 12. | Sets 12 V as default voltage.                                   |
    |          +----------------+--------------------------------------------------+------------------+-----------------------------------------------------------------+
    |          | interface_name | | Interface used for communication               | none             | Sets no software communication (e.g. for 'pwr_batt')            |
    |          |                | | with controller.                               |                  |                                                                 |
    |          |                |                                                  +------------------+-----------------------------------------------------------------+
    |          |                |                                                  | modbus           | Sets a modubs connection                                        |
    +----------+----------------+--------------------------------------------------+------------------+-----------------------------------------------------------------+
    | tx       | model          | Type of transmitter.                             | mb_2024_0_2      | | Load TX defined in                                            |
    |          |                |                                                  |                  | | :func:`ohmpi.hardware_components.mb_2024_0_2`                 |
    |          |                |                                                  +------------------+-----------------------------------------------------------------+
    |          |                |                                                  | mb_2023_0_X      | | Load TX defined in                                            |
    |          |                |                                                  |                  | | :func:`ohmpi.hardware_components.mb_2023_0_X`                 |
    |          +----------------+--------------------------------------------------+------------------+-----------------------------------------------------------------+
    |          | voltage_max    | Maximum voltage supported by the TX board [V]    |*float*, e.g. 50. |                                                                 |
    |          +----------------+--------------------------------------------------+------------------+-----------------------------------------------------------------+
    |          | current_max    | Maximum current supported by TX board [A]        |*float*, e.g. 0.05| Is function of r_shunt. Can be calculated as 4.80/(50*r_shunt)  |
    |          +----------------+--------------------------------------------------+------------------+-----------------------------------------------------------------+
    |          | r_shunt        | Value (in Ohms) of shunt resistor mounted on TX. | *float*, e.g. 2. | 2 Ohms resistor.                                                |
    |          +----------------+--------------------------------------------------+------------------+-----------------------------------------------------------------+
    |          | interface_name | | Name of interface used for communication with  |                  |                                                                 |
    |          |                | | controller                                     | i2c              | I2C connector 1                                                 |
    |          |                |                                                  +------------------+-----------------------------------------------------------------+
    |          |                |                                                  | i2c_ext          | I2C connector 2                                                 |
    +----------+----------------+--------------------------------------------------+------------------+-----------------------------------------------------------------+
    | rx       | model          | Type of transmitter.                             | mb_2024_0_2      | | Load RX defined in                                            |
    |          |                |                                                  |                  | | :func:`ohmpi.hardware_components.mb_2024_0_2`                 |
    |          |                |                                                  +------------------+-----------------------------------------------------------------+
    |          |                |                                                  | mb_2023_0_X      | | Load RX defined in                                            |
    |          |                |                                                  |                  | | :func:`ohmpi.hardware_components.mb_2024_0_2`                 |
    |          +----------------+--------------------------------------------------+------------------+-----------------------------------------------------------------+
    |          | latency        | | Latency in seconds in continuous mode          |                  |                                                                 |
    |          |                | | (related to ADS)                               |*float*, e.g. 0.01| 10 ms                                                           |
    |          +----------------+--------------------------------------------------+------------------+-----------------------------------------------------------------+
    |          | sampling_rate  | Number of samples per second                     | *int*, e.g. 50   |  50 samples per seconds.                                        |
    |          +----------------+--------------------------------------------------+------------------+-----------------------------------------------------------------+
    |          | interface_name | | Name of interface used for communication with  |                  |                                                                 |
    |          |                | | controller                                     | i2c              | I2C connector 1                                                 |
    |          |                |                                                  +------------------+-----------------------------------------------------------------+
    |          |                |                                                  | i2c_ext          | I2C connector 2                                                 |
    +----------+----------------+--------------------------------------------------+------------------+-----------------------------------------------------------------+
    | mux      | boards         | | Dictionary containing all MUX boards of the    |                  |                                                                 |
    |          |                | | system and the associated specific             |                  |                                                                 |
    |          |                | | configuration.                                 | mux_id           | Dictionary (see table_mux_config_)                              |
    |          +----------------+--------------------------------------------------+------------------+-----------------------------------------------------------------+
    |          | default        | | Dictionary containing configuration applicable |                  |                                                                 |
    |          |                | | to all MUX boards of the systems               | default_dict     | Dictionary (see table_mux_config_)                              |
    +----------+----------------+--------------------------------------------------+------------------+-----------------------------------------------------------------+

.. _table_mux_config:
.. table:: MUX board general config in HARDWARE_CONFIG

    +--------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
    | Module Key         |                                                         Value                                                                                |
    |                    +--------------------------------------------------+-------------------------+-----------------------------------------------------------------+
    |                    | Description                                      | Expected Value          | Value description                                               |
    +====================+==================================================+=========================+=================================================================+
    | model              | Type of Mux board.                               | mux_2024_0_X            | | Load RX defined in                                            |
    |                    |                                                  |                         | | :func:`ohmpi.hardware_components.mux_2024_0_X`                |
    |                    |                                                  +-------------------------+-----------------------------------------------------------------+
    |                    |                                                  | mux_2023_0_X            | | Load RX defined in                                            |
    |                    |                                                  |                         | | :func:`ohmpi.hardware_components.mux_2023_0_X`                |
    +--------------------+--------------------------------------------------+-------------------------+-----------------------------------------------------------------+
    | electrodes         | List of electrodes addressed by the MUX board    | | *array-like*,         |    Sets electrode IDs addressed by the MUX board                |
    |                    |                                                  | | e.g. range(1,65)      |                                                                 |
    +--------------------+--------------------------------------------------+-------------------------+-----------------------------------------------------------------+
    | roles              | Roles addressed by the MUX board                 | | * *string*:           | | Sets roles addressed by the MUX board.                        |
    |                    |                                                  | |  'A', 'B', 'M', 'N'   | | If *string*, MUX addresses only 1 role (for MUX 2023)         |
    |                    |                                                  | | * or *list*, e.g.     | |                                                               |
    |                    |                                                  | |    ['A, 'B']          | | For MUX 2024:                                                 |
    |                    |                                                  | | * or *dict*, e.g.     | | * Number of roles defines if MUX set up in 2 or 4 roles mode. |
    |                    |                                                  | |  {'A':'X','B':'Y',    | | * *list* or *array* order determines physical cabling         |
    |                    |                                                  | |  'M':'XX','N':'YY'}   | | * *dict* values rely on annotation on MUX 2024 board          |
    |                    |                                                  |                         | |   'X', 'Y', 'XX', 'YY'                                        |
    +--------------------+--------------------------------------------------+-------------------------+-----------------------------------------------------------------+
    | voltage_max        | Maximum injected voltage managed by the MUX board| *float*, e.g. 50.       |  Sets maximum voltage to 50 V.                                  |
    +--------------------+--------------------------------------------------+-------------------------+-----------------------------------------------------------------+
    | current_max        | Maximum current [in A] managed by the MUX board  | *float*, e.g. 3.        |  Sets maximum current to 3 A.                                   |
    +--------------------+--------------------------------------------------+-------------------------+-----------------------------------------------------------------+

.. table:: MUX 2023 board specific config in HARDWARE_CONFIG

    +--------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
    | Module Key         |                                                         Value                                                                                |
    |                    +--------------------------------------------------+-------------------------+-----------------------------------------------------------------+
    |                    | Description                                      | Expected Value          | Value description                                               |
    +====================+==================================================+=========================+=================================================================+
    |  mux_tca_address   | I2C address of MUX board                         | | *hex integer*         |          Address of MUX board                                   |
    |                    |                                                  | | 0x70 - 0x77           |                                                                 |
    +--------------------+--------------------------------------------------+-------------------------+-----------------------------------------------------------------+

.. table:: MUX 2024 board specific config in HARDWARE_CONFIG

    +--------------------+----------------------------------------------------------------------------------------------------------------------------------------------+
    | Module Key         |                                                         Value                                                                                |
    |                    +--------------------------------------------------+-------------------------+-----------------------------------------------------------------+
    |                    | Description                                      | Expected Value          | Value description                                               |
    +====================+==================================================+=========================+=================================================================+
    | addr1              | Physical position of jumper on addr1             | | *string* 'up' or 'down| | This will compute I2C address of MUX board based on addr1     |
    |                    |                                                  |                         | | and addr 2 configuration. See :ref:`mux2024addresses`.        |
    +--------------------+--------------------------------------------------+-------------------------+-----------------------------------------------------------------+
    | addr2              | Physical position of jumper on addr1             | | *string* 'up' or 'down| | This will compute I2C address of MUX board based on addr1     |
    |                    |                                                  |                         | | and addr 2 configuration. See :ref:`mux2024addresses`.        |
    +--------------------+--------------------------------------------------+-------------------------+-----------------------------------------------------------------+
    |    tca_address     | I2C address of I2C extension                     | None *(default)*        |    No I2C extensions cabled.                                    |
    |                    |                                                  +-------------------------+-----------------------------------------------------------------+
    |                    |                                                  | *hex integer*, e.g. 0x71|          Address of I2C extension                               |
    +--------------------+--------------------------------------------------+-------------------------+-----------------------------------------------------------------+
    |     tca_channel    | Channel of the I2C extension                     | *int* 0 - 7             |   Channel used in case I2C extension configured.                |
    +--------------------+--------------------------------------------------+-------------------------+-----------------------------------------------------------------+

Here's an example of the HARDWARE_CONFIG:

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
                        'electrodes': range(1, 9),
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


The logging dictionaries divided in:

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



The MQTT dictionaries divided in:

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

