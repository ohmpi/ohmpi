# OhmPi

Development of a low-cost multi-electrodes resistivity meter for electrical resistivity mesaurement for lab applications, based on raspberry board

## Installation

1. Download a .zip of this repository (or use `git clone https://gitlab.com/ohmpi/ohmpi.git`)
2. Enter the repository (`cd path/to/ohmpi`) and install the software needed. We made a simple script to make it simpler:

`./install.sh`

The installation script will create a virtual python environement `ohmpy` (with a 'y' at the end) where all packages specified in *requirements.txt* will be installed. The script also takes care of creating a configuration for your hardware if you wish.

To activate the environment and set the necessary `$PYTHONPATH` variable, you can use:

`source env.sh`

More examples are provided in the **[documentation](https://ohmpi.gitlab.com/ohmpi)**.


## Gallery

A few pictures of the components of the OhmPi. More in the [**DOCUMENTATION**](https://ohmpi.gitlab.com/ohmpi)!

![measurment board](doc/source/img/mb.2024.x.x/32.jpg)
*Measurement board (v2024).*

![multiplexer board](doc/source/img/mux.2024.0.x/7.jpg)
*Multiplexer board (v2024).*

![software architecure](doc/source/img/software/ohmpi_2024_architecture.png)
*Software architecture.*


## Citing Ohmpi

If you use Ohmpi for you work, please cite [this paper](https://www.sciencedirect.com/science/article/pii/S2468067220300316) as:

    Rémi Clement, Yannick Fargier, Vivien Dubois, Julien Gance, Emile Gros, Nicolas Forquet, OhmPi: An open source data logger for 
    dedicated applications of electrical resistivity imaging at the small and laboratory scale, HardwareX, Volume 8, 2020, e00122, ISSN 2468-0672, https://doi.org/10.1016/j.ohx.2020.e00122..


## License information

You may redistribute and modify this documentation and make products using it under the terms of the CERN-OHL-P v2 (https://cern.ch/cern-ohl). This documentation is distributed WITHOUT ANY EXPRESS OR IMPLIED WARRANTY, INCLUDING OF MERCHANTABILITY, SATISFACTORY QUALITY AND FITNESS FOR A PARTICULAR PURPOSE. Please see the CERN-OHL-P v2 for applicable conditions
