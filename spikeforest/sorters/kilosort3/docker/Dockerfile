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

# gcc-8 (cuda mex doesn't seem to work with gcc >8)
RUN apt-get install -y gcc-8 g++-8 && ln -sf /usr/bin/gcc-8 /usr/bin/gcc && ln -sf /usr/bin/g++-8 /usr/bin/g++

# spikeinterface/spikesorters
RUN pip install spikesorters==0.4.4

RUN mkdir -p /src && git clone https://github.com/MouseLand/Kilosort /src/Kilosort3 && cd /src/Kilosort3 && git checkout a1fccd9abf13ce5dc3340fae8050f9b1d0f8ab7a

ENV HITHER_IN_CONTAINER=1
    
LABEL version="0.1.0"