FROM spikeinterface/kilosort3-base:0.1.0

RUN pip install simplejson requests click

RUN pip install h5py

# spikeinterface/spikesorters
RUN pip install spikesorters==0.4.4

ENV HITHER_IN_CONTAINER=1
    
LABEL version="0.1.1"