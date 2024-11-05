Infiltration below hedges</wrap>
***************************************

Fieldwork Date: January 29, 30, 31 and February 1, 2024. 

Location: Pollionnay 

Participants: Hanifa Bader, Remi Clement, Jean Marcais, Nadia Carluer, Laurent Lassabatere, Fanny Courapied, Arnold Imig, Arnaud Watlet, Claire Lauvernet, Adrien Bonnefoy


Abstract
======
The primary goal of this mission was to install an Electrical Resistivity Tomography (ERT) system on a hedge in Pollionnay. This system aims to provide detailed images of the soil’s electrical resistivity distribution and enable remote control of these geoelectric monitoring devices. Ultimately, the objective is to observe significant temporal variations caused by environmental, hydraulic, and meteorological phenomena affecting the structure. This report details the ERT instrumentation activities conducted both in the laboratory and on-site from January 29 to February 1, 2024, to establish a progress report.

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

      
 .. figure:: ../../img/images_hedges/fig3.png
   :width: 100%
   :align: center

   Figure 2 : Carte électromagnétique de localisation de la zone d’étude


III.	System Design
===========================

1.	Equipmemnt Selection:
--------------------------

Before installation, a thorough study is conducted to select the appropriate equipment for the study, considering the specifics of the hedge and soil conditions, as well as their compatibility and suitability for the project's specific needs. This includes:

- Electrode Selection:Choosing the right electrodes is crucial for obtaining reliable results. Factors such as soil resistivity, electrode size, and material must be considered to ensure optimal performance.
   
 .. figure:: ../../img/images_hedges/fig4.jpg
   :width: 50%
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

   Figure 4 : Les batteries
- •	Selection of the resistivity meter :
The resistivity meter installed on-site is the OhmPi resistivity meter (Figure 5), a low-cost, open-hardware device designed for measuring electrical resistivity. It features a multiplexer capable of handling measurements from 32 electrodes. The device offers a wide measurement range for current values, from 0.1 mA to 80 mA, and a potential difference measurement range from 0.001 V to 12.00 V. This choice provides several advantages, including its compact size and widespread use in open hardware applications, making it a cost-effective solution (Clement et al., 2020).
   
 .. figure:: ../../img/images_hedges/fig8.png
   :width: 100%
   :align: center

   Figure 5: Disposition de résistivimètre OhmPi de laboratoire

To perform measurements, the OhmPi must be paired with a system that injects current and simultaneously measures both the potential difference and the current. This configuration ensures a comprehensive and efficient acquisition of electrical resistivity data (Clement et al., 2020).

2. Electrode positions Planning
-----------------------------------------------
A detailed analysis of the hedge was conducted to determine the optimal placement of the electrodes based on the site’s geometry. This planning was crucial to ensure uniform data collection and optimal resolution.

A map showing the electrode positions

IV.	Installation sur le Terrain:
==================================
1.	Préparation du Site:
-----------------------
Before beginning the installation, we conducted thorough site preparation, starting with the setup of the cabin, trench removal, and marking the electrode locations.

• Cabin Preparation
The cabin preparation for the resistivimeter began with the trench removal, followed by leveling the ground and laying a layer of gravel as a base. A layer of sand was added to enhance stability, then the base was concreted according to specifications. The wooden cabin structure was then built, with a sturdy frame anchored to the concrete base, wooden panels for the walls, and a waterproof roof (Figure 3). Final checks were performed to ensure structural stability, equipment security, and the waterproofing of the concrete base, providing an optimal setup for the resistivimeter and easy access to cables and connections.

The cabin housing the resistivimeter must be carefully prepared to ensure the equipment functions correctly. Follow these steps:

    Position the solar panels above the cabin to maximize sunlight exposure.
    Install the batteries in a secure location inside the cabin, ensuring they are properly connected to both the resistivimeter and solar panels.
    Check the electrical connections to confirm they are secure and that no cables are damaged.
     
 .. figure:: ../../img/images_hedges/fig9.png
   :width: 100%
   :align: center

   Caption
     
 .. figure:: ../../img/images_hedges/fig10.png
   :width: 100%
   :align: center

   Figure 6 : Les étapes de préparation de la cabine  

