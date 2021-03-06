#!/bin/bash
set -e

#ARGS="main_analysis_irc.json --use_slurm" # --skip_failing"
#ARGS="main_analysis_irc.json" # --skip_failing"
#ARGS="main_analysis_irc.json --skip_failing --upload_to spikeforest.kbucket,spikeforest.public --download_from spikeforest.kbucket,spikeforest.public"
#ARGS="main_analysis_irc.json --skip_failing --download_from spikeforest.kbucket,spikeforest.public"
#ARGS="main_analysis_irc.json --use_slurm --skip_failing --download_from spikeforest.kbucket,spikeforest.public"
ARGS="main_analysis_irc.json --use_slurm --skip_failing --download_from spikeforest.kbucket,spikeforest.public --upload_to spikeforest.kbucket"

./main_analysis $ARGS --analyses hybrid_janelia
#./main_analysis $ARGS --analyses manual_franklab
./main_analysis $ARGS --analyses paired_boyden32c
./main_analysis $ARGS --analyses paired_crcns
./main_analysis $ARGS --analyses paired_kampff
./main_analysis $ARGS --analyses paired_mea64c
#./main_analysis $ARGS --analyses paired_monotrode
./main_analysis $ARGS --analyses synth_bionet
./main_analysis $ARGS --analyses synth_magland
./main_analysis $ARGS --analyses synth_mearec_neuronexus
./main_analysis $ARGS --analyses synth_mearec_tetrode
#./main_analysis $ARGS --analyses synth_monotrode
./main_analysis $ARGS --analyses synth_visapy
