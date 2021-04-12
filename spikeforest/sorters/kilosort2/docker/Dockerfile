FROM magland/matlab_for_kilosort:0.1.0

#########################################
### Python                                                               
RUN apt update && apt -y install git wget build-essential
RUN apt install -y python3 python3-pip
RUN rm -f /usr/bin/python && ln -s python3 /usr/bin/python
RUN rm -f /usr/bin/pip && ln -s pip3 /usr/bin/pip
RUN DEBIAN_FRONTEND=noninteractive apt install -y python3-tk

# USER matlab

RUN pip install numpy
RUN pip install simplejson requests click

RUN pip install h5py

# spikeinterface/spikesorters
RUN pip install spikesorters==0.4.4

RUN mkdir -p /src && git clone https://github.com/MouseLand/Kilosort /src/Kilosort2 && cd src/Kilosort2 && git checkout v2.0
ENV KILOSORT2_PATH=/src/Kilosort2

ENV HITHER_IN_CONTAINER=1
    
LABEL version="0.1.0"