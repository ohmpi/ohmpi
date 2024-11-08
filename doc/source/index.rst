.. Ohmpi documentation master file, created by
   sphinx-quickstart on Tue Jun 30 20:22:03 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

OHMPI: Open source and open hardware resistivity-meter
======================================================



.. sidebar:: Summary

    :Release: |release|
    :Date: |today|
    :Date start: July 2016	
    :Authors: **Rémi CLEMENT, Nicolas FORQUET, Yannick FARGIER, Vivien DUBOIS, Hélène GUYARD, Olivier KAUFMANN, Guillaume BLANCHY, Arnaud WATLET**
    :Target: users, researchers and developers 
    :Status: some mature, some in progress

This documentation presents the development of a low-cost, open hardware
resistivity meter to provide the scientific community with a robust
and flexible tool for small-scale experiments. Called OhmPi, this resistivity meter
features current injection and measurement functions associated with a multiplexer
that allows performing automatic measurements.

Contents
********

.. toctree::
   :maxdepth: 1
   :caption: Introduction

   source_rst/introduction/overview
   source_rst/introduction/about

.. toctree::
   :maxdepth: 2
   :caption: Build OhmPi boards

   source_rst/hardware/hw_info
   source_rst/hardware/mb/mb_2023
   source_rst/hardware/mb/mb_2024
   source_rst/hardware/mux/mux_2023
   source_rst/hardware/mux/mux_2024
   source_rst/hardware/hw_pwr
   source_rst/hardware/hw_rpi



.. toctree::
   :maxdepth: 2
   :caption: Build OhmPi systems

   source_rst/hardware/hw_ohmpi
   OhmPi v2024 (64 elec) <source_rst/hardware/assemble_ohmpi/assembling_mb2024_MUX_2023_dph5005.rst>
   OhmPi Lite v2024 (32 elec) <source_rst/hardware/assemble_ohmpi/assembling_mb2024_MUX_2024_dph5005.rst>
   OhmPi v2023 (64 elec) <source_rst/hardware/assemble_ohmpi/assembling_mb2023_MUX_2023_12V.rst>
   Deploy OhmPi <source_rst/deploy>

.. toctree::
   :maxdepth: 1
   :caption: Operate OhmPi

   Software architecture <source_rst/software/architecture>
   Software installation <source_rst/software/installation>
   Operating the system <source_rst/software/operations/index>
   API reference <source_rst/software/api>

.. toctree::
   :maxdepth: 1
   :caption: Additional resources

   source_rst/troubleshooting
   source_rst/gallery
   source_rst/developments
   source_rst/archived_version

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: References

   Link to OhmPi Repository <https://gitlab.com/ohmpi/ohmpi>

`PDF version of this documentation <_static/ohmpi.pdf>`_

  



