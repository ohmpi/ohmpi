Loggers
*******

Loggers have been introduced in this release. They use the excellent logging python package.
Specific handlers have been implemented for running with ohmpi.py (one for logging to an mqtt broker (see `MQTT interface`_ for more details) and one for creating zipped rotated logs on disk).

Two loggers have been defined. The first one is dedicated to log operations execution. It is named exec_logger. The second one, named data_logger, is dedicated to log data. A third one is planned to log the state of health (SOH) of the system in a future version.

By default, logs are written to the console (print-like), stored locally in files (a zip is created after some time i.e. every day and/or when the size of the log exceeds a maximum size) and sent to an MQTT broker. Different logging levels may be defined for the different logs and handlers in the `Configuration file`_.

Advanced users may write new handlers and edit the `setup_loggers.py` file to customize the logging mechanisms to their needs.
