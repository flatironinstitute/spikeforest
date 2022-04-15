from .load_spikeforest_sorting_outputs import load_spikeforest_sorting_outputs


def load_spikeforest_sorting_output(*, study_name: str, recording_name: str, sorter_name: str):
    all_sorting_outputs = load_spikeforest_sorting_outputs()
    x = [
        X for X in all_sorting_outputs
        if X.study_name == study_name and X.recording_name == recording_name and X.sorter_name == sorter_name
    ]
    if len(x) == 0: raise Exception(f'Sorting output not found: {study_name}/{recording_name}/{sorter_name}')
    X = x[0]
    return X