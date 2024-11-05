OhmPi to explore infiltration on hedges
***************************************

Compte Rendu de Mission: Installation de la Tomographie de Résistivité Électrique avec Ohmpi sur la Haie
========================================================================================================

Date de la Mission: 29, 30, 31 janvier et 1 février 2024.
Lieu: Pollionnay
Participants:
Hanifa Bader, Remi Clement, Jean Marcais, Nadia Carluer, Laurent Lassabatere, Fanny Courapied, Arnold Imig, Arnaud Watlet, Claire Lauvernet, Adrien Bonnefoy




RÉSUMÉ
======
L’objectif principal de cette mission était d'installer un système de Tomographie de Résistivité Électrique (ERT) sur une haie à Pollionnay, dans le but d'obtenir des images détaillées de la distribution des résistivités électriques du sol, tout en permettant le pilotage à distance de ces dispositifs de monitoring géoélectrique. L'objectif ultime était d'observer les variations temporelles significatives générées par les phénomènes environnementaux, hydrauliques et météorologiques auxquels l’ouvrage est exposé. Ce rapport présente les actions d’instrumentation ERT menées au laboratoire et sur le site (29, 30, 31 janvier et 1 février 2024), visant à établir un bilan d’étape.
MOTS-CLEFS
Monitoring géoélectrique, tomographie de résistivité électrique, Ohmpi, instrumentation, haies.


Table des matières
==================
I.	Introduction	3
II.	Présentation du site	3
III.	Conception du Système	4
1.	Choix de l'Équipement:	4
2.	Planification de disposition des électrodes:	6
IV.	Installation sur le Terrain:	7
1.	Préparation du Site:	7
2.	Mise en Place des Électrodes:	10
3.	Mise en Place du Câblage:	11
4.	Fermeture des tranchées	13
V.	Tests	15
VI.	Conclusion	15


I.	Introduction
===============
La tomographie de résistivité électrique (ERT) représente une méthode géophysique puissante qui permet la caractérisation des propriétés électriques des sous-sols. Elle est appliquée sur le terrain pour caractériser la structure électrique du sous-sol à un instant t donné. Dans le but de caractériser les mouvements d'eau et les variations rapides des transferts hydriques à des échelles temporelles fines en réponse aux conditions environnementales changeantes, la méthode électrique « Tomographie de Résistivité Électrique (ERT) en suivi temporel parait adaptée. Utilisée en mode de suivi temporel, elle facilite l'étude des processus d'infiltration sous une haie située dans un bassin d'observation à long terme près de Lyon, France (Lagouy et al., 2015). Dans notre contexte, en considérant que le développement des résistivimètre en source ouverte, tels qu'Ohmpi (Clement et al., 2020), offre la possibilité de surveiller de manière intensive les processus hydrologiques.
Cette documentation vise à fournir une vue détaillée du processus d'installation d'un système ERT faite le 29, 30, 31 janvier et 1 février 2024. Elle englobe la conception du système intégrant un résistivimètre Ohmpi, le schéma de câblage, la disposition des électrodes, une illustration de l'armoire de contrôle, ainsi que les tests mensuels recommandés.

II.	Présentation du site
==========================
Le bassin de l’Yzeron, situé dans l’ouest lyonnais, est suivi depuis de nombreuses années par INRAE, dans le cadre de l’OTHU, site atelier de la Zone Atelier Bassin du Rhone.  Il comporte des haies, et celle que nous souhaitons étudier se trouve à Pollionnay sur un terrain incliné selon trois pentes différentes, variant entre 4 et 5 %. Sa longueur totale est d'environ 25 mètres, avec 8 mètres de densité plus forte au milieu, comme illustré dans la Figure 1.b. 
  
 .. figure:: ../../../img/images_hedges/fig1.png
   :width: 100%
   :align: center

   Caption
     
 .. figure:: ../../../img/images_hedges/fig2.png
   :width: 100%
   :align: center

   Caption
     
 .. figure:: ../../../img/images_hedges/fig3.png
   :width: 100%
   :align: center

   Caption
Figure 2 : Carte électromagnétique de localisation de la zone d’étude


III.	Conception du Système
===========================

