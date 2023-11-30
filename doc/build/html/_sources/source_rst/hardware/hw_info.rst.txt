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

**Measuring voltage**

Voltage measurement is typically done through an **ADC (Analog to Digital Converter)**.
In the OhmPi, the component `ADS1115`, a 16-bit ADC is used. The `ADS1115` is
also equipped with a programmable gain control (PGA), which means it can
scale up the measured voltage by a factor before digitising it. Its gain can
vary between 2/3 and 16. With a gain of 1, this component can measure voltages
between 0 and 5 V with a precision of 5 / (2 ^ 16) = 0.076 mV.

However, we often measure voltage beyond 5 V. So to measure larger voltage with
our ADC, we need to divide the received voltage. In mb_2023, this is done using
a **resistor divider bridge**. The voltage at MN is the distributed across two
resistors placed in series according to their respective resistances. For instance,
if we see 12V at MN and have two resistors in series of 150 and 300 Ohms. We will measure
12 * 150 / (150 + 300) = 4 V on the first resistor and 8 V on the second. The 4 V can
be measured by our ADC.

Another technique to reduce the voltage consist in using **opamp (Operational Amplifier)**.
These devices have multiple applications and using a given configuration with a known resistance,
can be used to scale down the voltage input. In addition, opamp are used in 'follow-up' mode
to ensure a **high input impedance** of the MN part. Indeed, if current is leaking in the MN
part while we measure, it will affect our measure.

In the measurement board 2024 (mb_2024), an opamp is also used in differential model to only
measure the difference in voltage between M and N (N is used as a 'floating ground'). This
enables us to measure much higher voltage as long as the difference between M and N is not too large.


**Measuring current**

Current is usually measure by measuring the voltage through a very accurate resistance
called a **shunt resistance**. In `mb_2023`, a shunt resistance of 2 Ohms is used.
As this resistance has a tiny value, the voltage measure at on it is also very small and
need to be amplified before being measured by the ADC. This is done through the INA282 components.

In `mb_2024`, the current measurement is done via a click module where the shunt and amplifier (INA equivalent)
are already soldered.


**Polarity control**

Each half-cycle has a different polarity. Current is first injected from A to B then from B to A
with or without a time-off between the two. This reversed of polarity is ensured using
four **relays** (optical in v2023, mechanical in v2024) that operate this transition. The
relays are controlled from the MCP2308 which is **GPIO expander**.

**Communication**

The ADC (ADS1115) and GPI expander (MCP2308) communicate with the controller (raspberrypi) via
two wires (SDA and SCL) using the **I2C protocol**. This protocol uses a line which sends
pulses from a clock (SCL) and another line to transmit data (SDA). These lines must be
pulled high using pull-up resistors (meaning at rest, there should be 5V between these lines and the ground).


Multiplexer
===========

Multiplexer are used to address multiple electrodes. For this they use **relays**
to create an electronic path between the electrode and the entry (A, B, M, or N) on the
measurement board. The relays are usually controlled by **GPIO expander** (MCP23017).
Because too many GPIO expander cannot be addressed on the same I2C bus, we use a
**I2C expander** (TCAXXXX) which is itself connected via I2C to the controller (rapsberrypi).
