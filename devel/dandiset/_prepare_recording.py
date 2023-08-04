import os
from dataclasses import dataclass
from spikeforest.load_spikeforest_recordings.SFRecording import SFRecording

from datetime import datetime
from uuid import uuid4

import numpy as np
from dateutil.tz import tzlocal

from pynwb import NWBHDF5IO, NWBFile
from pynwb.ecephys import LFP, ElectricalSeries
from pynwb.file import Subject

from StudyInfo import StudyInfo
from RecordingInfo import RecordingInfo


def _prepare_recording(R: SFRecording, *, nwb_fname: str, study_info: StudyInfo, recording_info: RecordingInfo, overwrite: bool = True):
    print(f'Preparing recording: {R.study_set_name}/{R.study_name}/{R.recording_name}')
    if os.path.exists(nwb_fname) and (not overwrite):
        print(f'File exists: {nwb_fname}')
        return
    recording = R.get_recording_extractor()
    sorting_true = R.get_sorting_true_extractor()
    print(f'{recording.get_num_channels()} channels, {recording.get_sampling_frequency()} Hz, {recording.get_total_duration()} sec')
    print(f'Unit ids: {sorting_true.get_unit_ids()}')

    nwbfile = NWBFile(
        session_description=f'SpikeForest recording: {R.study_set_name}/{R.study_name}/{R.recording_name}',
        identifier=str(uuid4()),
        session_start_time=datetime.now(tzlocal()),
        experimenter=study_info.experimenter,
        experiment_description=study_info.experiment_description,
        lab=study_info.lab,
        institution=study_info.institution,
        subject=Subject( # tutorial didn't include this
            subject_id='unknown',
            age='P0Y',
            date_of_birth=datetime(1970, 1, 1, 12, tzinfo=tzlocal()),
            sex='U',
            species='Unknown species',
            description='Unknown subject'
         ),
        session_id=f'{R.study_name}/{R.recording_name}',
        keywords=['spikeforest'] # tutorial didn't include this
    )

    # add electrode information
    device = nwbfile.create_device(
        name=recording_info.device_name,
        description=recording_info.device_description
    )
    nwbfile.add_electrode_column(
        name='label',
        description='electrode label'
    )
    nwbfile.add_electrode_column(
        name='x',
        description='x coordinate'
    )
    nwbfile.add_electrode_column(
        name='y',
        description='y coordinate'
    )
    nwbfile.add_electrode_column(
        name='z',
        description='z coordinate'
    )
    electrode_group = nwbfile.create_electrode_group(
        name='main',
        description='main electrode group',
        device=device,
        location='unknown'
    )
    locations = recording.get_channel_locations()
    for i, channel_id in enumerate(recording.get_channel_ids()):
        nwbfile.add_electrode(
            group=electrode_group,
            label=str(channel_id),
            location='unknown',
            x=locations[i][0],
            y=locations[i][1] if len(locations[i]) > 1 else float(0),
            z=locations[i][2] if len(locations[i]) > 2 else float(0)
        )
    
    # add ElectricalSeries
    all_table_region = nwbfile.create_electrode_table_region(
        region=list(range(len(recording.get_channel_ids()))),
        description='all electrodes'
    )
    raw_data = recording.get_traces()
    raw_electrical_series = ElectricalSeries(
        name='ElectricalSeries',
        description='Raw acquisition traces',
        data=raw_data,
        electrodes=all_table_region,
        starting_time=0.0,
        rate=recording.get_sampling_frequency()
    )
    nwbfile.add_acquisition(raw_electrical_series)

    # add spike trains
    for unit_id in sorting_true.get_unit_ids():
        st = sorting_true.get_unit_spike_train(unit_id=unit_id)
        nwbfile.add_unit(
            id=unit_id,
            spike_times=st / recording.get_sampling_frequency()
        )

    # Write the nwb file
    with NWBHDF5IO(nwb_fname, 'w') as io:
        io.write(nwbfile, cache_spec=True)