•	Enlèvement des tranchées
L'enlèvement des tranchées pour les deux lignes d'électrodes perpendiculaires à la haie a été une étape méthodique et précise de la préparation du site. Tout d'abord, un tracé précis a été établi en fonction du plan d'installation, déterminant les positions exactes des électrodes. Ensuite, les tranchées ont été excavées avec soin en utilisant des outils appropriés, en veillant à maintenir une profondeur de 10 cm et une largeur de 20 cm. Une fois les tranchées réalisées, des précautions ont été prises pour minimiser les perturbations du sol environnant, préservant ainsi la stabilité de la structure et évitant toute interférence indésirable avec les mesures de résistivité électrique. Enfin, les tranchées ont été soigneusement refermées après l'installation des électrodes, restaurant ainsi le site à son état initial autant que possible. Cette démarche méticuleuse garantit l'intégrité du site tout en facilitant la prise de mesures précises pour une interprétation fiable des données de la Tomographie de Résistivité Électrique.
   
 .. figure:: ../../img/images_hedges/fig11.png
   :width: 100%
   :align: center

   Figure 7 : Enlèvement des tranchées sur les deux lignes de électrodes.
   
•	Marquage des emplacements des électrodes

2.	Mise en Place des Électrodes:
--------------------------------
L'étape de l'emplacement des électrodes est une procédure critique qui nécessite une exécution précise pour assurer la qualité des mesures. Initialement, des tranchées ont été creusées aux emplacements préalablement marqués, assurant une profondeur adéquate pour la disposition des électrodes. Une fois les tranchées préparées, les électrodes ont été positionnées horizontalement selon le schéma défini, garantissant une distribution uniforme. Une attention particulière a été accordée à la mise en place de matière conductrice ?? autour des électrodes pour assurer une connexion efficace avec le sol. Cette matière, soigneusement sélectionnée pour ses propriétés conductrices, a été déployée de manière à minimiser toute interférence qui pourrait compromettre la qualité des mesures. En combinant le creusement précis des tranchées, la disposition précise des électrodes, l'application adéquate de matière conductrice, et la fermeture de toutes les connexions entre les électrodes et les fils électriques par le silicone, nous avons établi des conditions optimales pour la collecte de données fiables et précises lors de l'application de la Tomographie de Résistivité Électrique.
  
 .. figure:: ../../img/images_hedges/fig12.png
   :width: 100%
   :align: center

   Figure 8 : Les étapes de la mise en place des électrodes
3.	Mise en Place du Câblage:
----------------------------
Schéma de Câblage ???
Le processus de câblage entre les électrodes et le résistivimètre implique plusieurs étapes méthodiques, visant à assurer une connexion stable et fiable pour la collecte précise des données. Tout d'abord, les câbles sont déployés depuis le résistivimètre vers les emplacements préalablement marqués des électrodes. La connexion de ces câbles au niveau de l'OhmPi et entre les câbles eux-mêmes (Figure 9) est choisie en fonction d'un catalogue de couleurs prédéfini, simplifiant ainsi l'identification des connexions. À ce stade, une résine spéciale est méticuleusement ajoutée dans les boîtes de connexion pour assurer une isolation efficace et une protection contre les conditions environnementales adverses. Cette résine garantit également la stabilité électrique des connexions. Les câbles sont ensuite connectés à l’OhmPi en suivant le schéma de câblage prédéfini. Une vérification minutieuse est effectuée à chaque étape pour s'assurer que toutes les connexions sont sécurisées et que le système est prêt à collecter des données précises lors de l'application ultérieure de la Tomographie de Résistivité Électrique (ERT). Cela est atteint en lançant une séquence qui cherche les résistances de contact entre les électrodes et le sol qui donne des valeurs acceptables entre 1 et 4 kOhm.
    
  
 .. figure:: ../../img/images_hedges/fig13.png
   :width: 100%
   :align: center

   Caption
     
 .. figure:: ../../img/images_hedges/fig14.png
   :width: 100%
   :align: center

   Figure 9 : Photo de câblage au niveau des boites de connections entre les câbles  et au niveau de l'Armoire
   
