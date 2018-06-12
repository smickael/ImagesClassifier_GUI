#!/bin/bash

sudo apt-get install python3-pip python3-venv
python3 -m venv --python=python3.5 IC_GUI
cd IC_GUI
source bin/activate
#dependencies
python3 -m pip install picamera
python3 -m pip install pillow
python3 -m pip install pandas
python3 -m pip install numpy
python3 -m pip install tensorflow
python3 -m pip install keras
python3 -m pip install matplotlib
#quit venv
deactivate
