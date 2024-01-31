OhmPi electronic design
************************


Measurement board
=================

The measurement board integrates different electronic components to

- measure the voltage at MN
- measure the current injected at AB
- switch the polarity of AB (to make different half-cycles/stack)

Some general explanation about the components is given below to help you understand
the general electronics of the OhmPi. For more details, we redirect the reader to
the datasheet of each component.

.. image:: ../../../img/Hardware_structure.png

  OhmPi hardware flowchart.

**Measuring voltage**

Voltage measurement is typically done through an **ADC (Analog to Digital Converter)**.
In the OhmPi, the component `ADS1115`, a 16-bit ADC is used. The `ADS1115` is
also equipped with a programmable gain control (PGA), which means it can
scale up the measured voltage by a factor before digitizing it. Its gain can
vary between 2/3 and 16. With a gain of 1, this component can measure voltages
between 0 and 5 V with a precision of 5 / (2 ^ 16) = 0.076 mV.

However, we often measure voltage beyond 5 V. So to measure larger voltage with
our ADC, we need to divide the received voltage. In ``mb_2023``, this is done using
a **resistor divider bridge**. The voltage at MN is the distributed across two
resistors placed in series according to their respective resistances. For instance,
if we see 12V at MN and have two resistors in series of 150 and 300 Ohms. We will measure
12 * 150 / (150 + 300) = 4 V on the first resistor and 12 * 300 / (150 + 300) = 8 V on the second. The 4 V can
be measured by our ADC.

Another technique to reduce the voltage consists in using **operational amplifier (opamp)**.
These devices have multiple applications and using a given configuration with a known resistance,
can be used to scale down the voltage input. In addition, opamp are used in 'follow-up' mode
to ensure a **high input impedance** of the MN part. Indeed, if current is leaking in the MN
part while we measure, it will affect our measurement.

In the measurement board 2024 (``mb_2024``), an opamp is also used in differential mode to
measure the difference in voltage between M and N (N is used as a 'floating ground'). This
enables us to measure much higher voltage as long as the difference between M and N is not too large.


**Measuring current**

Current measurement is usually obtained by measuring the voltage through a very accurate resistance
called a **shunt resistance**. In ``mb_2023``, a shunt resistance of 2 Ohms is used.
As this resistance has a tiny value, the voltage drop measured through it is also very small and
need to be amplified before being measured by the ADC. This is done through the INA282 component (also an opamp).

In ``mb_2024``, the current measurement is done via a "Click module" where the shunt and amplifier (INA equivalent)
are already soldered.


**Polarity control**

Each half-cycle has a different polarity. Current is first injected from A to B then from B to A
with or without an off-time between the two injections. This cycle of polarity is ensured using
four **relays** (optical in v2023, mechanical in v2024) that open or close alternatively. The
relays are controlled from the MCP23008 which is **GPIO expander**.

**Communication**

The ADC (ADS1115) and GPI expander (MCP23008) communicate with the controller (raspberrypi) via
two wires (SDA and SCL) using the **I2C protocol**. This protocol makes use of two wires. One wire is used to send
pulses from a clock (SCL) and the other one to transmit data (SDA). These wires must be
pulled high using pull-up resistors (meaning at rest, there should be 5V between these wires and the ground).


Multiplexer
===========

Multiplexer are used to address multiple electrodes. For this they use **relays**
to create an electronic path between the electrode and the entry (A, B, M, or N) on the
measurement board. The relays are usually controlled by a **GPIO expander** (MCP23017).
Because too many GPIO expander cannot be addressed on the same I2C bus, we use a
**I2C expander** (TCA9548A) which is itself connected via I2C to the controller (Rapsberry Pi).
