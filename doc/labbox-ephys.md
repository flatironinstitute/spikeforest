# Viewing a SpikeForest recording/sorting using labbox-ephys

**Step 1**: Install and set up `kachery-p2p` and `spikeforest` as in [these instructions](./download-spikeforest-data.md).

**Step 2** Run the labbox-ephys web server locally

```
# in a new terminal
> labbox-ephys
```

Now point your browser to `http://localhost:15351`

You will see the default (local) workspace which should not have any recordings/sortings in it to start.

See [labbox-ephys](https://github.com/flatironinstitute/labbox-ephys) for more information.

**Step 3** Import a recording/sorting pair into the default workspace using a Python script

```python
import labbox_ephys as le

# Select a recording/sorting pair from SpikeForest
recording_name = 'paired_kampff/2014_11_25_Pair_3_0'
recording_uri = 'sha1://a205f87cef8b7f86df7a09cddbc79a1fbe5df60f/2014_11_25_Pair_3_0.json'
sorting_uri = 'sha1://c656add63d85a17840980084a1ff1cdc662a2cd5/2014_11_25_Pair_3_0.firings_true.json'

# Load the recording and sorting objects
recording = le.LabboxEphysRecordingExtractor(recording_uri, download=False)
sorting_true = le.LabboxEphysSortingExtractor(sorting_uri)

# Load the default workspace and import the recording/sorting
workspace = le.load_workspace()
R_id = workspace.add_recording(recording=recording, label=recording_name)
S_id = workspace.add_sorting(sorting=sorting_true, recording_id=R_id, label='true')
```

You should see the newly-imported recording appear in the workspace on the browser page.