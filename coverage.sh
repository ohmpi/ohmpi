#!/bin/bash
source env.sh
pip install coverage
coverage run --source=ohmpi .dev/test_all.py
coverage report --include=ohmpi/ohmpi.py,ohmpi/hardware_system.py
coverage html
