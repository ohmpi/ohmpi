Infiltration below hedges
***************************************

Fieldwork Date: January 29, 30, 31 and February 1, 2024. 

Location: Pollionnay 

Participants: Hanifa Bader, Remi Clement, Jean Marcais, Nadia Carluer, Laurent Lassabatere, Fanny Courapied, Arnold Imig, Arnaud Watlet, Claire Lauvernet, Adrien Bonnefoy


Abstract
======
The primary goal of this mission was to install an Electrical Resistivity Tomography (ERT) system on a hedge in Pollionnay. This system aims to provide detailed images of the soils electrical resistivity distribution and enable remote control of these geoelectric monitoring devices. Ultimately, the objective is to observe significant temporal variations caused by environmental, hydraulic, and meteorological phenomena affecting the structure. This report details the ERT instrumentation activities conducted both in the laboratory and on-site from January 29 to February 1, 2024, to establish a progress report.

I.	Introduction
================
Electrical Resistivity Tomography (ERT) is a effective geophysical method used to characterize the electrical properties of subsurfaces. It is applied in the field to map the electrical structure of the subsurface at a given time. To understand flow movements and rapid variations in water transfers at fine time scales due to changing environmental conditions, the method of “Electrical Resistivity Tomography (ERT) in time-based monitoring” is particularly suitable. When used in time-based monitoring mode, it facilitates the study of infiltration processes under a hedge located in a long-term observation basin near Lyon, France (Lagouy et al., 2015).
In our context, the development of open-source resistivity meters, such as Ohmpi (Clement et al., 2020), enables intensive monitoring of hydrological processess.
This documentation aims to provide a detailed view of the installation process of an ERT system made on January 29, 30, 31 and February 1, 2024. It includes the design of the system integrating an Ohmpi resistivity meter, the wiring diagram, the electrode layout, an illustration of the control cabinet, as well as the recommended monthly tests. 

II.	Presentation of the site
============================
The Yzeron watershed, situated west of Lyon, has been monitored for many years by INRAE, as part of the OTHU and serves as a workshop site for the Rhone Watershed Workshop Zone. This area includes several hedges, with the specific hedge we aim to study located in Pollionnay. The terrain here is inclined with three different slopes, ranging between 4% and 5%. The hedge spans approximately 25 meters in total length, with a denser section of about 8 meters in the middle, as shown in Figure 1.b. 
  
 .. figure:: ../../img/images_hedges/fig1.png
   :width: 100%
   :align: center
   Figure 1: a) Full view of the hedge                b) View of the dense part of the hedge
      
 .. figure:: ../../img/images_hedges/fig3.png
   :width: 100%
   :align: center
   Figure 2: Electromagnetic map showing the location of the study area

   


III.	System Design
===========================

1.	Equipmemnt Selection:
--------------------------

Before installation, a thorough study is conducted to select the appropriate equipment for the study, considering the specifics of the hedge and soil conditions, as well as their compatibility and suitability for the project's specific needs. This includes:

- Electrode Selection:Choosing the right electrodes is crucial for obtaining reliable results. Factors such as soil resistivity, electrode size, and material must be considered to ensure optimal performance.
   
 .. figure:: ../../img/images_hedges/fig4.jpg
   :width: 100%
   :align: center

    
     
 .. figure:: ../../img/images_hedges/fig6.jpg
   :width: 100%
   :align: center

   Figure 3: Photos illustrant la préparation des électrodes en laboratoire.

- •	Selection of cables : 

- •	Selection of batteries :
   
 .. figure:: ../../img/images_hedges/fig7.jpg
   :width: 100%
   :align: center

   Figure 4 : the batteries
- •	Selection of the resistivity meter :
The resistivity meter installed on-site is the OhmPi resistivity meter (Figure 5), a low-cost, open-hardware device designed for measuring electrical resistivity. It features a multiplexer capable of handling measurements from 32 electrodes. The device offers a wide measurement range for current values, from 0.1 mA to 80 mA, and a potential difference measurement range from 0.001 V to 12.00 V. This choice provides several advantages, including its compact size and widespread use in open hardware applications, making it a cost-effective solution (Clement et al., 2020).
   
 .. figure:: ../../img/images_hedges/fig8.png
   :width: 100%
   :align: center

   Figure 5: Laboratory OhmPi resistivity meter setup.

