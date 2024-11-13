***************
System Overview
***************

    .. image:: ../../img/logo/ohmpi/LOGO_OHMPI.png
        :align: center
        :width: 336px
        :height: 188px
        :alt: Logo OhmPi

.. warning::
    OhmPi is a participative project open to all, it requires skills in electronics and to respect the safety rules.
    OhmPi must be assembled in a professional context and by people competent in electronics. The OhmPi team cannot be
    held responsible for any material or human damage which would be associated with the use or the assembly of OhmPi.
    The OhmPi team cannot be held responsible if the equipment does not work after assembly. You may redistribute and
    modify this documentation and make products using it under the terms of the CERN-OHL-P v2. This documentation is
    distributed WITHOUT ANY EXPRESS OR IMPLIED WARRANTY, INCLUDING OF MERCHANTABILITY, SATISFACTORY QUALITY AND FITNESS
    FOR A PARTICULAR PURPOSE. Please see the CERN-OHL-P v2 for applicable conditions.


What is OhmPi?
**************

The OhmPi project was initiated to develop an open-source, open-hardware resistivity meter,
particularly designed for the research community, education, and humanitarian or not-for-profit organisations.
In the last decade, geoelectrical monitoring has become a popular tool to study and monitor
physical processes in hydrology. As novel applications emerge, the need for more accessible and flexible acquisition systems
grows in the research community. The flexibility and adaptability of OhmPi makes it particularly suited to
develop novel acquisition strategies or design innovative small-scale monitoring experiments.

.. note::
   Anyone who wants to get involved is welcome to join the OhmPi project!

How does it work?
*****************

The OhmPi is composed of different modules:

- a measurements board (``mb``): that measures the current and voltage and modulates the injected current
- 0, 1, ... or n multiplexer boards (``mux``): that address different electrodes
- a power supply (``pwr``): either a 12V battery or a more advanced power supply where we can control the voltage/current
- a general controller (``ctrl``): to control the measurement board, multiplexer boards and power supply (=raspberrypi)

These module exists in different versions and can be combined using a configuration file.
You can then upgrade your measurement board or power supply for specific applications.

.. figure:: ../../img/Hardware_structure.png
  :width: 1000px
  :align: center

  OhmPi hardware flowchart.

In "BUILD OHMPI BOARDS" section we detail how to build each single module of an OHMPI system.



How does it look like?
**********************

.. warning::
    We **strongly** recommend to test the assembled system in a controlled environment (in the lab, on resistor boards) before deploying
    in the field!

.. image:: ../../img/ohmpi_systems_examples.jpg
   :width: 900px
   :align: center

Recommended configurations
__________________________

+-------------------------------+--------------------------------+--------------------+--------------------------+--------------------------+--------------------------------------------------+
|Applications                   |Measurement Board               |Mux                 |Raspberry Pi              | Power supply             |Config file name                                  |
+-------------------------------+--------------------------------+--------------------+--------------------------+--------------------------+--------------------------------------------------+
| | 64 or more electrodes       |mb v2024                        |Mux v2023           | | Raspberry Pi 3 Model B | DPH5005                  | config_mb_2024_0_2__4_mux_2023_dph5005.py        |
| | for field monitoring        |                                |                    | | or 4 model B           |                          |                                                  |
+-------------------------------+--------------------------------+--------------------+--------------------------+--------------------------+--------------------------------------------------+
| | 8, 16, 32, 48 electrodes    |mb v2024                        |Mux v2024           | | Raspberry Pi 3 Model B | DPH5005                  | config_mb_2024_0_2__4_mux_2024_2roles_dph5005.py |
| | for field monitoring        |                                |                    | | or 4 model B           |                          |                                                  |
+-------------------------------+--------------------------------+--------------------+--------------------------+--------------------------+--------------------------------------------------+
| | 8, 16, 32, 48 electrodes    |mb v2024                        |Mux v2024           | | Raspberry Pi 3 Model B | 12V Battery              | config_mb_2024_0_2__4_mux_2024_2roles.py         |
| | for laboratory monitoring   |                                |                    | | or 4 model B           |                          |                                                  |
+-------------------------------+--------------------------------+--------------------+--------------------------+--------------------------+--------------------------------------------------+
| | 4 electrodes concrete sample|mb v2024                        |None                |Raspberry Pi 3 Model B    | DPH5005                  | config_mb_2024_0_2_dph5005.py                    |
| | Laboratory (Rhoa and IP)    |                                |                    |                          |                          |                                                  |
+-------------------------------+--------------------------------+--------------------+--------------------------+--------------------------+--------------------------------------------------+
| | 4 electrodes soil sample    |mb v2024                        |None                |Raspberry Pi 3 Model B    | 12V Battery              | config_mb_2024_0_2.py.                           |
| | laboratory (Rhoa and IP)    |                                |                    |                          |                          |                                                  |
+-------------------------------+--------------------------------+--------------------+--------------------------+--------------------------+--------------------------------------------------+
| | 4 electrodes-soil sample    |mb v2023                        |None                |Raspberry Pi 3 Model B    | 12V Battery              | config_mb_2023.py                                |
| | laboratory (only Rhoa)      |                                |                    |                          |                          |                                                  |
+-------------------------------+--------------------------------+--------------------+--------------------------+--------------------------+--------------------------------------------------+

