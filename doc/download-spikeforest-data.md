# Downloading SpikeForest datasets

You can load the SpikeForest recordings and ground-truth sortings directly into SpikeInterface Python object.

**Step 1a**: [Install kachery-p2p and run a kachery-p2p daemon](https://github.com/flatironinstitute/kachery-p2p/blob/main/doc/setup_and_installation.md)

**Step 1b**: [Join the spikeforest-download channel](./join-spikeforest-download-channel.md)

**Step 2**: Install the most recent version of labbox-ephys

**Step 3**: Select a recording for download from the [spikeforest_recordings](https://github.com/flatironinstitute/spikeforest_recordings) repo.

For example, if you browsed to the [paired_kampff](https://github.com/flatironinstitute/spikeforest_recordings/tree/master/recordings/PAIRED_KAMPFF/paired_kampff) study, you should see a collection of recordings and sortings in .json files.

For example, the recording [2014_11_25_Pair_3_0.json](https://github.com/flatironinstitute/spikeforest_recordings/blob/master/recordings/PAIRED_KAMPFF/paired_kampff/2014_11_25_Pair_3_0.json) with its ground truth sorting [2014_11_25_Pair_3_0.firings_true.json](https://github.com/flatironinstitute/spikeforest_recordings/blob/master/recordings/PAIRED_KAMPFF/paired_kampff/2014_11_25_Pair_3_0.firings_true.json). Inspecting the `self_reference` fields in these gives you URI's (universal pointers) to these:

* Recording: `sha1://a205f87cef8b7f86df7a09cddbc79a1fbe5df60f/2014_11_25_Pair_3_0.json`
* Ground truth sorting: `sha1://c656add63d85a17840980084a1ff1cdc662a2cd5/2014_11_25_Pair_3_0.firings_true.json`

**Step 4**: Load the sorting and recording into SpikeInterface objects via labbox-ephys

```python
import labbox_ephys as le

recording_uri = 'sha1://a205f87cef8b7f86df7a09cddbc79a1fbe5df60f/2014_11_25_Pair_3_0.json'
sorting_uri = 'sha1://c656add63d85a17840980084a1ff1cdc662a2cd5/2014_11_25_Pair_3_0.firings_true.json'

recording = le.LabboxEphysRecordingExtractor(recording_uri, download=False)
sorting_true = le.LabboxEphysSortingExtractor(sorting_uri)

channel_ids = recording.get_channel_ids()
samplerate = recording.get_sampling_frequency()
num_timepoints = recording.get_num_frames()
print(f'Recording has {len(channel_ids)} channels and {num_timepoints} timepoints (samplerate: {samplerate})')

unit_ids = sorting_true.get_unit_ids()
spike_train = sorting_true.get_unit_spike_train(unit_id=unit_ids[0])
print(f'Unit {unit_ids[0]} has {len(spike_train)} events')
```

The `download=False` means that that we don't want to download the entire recording upfront (just lazy load it on demand). If you set this to True, the entire recording will be downloaded to your kachery storage directory.

You can now interact with these Python objects using tools from [SpikeInterface](https://github.com/spikeinterface) and [labbox-ephys](https://github.com/flatironinstitute/labbox-ephys).





