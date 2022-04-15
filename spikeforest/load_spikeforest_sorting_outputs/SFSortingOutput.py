from copy import deepcopy
import kachery_cloud as kcl
import sortingview as sv
from spikeinterface.core.old_api_utils import OldToNewRecording, OldToNewSorting


class SFSortingOutput:
    def __init__(self, sorting_output_record: dict) -> None:
        self._sorting_output_record = sorting_output_record
    @property
    def sorting_output_record(self):
        return deepcopy(self._sorting_output_record)
    @property
    def recording_name(self):
        return self._sorting_output_record['recordingName']
    @property
    def study_name(self):
        return self._sorting_output_record['studyName']
    @property
    def sorter_name(self):
        return self._sorting_output_record['sorterName']
    @property
    def cpu_time_sec(self):
        return self._sorting_output_record['cpuTimeSec']
    @property
    def return_code(self):
        return self._sorting_output_record['returnCode']
    @property
    def timed_out(self):
        return self._sorting_output_record['timedOut']
    @property
    def start_time(self):
        return self._sorting_output_record['startTime']
    @property
    def end_time(self):
        return self._sorting_output_record['endTime']
    @property
    def sorting_object(self):
        return self._sorting_output_record.get('sortingObject', None)
    def get_console_out(self):
        console_out_uri = self._sorting_output_record['consoleOut']
        return kcl.load_text(console_out_uri)
    def get_sorting_extractor(self):
        sorting_object = self.sorting_object
        if sorting_object is None: return None
        return OldToNewSorting(sv.LabboxEphysSortingExtractor(sorting_object))