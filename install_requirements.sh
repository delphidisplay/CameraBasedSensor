#!/bin/bash

echo "INSTALLING WITH PACKAGE MANAGER"
sudo apt-get install python3.6

echo "INSTALLING PYTHON DEPENDENCIES"
pip3 install flask
pip3 install opencv-python
pip3 install shapely
pip3 install matplotlib
pip3 install imultils 


echo "INSTALLATION COMPLETE"