1.	Choix de l'Équipement:
-------------------------
Avant l'installation, une étude approfondie est faite par sélectionner le matériel approprié pour la mission, en prenant en compte les spécificités de la haie et des conditions du sol, ainsi leur compatibilité et de leur adéquation aux besoins spécifiques du projet. 
Cela inclut : 
•	Le choix des électrodes :  
La sélection des électrodes est intéressante pour obtenir des résultats fiables. Considérez la résistivité du sol et choisissez des électrodes appropriées, en tenant compte de la taille, et du matériau.
  
   
 .. figure:: ../../../img/images_hedges/fig4.png
   :width: 100%
   :align: center

   Caption
     
 .. figure:: ../../../img/images_hedges/fig5.png
   :width: 100%
   :align: center

   Caption
     
 .. figure:: ../../../img/images_hedges/fig6.png
   :width: 100%
   :align: center

   Caption
Figure 3: Photos illustrant la préparation des électrodes en laboratoire.

- •	Le choix des câbles : 

- •	Le choix des batteries :
   
 .. figure:: ../../../img/images_hedges/fig7.png
   :width: 100%
   :align: center

   Caption
Figure 4 : Les batteries
- •	Le choix du résistivimètre :
Un résistivimètre installe sur site est le résistivimètre OhmPi (Figure 2) qui est un appareil à faible coût, présentant du matériel ouvert (hardware), pour mesurer la résistivité électrique. Il intègre un multiplexeur permettant des mesures sur 32 électrodes. Les capacités de l'appareil comprennent une large plage de mesure pour les valeurs de courant, s'étendant de 0,1 mA à 80 mA, et une plage de mesure de la différence de potentiel de 0,001 V à 12,00 V. Ce choix offre des avantages tels qu'une taille compacte et une utilisation répandue dans les applications matérielles ouvertes, contribuant à un ratio coût/efficacité attractif. (Clement et al. 2020)
   
 .. figure:: ../../../img/images_hedges/fig8.png
   :width: 100%
   :align: center

   Caption 
Figure 5: Disposition de résistivimètre OhmPi de laboratoire
Pour effectuer des mesures, le OhmPi doit être associé à un système chargé d'injecter du courant et de mesurer simultanément la différence de potentiel et le courant. Cette configuration garantit une acquisition complète et efficace des données de résistivité électrique. (Clement et al. 2020)
2.	Planification de disposition des électrodes:
-----------------------------------------------
Une analyse détaillée de la haie a été effectuée pour déterminer la disposition optimale des électrodes en fonction de la géométrie du site. Cette planification a été cruciale pour garantir une collecte de données homogène et une résolution optimale.

Une carte avec la position des électrodes


IV.	Installation sur le Terrain:
==================================
1.	Préparation du Site:
-----------------------
Avant de commencer l'installation, nous avons procédé à une préparation minutieuse du site en commençant par la préparation de la cabine, l'enlèvement des tranchées et le marquage des emplacements des électrodes.
•	Préparation de la Cabine
La préparation de la cabine pour le résistivimètre a débuté par l'enlèvement de tranchées, suivies de l'aplanissement du sol et de la pose d'une couche de cailloux comme base. Une couche de sable a été ajoutée pour améliorer la stabilité, puis la base a été bétonnée conformément aux spécifications. La construction de la maison de cabine en bois a suivi, avec un cadre robuste fixé à la base en béton, des panneaux en bois pour les parois, et un toit étanche (Figure 3). Des vérifications finales ont été effectuées pour garantir la stabilité de la structure, la sécurité du matériel, et l'étanchéité de la base en béton, assurant ainsi une installation optimale pour le résistivimètre et un accès pratique aux câbles et aux connexions.
La cabine qui abrite le résistivimètre doit être préparée soigneusement pour assurer le bon fonctionnement de l'équipement. Suivez ces étapes :
-	Placement des panneaux solaires au-dessus de la cabine de manière à maximiser l'exposition au soleil. 
-	Installation des batteries dans un endroit sécurisé à l'intérieur de la cabine en s’assurant qu'elles sont correctement connectées au résistivimètre et aux panneaux solaires.
-	Vérifiant les connexions électriques pour assurer qu'elles sont sécurisées et qu'il n'y a pas de câbles endommagés.
   
     
 .. figure:: ../../../img/images_hedges/fig9.png
   :width: 100%
   :align: center

   Caption
     
 .. figure:: ../../../img/images_hedges/fig10.png
   :width: 100%
   :align: center

   Caption
