# SpikeForest

> :warning: This project is under construction.

Spike sorting benchmarking system.

This Python project allows you to download SpikeForest recordings, the associated ground truth sortings, and the outputs of the spike sorting runs, and load these into SpikeInterface recording and sorting extractors.

All data are pinned to IPFS and available on the kachery-cloud network.

# Setup

It is recommended that you use a conda environment with Python >= 3.8 and numpy

Clone this repository and install via pip

```bash
git clone <repo>
cd spikeforest
pip install -e .
```

Configure your kachery-cloud client

```bash
kachery-cloud-init
# follow the instructions to associate your client with your Google user name on kachery-cloud
```

# Getting started

* List all recordings with ground truth: [examples/list_all_recordings.py](examples/list_all_recordings.py)
* Load a recording and sorting extractors for a recording with ground truth: [examples/load_extractors_for_recording.py](examples/load_extractors_for_recording.py)
* List all sorting outputs: [examples/list_all_sorting_outputs.py](examples/list_all_sorting_outputs.py)
* Load sorting extractor for a sorting output: [examples/load_extractor_for_sorting_output.py](examples/load_extractor_for_sorting_output.py)

## Frequently asked questions

### How can I download the SpikeForest recordings and ground truth sorting data?

See example above

### How can I download the SpikeForest sorting outputs?

See example above

## Questions to be answered later

### How can I visualize a SpikeForest sorting using sortingview?

### How can I run containerized spike sorting on my own computer?