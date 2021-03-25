import kachery_p2p as kp
import pandas as pd
import labbox_ephys as le
import numpy as np

_sorting_results_uri = 'sha1://52f24579bb2af1557ce360ed5ccc68e480928285/file.txt?manifest=5bfb2b44045ac3e9bd2a8fe54ef67aa932844f58'

class SFSortingResults:
    """
    Class to load SpikeForest results and retrieve study names, recording names in a study, sorting names for
    a recording, and `SortingExtractor` objects.

    Parameters
    ----------
    sorting_results_uri: str or Path
        The uri of the sorting results.
        If None, the standard URI is used ('sha1://21c4ad407244f18318bdbdeef2c953ad1eb61aef/sortingresults.json)
    """
    def __init__(self, sorting_results_uri=None):
        if sorting_results_uri is None:
            self._sorting_results_uri = _sorting_results_uri
        else:
            self._sorting_results_uri = sorting_results_uri
        x = kp.load_json(self._sorting_results_uri)
        self._df = pd.DataFrame(x)
        print(f"Found {len(self._df)} sorting outputs")

    def get_sorting_output(self, study_name, recording_name, sorter_name):
        # get study
        dataset = self._df.query(f"studyName == '{study_name}'")
        assert len(dataset) > 0, f"Study '{study_name}' not found"

        # get recording
        dataset = dataset.query(f"recordingName == '{recording_name}'")
        assert len(dataset) > 0, f"Recording '{recording_name}' not found"

        # get sorting uri
        dataset = dataset.query(f"sorterName == '{sorter_name}'")
        assert len(dataset) == 1, f"Sorting output '{sorter_name}' not found"

        firings_uri = dataset["firings"].values[0]

        # TODO infer sample rate in a better way.
        sorting_object = {
            'sorting_format': 'mda',
            'data': {
                'firings': firings_uri,
                'samplerate': 30000
            }
        }
        sorting = le.LabboxEphysSortingExtractor(sorting_object)

        return sorting

    def get_study_names(self):
        study_names = list(np.unique(self._df["studyName"]))
        return study_names

    def get_recording_names(self, study_name):
        # get study
        dataset = self._df.query(f"studyName == '{study_name}'")
        assert len(dataset) > 0, f"Study '{study_name}' not found"

        recording_names = list(np.unique(dataset["recordingName"]))
        return recording_names

    def get_sorting_output_names(self, study_name, recording_name):
        # get study
        dataset = self._df.query(f"studyName == '{study_name}'")
        assert len(dataset) > 0, f"Study '{study_name}' not found"

        # get recording
        dataset = dataset.query(f"recordingName == '{recording_name}'")
        assert len(dataset) > 0, f"Recording '{recording_name}' not found"

        sorting_output_names = list(np.unique(dataset["sorterName"]))
        return sorting_output_names