To perform measurements, the OhmPi must be paired with a system that injects current and simultaneously measures both the potential difference and the current. This configuration ensures a comprehensive and efficient acquisition of electrical resistivity data (Clement et al., 2020).

2. Electrode positions Planning
-----------------------------------------------
A detailed analysis of the hedge was conducted to determine the optimal placement of the electrodes based on the sites geometry. This planning was crucial to ensure uniform data collection and optimal resolution.

todo    A map showing the electrode positions

IV.	Site installation:
==================================
1.	Preparation of site:
-----------------------
Before beginning the installation, we conducted thorough site preparation, starting with the setup of the cabinet, trench removal, and marking the electrode locations.

• Cabinet Preparation
The cabinet preparation for the resistivimeter began with the trench removal, followed by leveling the ground and laying a layer of gravel as a base. A layer of sand was added to enhance stability, then the base was concreted according to specifications. The wooden cabin structure was then built, with a sturdy frame anchored to the concrete base, wooden panels for the walls, and a waterproof roof (Figure 3). Final checks were performed to ensure structural stability, equipment security, and the waterproofing of the concrete base, providing an optimal setup for the resistivimeter and easy access to cables and connections.

The cabin housing the resistivimeter must be carefully prepared to ensure the equipment functions correctly. Follow these steps:

    Position the solar panels above the cabin to maximize sunlight exposure.
    Install the batteries in a secure location inside the cabin, ensuring they are properly connected to both the resistivimeter and solar panels.
    Check the electrical connections to confirm they are secure and that no cables are damaged.
     
 .. figure:: ../../img/images_hedges/fig9.png
   :width: 100%
   :align: center

     
 .. figure:: ../../img/images_hedges/fig10.png
   :width: 100%
   :align: center

   Figure 6 : The preparation steps for the cabinet.

• Trench Removal

The removal of trenches for the two electrode lines perpendicular to the hedge was a methodical and precise step in site preparation. First, an accurate layout was established based on the installation plan, determining the exact positions of the electrodes. Then, the trenches were carefully excavated using appropriate tools, maintaining a depth of 10 cm and a width of 20 cm. Once the trenches were completed, precautions were taken to minimize disturbance to the surrounding soil, preserving the stability of the structure and avoiding any unwanted interference with the electrical resistivity measurements. Finally, after the electrodes were installed, the trenches were carefully refilled, restoring the site to its original condition as much as possible. This meticulous approach ensures the site’s integrity while facilitating precise measurements for reliable interpretation of Electrical Resistivity Tomography data.
   
 .. figure:: ../../img/images_hedges/fig11.png
   :width: 100%
   :align: center

   Figure 7 : Removal of trenches on the two lines of electrodes.
   
• Marking Electrode Locations

    Electrode Placement:

The electrode placement stage is a critical procedure requiring precise execution to ensure measurement quality. Initially, trenches were dug at the previously marked locations, ensuring adequate depth for electrode installation. Once the trenches were prepared, the electrodes were positioned horizontally according to the defined layout, ensuring uniform distribution. Special attention was given to the placement of a conductive material ?? around the electrodes to ensure effective soil contact. This material, carefully selected for its conductive properties, was applied in a manner that minimizes any interference that could compromise measurement quality. By combining precise trench digging, accurate electrode positioning, proper application of the conductive material, and sealing all connections between electrodes and electrical wires with silicone, we established optimal conditions for reliable and accurate data collection during the application of Electrical Resistivity Tomography.

 .. figure:: ../../img/images_hedges/fig12.png
   :width: 100%
   :align: center

   Figure 8 : The steps for setting up the electrodes.
3. Wiring Setup:

todo     Wiring Diagram ???


