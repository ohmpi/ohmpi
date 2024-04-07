Troubleshooting
********************

We encourage users to report any issue, or bugs as an issue in the `official repository on GitLab <https://gitlab.com/ohmpi/ohmpi/-/issues>`_.
Please have a look at existing open and closed issues before posting a new one.
We've compiled here below a list of common issues and and explanations on how to fix them.

Issue with the pulses between A and B
=====================================

In the measurement board v2023, this is likely due to the optical relays not opening or closing properly. These relays are quite fragile and, from experience, are easily damaged. Check if the optical relay are still working by measuring if they are conductor when turned on using a multimeter without connecting any electrodes to A and B.

If an optical relay is broken, you will have to replace it with a new one.

In the measurement board v2024, these optical relays are replaced by mechanical relays which are more robust and shoudn't cause any issue.


Values given is not the correct one
===================================

One possible cause is that the **shunt resistor was burned**. Once burned, the value of the resistor is not correct anymore and we advice to change it. To see if the shunt is burned, you can measure the value of the shunt resistor to see if it still has the expected value.

Another possibility is that the MN voltage you are trying to measure is **over the range of the ADC** (+/- 4.5 V effective range for ADS1115). You can easily check that by measuring the voltage at MN with a voltmeter.

In the measurement board v2024, the current sensing part is replaced by a click board. It is possible that the shunt resistance on this click board is burned due to malfunction. In this case, erroneous value of current will be given. The click board must be replaced to solve the issue.


Communication issue between components
======================================

Most components of the OhmPi communicate via I2C protocol. This protocol works with two lines (SDA and SCL) that **must be pulled-up** at rest. The pull-up resistor consist in placing a 100k (or similar values) resistor between the line and VDD (5V in this case).

Check with the multimeter the voltage between SDA/SCL and the ground to see if it reaches 5V at rest. If it's not the case, you may need stronger pull-up (smaller value of pull-up resistor).

.. note::
    On the measurement board v2024, the I2C isolator from Mikroe, already has pull-up that adds to the pull-up already on the ADS1115 board. If the ADS1115 of the Vmn part cannot be seen by i2cdetect, we recommend to remove the pull-up resistors on the Mikroe I2C isolator board.

