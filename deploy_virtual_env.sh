#!/bin/bash
sudo apt-get install -y libatlas-base-dev
python -m venv ohmpy
source ohmpy/bin/activate || exit 1  # NOTE: Added || exit to avoid installing requirements in system python
export CFLAGS=-fcommon
pip install -r requirements.txt