4.	Fermeture des tranchées 
--------------------------
Une fois que le câblage a été soigneusement fixé et que la résine a eu le temps de sécher, la première étape consiste à replacer délicatement le sol excavé dans la tranchée (Figure 7). Une attention particulière est accordée pour éviter tout mouvement ou déplacement des câbles et des électrodes. La compaction du sol se fait progressivement, en couches fines, pour minimiser les vibrations susceptibles d'affecter la disposition des éléments du système. Pour garantir une fermeture adéquate, une répétition du test des résistances de contact est effectuée à cette étape, où toutes les valeurs se situent entre 1 et 4 kOhm, confirmant une connexion correcte.
Il est impératif de noter que cette étape de fermeture de tranchée est particulièrement sensible, et tout changement de position des électrodes pourrait compromettre la précision des mesures ultérieures. Une fois les tranchées correctement refermées et les électrodes stabilisées, le site est prêt pour la collecte de données de Tomographie de Résistivité Électrique, assurant ainsi des résultats fiables et précis.
  
 .. figure:: ../../img/images_hedges/fig15.png
   :width: 100%
   :align: center

   Caption
     
 .. figure:: ../../img/images_hedges/fig16.png
   :width: 100%
   :align: center

   Figure 10 ; Fermeture des tranchées
     
 
V.	Tests 
========
Des tests sont envisagés d'être effectués sur site en lançant des séquences à distance, une seule fois chaque jour et plusieurs fois selon les événements climatiques tels que les précipitations. Ces tests visent à démontrer la robustesse et la fonctionnalité du système de Tomographie de Résistivité Électrique (ERT). Ils consistent en l'activation à distance des dispositifs de monitoring géoélectrique, permettant une collecte automatisée de données sans nécessiter une intervention physique sur le site, sauf dans le cas de changement des fusibles et des batteries. À travers ces séquences, le système enregistre les variations temporelles des résistivités électriques du sol, offrant ainsi une surveillance continue et en temps réel. Les résultats obtenus à partir de ces tests contribuent à l'observation des variations significatives générées par les phénomènes environnementaux, hydrauliques et météorologiques. Cette approche automatisée renforce l'efficacité du suivi, permettant une réactivité rapide face à tout changement notable, tout en minimisant les perturbations sur le site. Ces tests réguliers jouent un rôle essentiel dans la validation continue du système et contribuent à l'obtention de données fiables pour une analyse approfondie des conditions du sol autour de la haie à Pollionnay.
VI.	Conclusion et perspective
===============================
En conclusion, la mise en œuvre réussie de la Tomographie de Résistivité Électrique (ERT) sur la haie à Pollionnay a permis d'obtenir des données significatives sur la distribution des résistivités électriques du sol. Les actions d'instrumentation effectuées au laboratoire et sur le site ont démontré la fiabilité du système dans la collecte automatisée des données, renforçant ainsi la surveillance continue de l'environnement géoélectrique.
En perspective, nous envisageons d'implémenter une stratégie de déclenchement des mesures basée sur des intervalles réguliers, particulièrement durant les périodes critiques. Cette approche sera caractérisée par la combinaison de mesures continues et d'observations ponctuelles, visant à capturer les évolutions du sol à différentes échelles temporelles. En plus, l'objectif est de minimiser le temps d'acquisition tout en garantissant une couverture temporelle adéquate. Pour optimiser davantage l'efficacité des mesures, une séquence d'optimisation est envisagée. Il devient impératif, notamment pour suivre les épisodes hydrologiques tels que les pluies abondantes, les infiltrations dans le sol, ou les variations des nappes phréatiques, d'acquérir rapidement un profil afin de permettre la répétition des mesures selon le principe d'un "time-lapse" et d'obtenir ainsi une représentation temporelle évolutive. Cette approche proactive permettra une gestion plus précise des événements environnementaux impactant la haie à Pollionnay, tout en optimisant la collecte des données géoélectriques.


some test


.. figure:: ../../../img/mb.2024.x.x/10.jpg
   :width: 100%
   :align: center

   Caption


