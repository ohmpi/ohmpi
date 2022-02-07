#!/bin/bash 
sudo apt-get install -y libatlas-base-dev
python3 -m venv ohmpy
source ohmpy/bin/activate
export CFLAGS=-fcommon
pip install -r requirements.txt

