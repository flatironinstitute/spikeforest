import kachery_cloud as kcl
from .load_spikeforest_recordings import load_spikeforest_recordings


def load_spikeforest_recording(*, study_name: str, recording_name: str):
    all_recordings = load_spikeforest_recordings()
    x = [
        R for R in all_recordings
        if R.study_name == study_name and R.recording_name == recording_name
    ]
    if len(x) == 0: raise Exception(f'Recording not found: {study_name}/{recording_name}')
    R = x[0]
    return R