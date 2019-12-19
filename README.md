# ohmpy

Development of a low-cost multi-electrodes resistivimeter  for electrical resistivity mesaurement for lab applications, based on raspberry board

Version 1.00

## Installation

All dependencies are specified in *requirements.txt*

**Note:** all instructions below should be typed in the terminal

It is first necessary to ensure that the libatlas-base-dev library is installed:
`sudo apt-get install libatlas-base-dev`

We strongly recommend users to create a virtual environment to run the code and installed all required dependencies. It can be done either in a directory gathering all virtual environments used on the computer or within the ohmpy directory.
*  create the virtual environment:
   `python3 -m venv ohmpy`
*  activate it using the following command:
   `source ohmpy/bin/activate`
*  install packages within the virtual environment. Installing the following package should be sufficient to meet dependencies:
`pip install RPi.GPIO adafruit-blinka numpy adafruit-circuitpython-ads1x15 pandas`
*  check that requirements are met using `pip list`
*  you should run you code within the virtual environment
*  to leave the virtual environment simply type: `deactivate`