Figure 6 : Les étapes de préparation de la cabine  
•	Enlèvement des tranchées
L'enlèvement des tranchées pour les deux lignes d'électrodes perpendiculaires à la haie a été une étape méthodique et précise de la préparation du site. Tout d'abord, un tracé précis a été établi en fonction du plan d'installation, déterminant les positions exactes des électrodes. Ensuite, les tranchées ont été excavées avec soin en utilisant des outils appropriés, en veillant à maintenir une profondeur de 10 cm et une largeur de 20 cm. Une fois les tranchées réalisées, des précautions ont été prises pour minimiser les perturbations du sol environnant, préservant ainsi la stabilité de la structure et évitant toute interférence indésirable avec les mesures de résistivité électrique. Enfin, les tranchées ont été soigneusement refermées après l'installation des électrodes, restaurant ainsi le site à son état initial autant que possible. Cette démarche méticuleuse garantit l'intégrité du site tout en facilitant la prise de mesures précises pour une interprétation fiable des données de la Tomographie de Résistivité Électrique.
   
 .. figure:: ../../../img/images_hedges/fig11.png
   :width: 100%
   :align: center

   Caption
   
Figure 7 : Enlèvement des tranchées sur les deux lignes de électrodes.
•	Marquage des emplacements des électrodes

2.	Mise en Place des Électrodes:
--------------------------------
L'étape de l'emplacement des électrodes est une procédure critique qui nécessite une exécution précise pour assurer la qualité des mesures. Initialement, des tranchées ont été creusées aux emplacements préalablement marqués, assurant une profondeur adéquate pour la disposition des électrodes. Une fois les tranchées préparées, les électrodes ont été positionnées horizontalement selon le schéma défini, garantissant une distribution uniforme. Une attention particulière a été accordée à la mise en place de matière conductrice ?? autour des électrodes pour assurer une connexion efficace avec le sol. Cette matière, soigneusement sélectionnée pour ses propriétés conductrices, a été déployée de manière à minimiser toute interférence qui pourrait compromettre la qualité des mesures. En combinant le creusement précis des tranchées, la disposition précise des électrodes, l'application adéquate de matière conductrice, et la fermeture de toutes les connexions entre les électrodes et les fils électriques par le silicone, nous avons établi des conditions optimales pour la collecte de données fiables et précises lors de l'application de la Tomographie de Résistivité Électrique.

3.	Mise en Place du Câblage:
----------------------------
Schéma de Câblage ???
Le processus de câblage entre les électrodes et le résistivimètre implique plusieurs étapes méthodiques, visant à assurer une connexion stable et fiable pour la collecte précise des données. Tout d'abord, les câbles sont déployés depuis le résistivimètre vers les emplacements préalablement marqués des électrodes. La connexion de ces câbles au niveau de l'OhmPi et entre les câbles eux-mêmes (Figure 9) est choisie en fonction d'un catalogue de couleurs prédéfini, simplifiant ainsi l'identification des connexions. À ce stade, une résine spéciale est méticuleusement ajoutée dans les boîtes de connexion pour assurer une isolation efficace et une protection contre les conditions environnementales adverses. Cette résine garantit également la stabilité électrique des connexions. Les câbles sont ensuite connectés à l’OhmPi en suivant le schéma de câblage prédéfini. Une vérification minutieuse est effectuée à chaque étape pour s'assurer que toutes les connexions sont sécurisées et que le système est prêt à collecter des données précises lors de l'application ultérieure de la Tomographie de Résistivité Électrique (ERT). Cela est atteint en lançant une séquence qui cherche les résistances de contact entre les électrodes et le sol qui donne des valeurs acceptables entre 1 et 4 kOhm.
    

   
Figure 9 : Photo de câblage au niveau des boites de connections entre les câbles  et au niveau de l'Armoire
4.	Fermeture des tranchées 
--------------------------
Une fois que le câblage a été soigneusement fixé et que la résine a eu le temps de sécher, la première étape consiste à replacer délicatement le sol excavé dans la tranchée (Figure 7). Une attention particulière est accordée pour éviter tout mouvement ou déplacement des câbles et des électrodes. La compaction du sol se fait progressivement, en couches fines, pour minimiser les vibrations susceptibles d'affecter la disposition des éléments du système. Pour garantir une fermeture adéquate, une répétition du test des résistances de contact est effectuée à cette étape, où toutes les valeurs se situent entre 1 et 4 kOhm, confirmant une connexion correcte.
Il est impératif de noter que cette étape de fermeture de tranchée est particulièrement sensible, et tout changement de position des électrodes pourrait compromettre la précision des mesures ultérieures. Une fois les tranchées correctement refermées et les électrodes stabilisées, le site est prêt pour la collecte de données de Tomographie de Résistivité Électrique, assurant ainsi des résultats fiables et précis.

     
 
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