The wiring process between the electrodes and the resistivimeter involves several methodical steps to ensure a stable and reliable connection for accurate data collection. First, cables are laid out from the resistivimeter to the pre-marked electrode locations. Connections between these cables at the OhmPi and between the cables themselves (Figure 9) are selected based on a predefined color-coding system, making it easier to identify connections. At this stage, a special resin is meticulously added to the connection boxes to ensure effective insulation and protection against adverse environmental conditions. This resin also guarantees electrical stability of the connections. The cables are then connected to the OhmPi following the predefined wiring diagram. A thorough check is performed at each step to ensure that all connections are secure and that the system is ready for accurate data collection during the subsequent application of Electrical Resistivity Tomography (ERT). This is achieved by running a sequence to check the contact resistances between the electrodes and the soil, aiming for acceptable values between 1 and 4 kOhms.
    
  
 .. figure:: ../../img/images_hedges/fig13.png
   :width: 100%
   :align: center

 .. figure:: ../../img/images_hedges/fig14.png
   :width: 100%
   :align: center

   Figure 9 : Wiring photo at the connection boxes between the cables and at the level of the cabinet.
   
4. Trench Closure

Once the wiring has been securely fixed and the resin has had time to dry, the first step is to carefully replace the excavated soil back into the trench (Figure 7). Special care is taken to avoid any movement or displacement of the cables and electrodes. Soil compaction is done gradually, in thin layers, to minimize vibrations that could affect the layout of system components. To ensure proper closure, the contact resistance test is repeated at this stage, confirming all values are between 1 and 4 kOhm, indicating correct connections.

It is important to note that this trench closure stage is particularly sensitive, and any shift in electrode positioning could compromise the accuracy of subsequent measurements. Once the trenches are properly closed and the electrodes stabilized, the site is ready for Electrical Resistivity Tomography data collection, ensuring reliable and accurate results.

 .. figure:: ../../img/images_hedges/fig15.png
   :width: 100%
   :align: center

 .. figure:: ../../img/images_hedges/fig16.jpg
   :width: 100%
   :align: center

   Figure 10 : Trench Closure
     
 
V.	Tests 
========
Tests are planned to be conducted on-site by initiating sequences remotely, once daily and multiple times according to weather events such as rainfall. These tests aim to demonstrate the robustness and functionality of the Electrical Resistivity Tomography (ERT) system. They involve remote activation of the geoelectrical monitoring devices, allowing automated data collection without requiring physical intervention on-site, except in cases of fuse and battery replacement. Through these sequences, the system records temporal variations in soil electrical resistivity, providing continuous, real-time monitoring. The results obtained from these tests contribute to observing significant variations caused by environmental, hydraulic, and meteorological phenomena. This automated approach enhances monitoring efficiency, enabling a rapid response to any notable changes while minimizing site disruptions. These regular tests play a vital role in the system’s ongoing validation and contribute to acquiring reliable data for an in-depth analysis of soil conditions around the hedgerow in Pollionnay.

VI.	Conclusion and perspective
===============================
In conclusion, the successful implementation of Electrical Resistivity Tomography (ERT) on the hedgerow in Pollionnay has yielded valuable data on soil electrical resistivity distribution. Instrumentation actions carried out in the laboratory and on-site demonstrated the systems reliability in automated data collection, thus strengthening continuous geoelectrical environmental monitoring.

Looking ahead, we plan to implement a measurement triggering strategy based on regular intervals, particularly during critical periods. This approach will combine continuous measurements with spot observations, aiming to capture soil changes at different temporal scales. Additionally, the goal is to minimize acquisition time while ensuring adequate temporal coverage. To further optimize measurement efficiency, an optimization sequence is under consideration. Acquiring rapid profiles becomes imperative, especially to track hydrological events such as heavy rainfall, soil infiltration, or groundwater level variations. This will allow measurements to be repeated following a "time-lapse" principle, providing an evolving temporal representation. This proactive approach will enable more precise management of environmental events impacting the Pollionnay hedgerow, while optimizing the collection of geoelectrical data.



.. figure:: ../../../img/mb.2024.x.x/10.jpg
   :width: 100%
   :align: center

   Caption


