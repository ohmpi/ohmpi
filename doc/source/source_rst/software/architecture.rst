Software architecture
#####################

The OhmPi v2024 software has been completely re-structured to enable increased flexibility for both users and developers. The software is based on an object-oriented module with a class exposing the OhmPi
functionalities used to interact with the OhmPi instrument via a web interface, IoT
communication protocols (e.g. MQTT) and/or directly through the Python API.

.. figure:: ../../img/software/ohmpi_2024_architecture.png
   :width: 1000px

     Software architecture of OhmPi v2024.

The software is organised in several modules describing the system in a hierarchy including three levels of description and
operation of the OhmPi.

Acquisition
***********
On the top level, the ``OhmPi`` class (in ohmpi/ohmpi.py) includes all the higher-level methods and properties allowing to
operate the system (e.g. acquire measurement sequences). The OhmPi class exposes the user-oriented
API, generates logs and handles IoT messages. Generic users are expected to interact with the system
through these higher-level functionalities, which are designed to remain as stable as possible while the
hardware evolves. Only the introduction of new end-user functionalities should imply new
developments at this level.

Hardware system
***************
On the medium level, the ``OhmPiHardware`` class provides a mean to assemble and operate the
acquisition system. The methods of this class orchestrate atomic operations of the system components
in order to expose basic system functionalities such as cross-MUX switching, square wave voltage
injection or full waveform voltage and current reading during injection cycles. These functionalities
are implemented using synchronization mechanisms between threads in order to insure that each
component keeps in step with the others.
The whole system is described in a *configuration file* listing the hardware components and versions
used. Through a dynamic import mechanism the modules containing the classes corresponding with
the physical hardware modules of a particular OhmPi system are instantiated and associated with the
system object instantiated from the OhmPiHardware class. In this way, it is relatively simple to build
customised systems once the concrete classes describing the system components have been written.
This part of the software architecture should remain stable if the overall system functionalities do not
evolve. However, the introduction of new functionalities at the system level or radical changes in the
way the components work together will require adaptations at this level.


Hardware components
*******************
On the base level, the five main hardware components are represented by distinct classes exposing the
components atomic functionalities. Theses classes are abstract classes in order to provide a common
interface for different implementations of a component. From these abstract classes concrete classes
are implemented representing the default properties, actual capabilities and ways to interact with the
physical modules or boards.
Improving an existing hardware component or introducing a new design may be desirable in order to,
e.g. reduce costs, improve performance, adapt measurement range to specific applications, or
incorporate easily available electronic components. It is at this level that software developments are
mainly expected to occur following updates on the hardware. The component class should expose the
minimal functionalities required by the hardware system for this type of component.