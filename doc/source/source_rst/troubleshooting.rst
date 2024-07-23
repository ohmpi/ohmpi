Troubleshooting
********************

We encourage users to report any issue, or bugs as an issue in the `official repository on GitLab <https://gitlab.com/ohmpi/ohmpi/-/issues>`_.
Please have a look at existing open and closed issues before posting a new one.
We have compiled here below a list of common issues and and explanations on how to fix them.
For issue with the hardware, make sure your board passes the hardware checks (:ref:`mb2024-test`, :ref:`mux2024-test`).


Communication issue between components (I2C, pull-up)
=====================================================

If you get an I2C communication error or cannot see some I2C address with `i2cdetect`.

Most components of the OhmPi communicate via I2C protocol. This protocol works with two lines (SDA and SCL) that **must be pulled-up** at rest. The pull-up resistor consist in placing a 100k (or similar values) resistor between the line and VDD (5V in this case).

Make sure you have the correct configuration for your assembled system (see :ref:`config`).
Check with the multimeter the voltage between SDA/SCL and the ground to see if it reaches 5V at rest. If it's not the case, you may need stronger pull-up (smaller value of pull-up resistor).

.. note::
    On the measurement board v2024, the I2C isolator from Mikroe, already has pull-up that adds to the pull-up already on the ADS1115 board. If the ADS1115 of the Vmn part cannot be seen by i2cdetect, we recommend to remove the pull-up resistors on the Mikroe I2C isolator board (see note fig29 in :ref:`mb2024-build`)


Issue with the pulses between A and B
=====================================

In the measurement board v2023, this is likely due to the optical relays not opening or closing properly. These relays are quite fragile and, from experience, are easily damaged. Check if the optical relay are still working by measuring if they are conductor when turned on using a multimeter without connecting any electrodes to A and B.

If an optical relay is broken, you will have to replace it with a new one.

In the measurement board v2024, these optical relays are replaced by mechanical relays which are more robust and should not cause any issue.


Values given is not the correct one
===================================

One possible cause is that the **shunt resistor was burned**. Once burned, the value of the resistor is not correct anymore and we advice to change it. To see if the shunt is burned, you can measure the value of the shunt resistor to see if it still has the expected value.

Another possibility is that the MN voltage you are trying to measure is **over the range of the ADC** (+/- 4.5 V effective range for ADS1115). You can easily check that by measuring the voltage at MN with a voltmeter.

In the measurement board v2024, the current sensing part is replaced by a click board. It is possible that the shunt resistance on this click board is burned due to malfunction. In this case, erroneous value of current will be given. The click board must be replaced to solve the issue.


Resistances values are divided by 2 (mb2024)
=================================================

This can be due to a badly soldered connection between the DG411 and the MCP23008 MN or between the output pins of the DG411.
This means that the gain is not applied in the Vmn part. Use a multimeter in continuity mode to check connectivity and soldering of DG411 and MCP23008.


Noise in the Vmn and Iab signals
================================

The OhmPi does not filter the signal for 50 or 60Hz power noise. This noise can appear in the Vmn reading if the Tx or Rx battery is connected to a charger connected to the grid.
It can also appear in the field if there is an AC leakage or high voltage power lines nearby.

.. figure:: ../img/troubleshooting/50hz_noise.png
  :width: 100%
  :align: center
  
  Example of 50 Hz noise coming from a charger connected to the TX battery

To solve this, you may need to design a system that disconnect the charger (turn if off) when doing a measurement.


Unexpected electrode takeout
============================

The IDC socket of the mux2023 and mux2024 are not wired identically. Double check that you connected the right electrode to the right ribbon cable (see drawings in the assembling tutorials)


Strong decay in current
=======================

A strong decay in current can be an indication that the battery cannot supply enough power to the DPH5005 to main the requested voltage.
I can also be that the injection time is too short to let the current reach steady-state. In this case, we recommend to increase the injection time.


Modbus error
============

Modbus is the protocol used to communicated between the DPH5005 and the Raspberry Pi via a USB cable.
If the Pi cannot detect the DPH, a modbus error can happen. Make sure the USB cable is ok and that the DPH5005 is supplied.
It can also be that the DPH is not given enough time to start (latency time). This can be increased in the `config.py > HARDWARE_CONFIG > rx > latency`.


Current max out at 48 mA
========================

By default, the measurement board (v2023 and v2024) are setup with a shunt resistor of 2 Ohms. This effectively limit the current
we can measure to 48 mA. If the data you collected show current that seems to stays close to this value, they are probably higher but the 
measurement board cannot measure them properly. Note that the shunt resistor **does not limit the current**. If a too large current goes though the 
shunt resistor, it will burn and its value will not be precisely equal to 2 Ohms.

To measure larger current in the field, we recommend to use another shunt resistors (e.g. 1 Ohms for max 100 mA, 0.5 Ohms for max 200 mA).
Multiple 2 Ohms shunt resistors can also be placed in parallel to decrease the shunt resistance.
