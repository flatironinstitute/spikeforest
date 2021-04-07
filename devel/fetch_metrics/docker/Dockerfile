FROM python:3.8

# install layers of prerequisites that don't change as often
# required for kachery_p2p support
RUN pip install simplejson requests click

# for spiketoolkit
RUN pip install numpy scipy pandas
RUN pip install scikit-learn
RUN pip install joblib networkx
RUN pip install h5py

# install spikeextractors, spiketoolkit, spikecomparison
RUN pip install spikeextractors==0.9.5 spiketoolkit==0.7.4 spikecomparison==0.3.2

# For hither singularity mode, this label needs to be consistent with the version on dockerhub
LABEL version="0.7.4"