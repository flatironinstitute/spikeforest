FROM python:3.8

RUN pip install numpy
RUN pip install simplejson requests click

# Install SpyKING CIRCUS
RUN apt-get update && apt-get install -y libmpich-dev
RUN pip install pyqt5==5.13
RUN apt-get update && apt-get install -y qt5-default
RUN apt-get update && apt-get install -y libglib2.0-0 libgl1-mesa-glx
RUN apt-get update && apt-get install -y packagekit-gtk3-module libcanberra-gtk-module libcanberra-gtk3-module
RUN pip install scikit-build
RUN pip install cmake>=3.18
RUN pip install spyking-circus==1.0.7

# spikeinterface/spikesorters
RUN pip install spikesorters==0.4.4

LABEL version="1.0.7"