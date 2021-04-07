FROM python:3.8

RUN pip install numpy
RUN pip install simplejson requests click

# Install MountainSort4
RUN mkdir -p /src \
    && git clone https://github.com/magland/ml_ms4alg \
    && cd ml_ms4alg && git checkout 84cbc2ea305bcc37d0eae1a0a313e859f611265c \
    && pip install .

# spikeinterface/spikesorters
RUN pip install spikesorters==0.4.4

LABEL version="0.3.6"