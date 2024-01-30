Monitoring application
**********************

This section details ways to automate measurement acquisition in order to set up the OhmPi as a monitoring tool.

Repeated acquisition at fixed intervals
=======================================
The easiest way to set up time-lapse acquisition is to perform repeated acquisition of a sequence at fixed intervals.
Repeated acquisition can be initiated from the three different `interfaces`_.

.. code-block:: python
  ### Run multiple sequences at given time interval
  k.settings['nb_meas'] = 3  # run sequence three times
  k.settings['sequence_delay'] = 100 # every 100 s
  k.run_multiple_sequences()  # asynchron
  # k.interrupt()  # kill the asynchron sequence

Scheduled acquisition using crontab
===================================
Example run_sequence script and crontab screenshot

IoT acquisition and sensor trigger
==================================
Example node-red experiment