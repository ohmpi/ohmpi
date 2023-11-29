Software interface to new hardware components
=============================================

*** DRAFT VERSION - TO BE REVIEWED *
This section is intended for developers of a new hardware component as part of an OhmPi system.

It presents some advices and best practices that should help developing new hardware components to work
within an OhmPi system.

OhmPi is an open source system and contributions in terms of hardware and software are welcome. However, in order to
maintain the project on tracks and promote exchange and reuse, it is necessary that contributors
Developing a new hardware component should ideally follow a few basic steps.

Two cases should be distinguished when dealing with hardware development components:

1- Developments of a hardware component that comply with the way the OhmPi Hardware System works. Such developments typically
focus on improving an existing component (reduce cost, improve performance, adapt range to specific applications,
design with easily available parts...). The newly created hardware component will expose the minimal functionalities required
by hardware_system for this type of component.

2- Developments of a hardware component that introduce changes in the way the OhmPi Hardware System works. Such
developments do not only focus on improving a single component but also on the way to operate the system. A
discussion with developers of the OhmPi_Hardware and OhmPi classes should be initiated at a very early stage to investigate
the best ways to design and implement a working solution.

If you are dealing with case 1 or have designed a development path and strategy, you are ready to start.

First the hardware board/device should be conceived and designed. The Ohmpi team recommends that contributors design or
import their boards within KiCAD and that both schemas and PCB are shared.

When developing a new component Class, always start your development in a new branch.
1- Create a new python file or make a copy and modify an existing similar component file. All hardware component modules
are stored in the ohmpi/hardware_component directory.
In the newly created python file, define a new class based on the relevant abstract class of abstract_hardware_components.py.
Implement the abstract methods to interact with your hardware. Name the file according to the name of the component.
Make sure to place this new python module in the ohmpi/hardware_component directory.

2- Create a new configuration file or make a copy and modify an existing configuration file. All existing config files
are stored in the ohmpi/hardware_component directory.
In this newly created config file, describe your system including the new component in the HARDWARE_CONFIG dictionary.
Name it config_XXX.py where XXX should be replaced by an expression describing the system.
Make sure to place your new config file in the ohmpi/configs directory.

3- Create a new script or make a copy and modify of an existing script for testing the component.
In this script, write python code where you will conduct the tests of the required functionalities of the new component.