Another possible combination is to use MUX v2023 with MUX v2024 together, which allows to add series of 8 electrodes to a 64-electrode system.
This could be handful if ones is looking to build e.g. a 96 electrode system, which would therefore feature 4 MUX 2023 (64 electrodes) + 4 MUX 2024 (32 electrodes).

In "BUILD OHMPI SYSTEMS" section we detail examples of OHMPI systems assemblies in different versions.

Today, version 1.0x is no longer maintained, but all boards from v2023 upwards are compatible with each other. This is the major innovation of 2024.
Depending on your needs and applications, you can choose the board you are going to use.


How to build an OhmPi successfully?
***********************************

and become and OhmPier!

Here are few tips:

- make **good soldering**: a lot of issues arise from bad soldering or soldering on the wrong side of PCB. Take your time, check your soldering with the multimeter, this will save you a lot of time afterwards.
- go **step by step**: follow the documentation, start by building a measurement board, then build multiplexers, then assemble the system.
- **hardware check**: for each board, check your electronics with the multimeter (there are checklists at the end of the "build your board" section)
- **software test**: use the software tests once the system is assembled. Always check with a resistor board before going on the field.
- if needed, **seek help**: consult the troubleshooting section or ask help on `Discord <https://discord.gg/5gwpHGyu>`_. Look at the open or closed gitlab issues.
- provide **feedback** and **share your experience**: OhmPi is an open-source open-hardware project, if you found a bug or have an idea to improve the hardware or the code, please use the `GitLab repository <https://gitlab.com/ohmpi/ohmpi>`_ and raise issues. You can also share your experience with the community.



Where are the OhmPi's?
**********************


.. raw:: html

    <embed>
           <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.7.1/jquery.min.js"></script>
           <script src="https://cdn.tutorialjinni.com/jquery-csv/1.0.21/jquery.csv.min.js"></script>
           <div id="map" >      
           </div>
           <p>The locations on the map are not precise locations.</p>

      <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
           integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
           crossorigin=""/>
           <!-- Make sure you put this AFTER Leaflet's CSS -->
      <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
           integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
           crossorigin=""></script>




      <script type="text/csv" id="unparsed" src="../../_static/map.csv"></script>


      <script type="text/javascript">

           var ohmpiIcon = L.icon({
               iconUrl: '../../_static/images_map/LOGO_OHMPI.png',
               //shadowUrl: '',

               iconSize:     [102, 57], // size of the icon
               //shadowSize:   [50, 64], // size of the shadow
               iconAnchor:   [21, 48], // point of the icon which will correspond to marker's location
               //shadowAnchor: [4, 62],  // the same for the shadow
               popupAnchor:  [25, -50] // point from which the popup should open relative to the iconAnchor
           });




           function addPinsToMap(locations) {
                for (let i=0; i<locations.length; i++ ) {
                     ohmpi = locations[i];

                     popup_content = "<b>Hi! I'm " + ohmpi.name + "</b>" + 
                          "<br>I've been setup by the " + ohmpi.institution + " in " + ohmpi.location + ".";

                     if (ohmpi.description.length > 0) {
                          popup_content += "<br><br><b>Description:</b> <br>" + ohmpi.description;
                     }
                     if (ohmpi.image.length > 0) {
                          popup_content += "<br><br><img width='90%' height='90%' src='" + ohmpi.image + "' />"
                     }
                     if (ohmpi.link.length > 0) {
                          popup_content += "<br><br><a href='" + ohmpi.link + "'>Link</a></b> <br>";
                     }

                     marker = L.marker([ ohmpi.latitude , ohmpi.longitude ], {icon: ohmpiIcon}).addTo(map);



                     marker.bindPopup(popup_content);
                }
           }


           var map = L.map('map').setView([50.52791,5.53022],7);

           L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
               maxZoom: 19,
               attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
           }).addTo(map);



           fetch("../../_static/map.csv")
             // fetch() returns a promise. When we have received a response from the server,
             // the promise's `then()` handler is called with the response.
             .then((response) => {
               // Our handler throws an error if the request did not succeed.
               if (!response.ok) {
                 throw new Error(`HTTP error: ${response.status}`);
               }
               // Otherwise (if the response succeeded), our handler fetches the response
               // as text by calling response.text(), and immediately returns the promise
               // returned by `response.text()`.
               return response.text();
             })
             // When response.text() has succeeded, the `then()` handler is called with
             // the text
             .then((text) => {
                var locations_json = $.csv.toObjects(text);
                addPinsToMap(locations_json)
             })
             .catch((error) => {
                console.log(error);
             });




           // This allows the map to render properly (Must be at the end of the code)
           setTimeout(
                function () {
                     window.dispatchEvent(new Event("resize"));
                }, 500);


      </script>


      <style>
           #map {
                height: 800px;
                width: 100%;
                margin: auto;
           }
      </style>
    </embed>

If you want your system to appear on the map, `register your OhmPi <https://framaforms.org/ohmpi-registration-form-1731060017>`_.