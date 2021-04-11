FROM python:3.8

RUN pip install numpy
RUN pip install simplejson requests click

# Install prerequisites
RUN apt-get update && apt-get install -y libgl1-mesa-glx
RUN pip install Cython
RUN pip install scipy numpy pandas scikit-learn matplotlib seaborn tqdm openpyxl PyQt5==5.14.0 pyqtgraph==0.10 quantities neo numba hdbscan
RUN pip install h5py

# # Install tridesclous
# For now we install from a fork - see the PR
# RUN pip install tridesclous==1.6.0
RUN git clone https://github.com/magland/tridesclous /src/tridesclous && cd /src/tridesclous && git checkout 098bcb3e382307a4eaf7864590a54dd397cf6f0d
RUN cd /src/tridesclous && pip install .

# spikeinterface/spikesorters
RUN pip install spikesorters==0.4.4

ENV TDC_IN_CONTAINER=1
    
LABEL version="1.6.0"