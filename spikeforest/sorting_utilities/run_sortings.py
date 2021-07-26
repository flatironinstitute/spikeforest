#!/usr/bin/python

from argparse import ArgumentParser, Namespace
from datetime import datetime
import json
import os
from typing import Any, Dict, Generator, List, NamedTuple, Tuple, TypedDict, Union
import yaml

from spikeforest._common.calling_framework import StandardArgs, add_standard_args, call_cleanup, extract_hither_config, _fmt_time, parse_shared_configuration, print_per_verbose
import spikeextractors as se
import spikeforest as sf
import hither2 as hi
import kachery_client as kc
import sortingview as sv

# Maps the sorter names (as they appear in the spec file) to the
# wrapper functions exposed by this package.
# If a new sorter is added, a corresponding entry should be added here.
KNOWN_SORTERS = {
    'SpykingCircus': sf.spykingcircus_wrapper1,
    'MountainSort4': sf.mountainsort4_wrapper1,
    'Tridesclous':   sf.tridesclous_wrapper1,
    'Kilosort2':     sf.kilosort2_wrapper1,
    'Kilosort3':     sf.kilosort3_wrapper1,
}

DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'

# TypedDict as we might be changing the values; NamedTuple is immutable
class ArgsDict(TypedDict):
    study_source_file: str
    sorter_spec_file: str

class RecordingRecord(NamedTuple):
    study_name: str
    recording_name: str
    recording_uri: str
    ground_truth_uri: str

class StudyRecord(NamedTuple):
    study_name: str
    recordings: List[RecordingRecord]

StudySetsDict = Dict[str, List[StudyRecord]]

class SorterRecord(NamedTuple):
    sorter_name: str
    sorting_parameters: Any # at present, this is in practice always an empty object

class SortingJob(NamedTuple):
    recording_name: str
    recording_uri: str
    ground_truth_uri: str
    study_name: str
    sorter_name: str
    params: Any
    sorting_job: hi.Job

class SorterStudyMatrixEntry(NamedTuple):
    sorter_record: SorterRecord
    requested_studies: List[str]
SorterStudyMatrixDict = Dict[str, SorterStudyMatrixEntry]

class SortingMatrixEntry(NamedTuple):
    sorter_record: SorterRecord
    requested_recordings: List[RecordingRecord]

# Key is a sorter-name; value is a Tuple of SorterRecord, List[RecordingRecord]
SortingMatrixDict = Dict[str, SortingMatrixEntry]

# TypedDict is JSON-serializable, while NamedTuple isn't
class OutputRecord(TypedDict):
    recordingName: str
    studyName: str
    sorterName: str
    sortingParameters: Any
    consoleOutUri: str
    cpuTimeSec: float
    errored: bool
    startTime: str
    endTime: str
    sortingOutput: Union[str, None]
    recordingUri: str
    groundTruthUri: str


def init_configuration() -> Tuple[ArgsDict, StandardArgs]:
    parser = ArgumentParser(description="Given a list of study sets, run the specified suite of " +
        "spike sorters. Store results in kachery and return a json object describing the resulting sortings.")
    parser = init_sorting_args(parser)
    parser = add_standard_args(parser)
    parsed = parser.parse_args()
    std_args = parse_shared_configuration(parsed)
    args = parse_argsdict(parsed)
    if (parsed.check_config):
        print(f"""Received the following environment vars:
            HITHER_USE_CONTAINER: {os.getenv('HITHER_USE_CONTAINER')}
            HITHER_USE_SINGULARITY: {os.getenv('HITHER_USE_SINGULARITY')}
            HITHER_MATLAB_MLM_LICENSE_FILE: {os.getenv('HITHER_MATLAB_MLM_LICENSE_FILE')}
        """)
        print(f"\n\tFinal Shared configuration:\n{json.dumps(std_args, indent=4)}")
        print(f"\n\tFinal configuration:\n{json.dumps(args, indent=4)}")
        exit()
    return (args, std_args)

def init_sorting_args(parser: ArgumentParser) -> ArgumentParser:
    parser.add_argument('--study-source-file', '-s', action='store', default=None,
        help="Path or kachery URI for the JSON file which contains the list of study sets. Note that " +
        "this parameter is usually part of the sorter spec file; if it is provided, the command-line " +
        "option will override any value specified in the sorter spec file.")
    parser.add_argument('--sorter-spec-file', '-l', action='store',
        help="Path or kachery URI for the YAML file which contains the sorters to run, with parameters.")
    return parser

def parse_argsdict(parsed: Namespace) -> ArgsDict:
    args: ArgsDict = {
        'study_source_file': '',
        'sorter_spec_file': ''
    }
    args['sorter_spec_file'] = parsed.sorter_spec_file
    if args['sorter_spec_file'] is None or not os.path.exists(args['sorter_spec_file']):
        raise FileNotFoundError(f"Requested spec file {args['sorter_spec_file']} does not exist.")
    if (parsed.study_source_file is not None):
        args['study_source_file'] = parsed.study_source_file
    else:
        with open(args['sorter_spec_file']) as file:
            spec_yaml = yaml.safe_load(file)
            args['study_source_file'] = spec_yaml['studysets']
    if not os.path.exists(args['study_source_file']):
        raise FileNotFoundError(f"Requested study source file {args['study_source_file']} does not exist.")
    return args

def parse_sorters(spec_filename: str, known_study_sets: List[str]) -> SorterStudyMatrixDict:
    with open(spec_filename) as file:
        spec_yaml = yaml.safe_load(file)
    declared_study_sets = { i : i for i in spec_yaml['studyset_names'] }
    missing_sets = list(filter(lambda s: s not in known_study_sets, declared_study_sets))
    if len(missing_sets) != 0:
        bad = "\n\t".join(missing_sets)
        raise Exception(f"Spec file references study sets not recorded in study set file:\n\t{bad}")
    sorting_matrix: SorterStudyMatrixDict = {}
    for sorter in spec_yaml['spike_sorters']:
        s: SorterRecord = SorterRecord(sorter_name=sorter['name'], sorting_parameters=sorter['params'])
        if s.sorter_name not in list(KNOWN_SORTERS.keys()):
            raise Exception(f"Spec file {spec_filename} requested unrecognized sorter {s.sorter_name}.")
        requested_study_sets: List[str] = sorter['studysets']
        if not all(elem in declared_study_sets for elem in requested_study_sets):
            err = f"Sorter record {s.sorter_name} requests an unknown study. " + \
                  f"(Requested:\n{requested_study_sets}, known:\n{list(declared_study_sets.keys())})"
            raise Exception(err)
        sorting_matrix[s.sorter_name] = (s, requested_study_sets)
    return sorting_matrix


# class SortingMatrixEntry(NamedTuple):
#     sorter_record: SorterRecord
#     requested_recordings: List[RecordingRecord]

def populate_sorting_matrix(study_matrix: SorterStudyMatrixDict, study_sets: StudySetsDict) -> SortingMatrixDict:
    detailed_matrix: SortingMatrixDict = {}
    for sorter_name in study_matrix.keys():
        (sorter, study_set_names) = study_matrix[sorter_name]
        detailed_matrix[sorter_name] = SorterStudyMatrixEntry(
            sorter_record = sorter,
            requested_studies=[x for name in study_set_names
                                    for study in study_sets[name]
                                        for x in study.recordings]
        )
    return detailed_matrix

def load_study_records(study_set_file: str) -> StudySetsDict:
    hydrated_sets = kc.load_json(study_set_file)
    assert hydrated_sets is not None
    study_sets: StudySetsDict = {}
    # Make a list of study_set lists, one per StudySet in the source json file.
    for study_set in hydrated_sets['StudySets']:
        name = study_set['name']
        records = make_study_records_from_studyset(study_set)
        study_sets[name] = records
    return study_sets


def make_study_records_from_studyset(study_set: Any) -> List[StudyRecord]:
    # study_set should be one element of the 'StudySets' key of studysets.json, as in:
    # { [ ...fields not used by this script... ]
    #   "name": "ALL_CAPS_NAME",  --> These should match the names in the spec yaml
    #   "studies": [
    #       {     # format for each study --> Mapped to a StudyRecord.
    #           "name": "synth_magland_noise20_K20_C8",
    #           "studySetName": "SYNTH_MAGLAND",
    #           "recordings": [
    #               {
    #                   "name": "001_synth",
    #                   ... [unused data fields omitted] ...
    #                   "recordingUri":   <a uri>,
    #                   "sortingTrueUri": <another uri>
    #               }, ... }
    records: List[StudyRecord] = []
    for study in study_set['studies']:
        records.append(
            StudyRecord(
                study_name=study['name'],
                recordings=[
                            RecordingRecord(
                                study_name       = study['name'],
                                recording_name   = r['name'],
                                recording_uri    = r['recordingUri'],
                                ground_truth_uri = r['sortingTrueUri']
                            )
                            for r in study['recordings']]
            )
        )
    return records


# Output:
# File of the sort as sortings.json.
# This format is:
# [For each sorter-recording pair]:
# {
#     "recordingName": "20160415_patch2", --> comes from study list
#     "studyName": "paired_mea64c", --> comes from study list
#     "sorterName": "HerdingSpikes2", --> ith sorter name
#     "sortingParameters": {}, --> also comes from sorter list
# ---
#     "consoleOut": "sha1://aec68278bde6695224890000f1db8bd449964c65/file.txt", --> running the sorter
#        --> We should structure this so the console output includes the container/environment information
#        --> Look @ sorter examples (e.g. testSpykingCircus in devel/sorting) as examples of running sorter
#        --> hither option: does not yet exist.
# x   "container": "docker://magland/sf-herdingspikes2:0.3.2", --> comes from running the sorter
#        --> Or maybe this is an 'image' field that isn't part of the console out? Methodological issues??
#     "cpuTimeSec": 92.18, --> running sorter
#     "timedOut": false, --> running sorter. How do we know?
#                        --> A: We don't right now, it's pending. It'll be supported in the next hither
#     "startTime": "2020-02-25T17:07:47.394880", --> running sorter
#     "endTime": "2020-02-25T17:09:32.901005", --> running sorter
#           --> change 'firings' to 'sortingOutputUri'
#     "firings": "sha1://0d1ae184564d358ace078c645026583fbb3d6fba/0d1ae184564d358ace078c645026583fbb3d6fba", --> sorter
# ---> These 2 are just echoing the input list
#     "recordingUri": "sha1://05536d7a37efb3f5f2ca42c987964f199305f480/20160415_patch2.json",
#     "sortingTrueUri": "sha1://71eea1fbe545bacf12884711baab387dce7160e1/20160415_patch2.firings_true.json"
# }
def queue_sort(sorter: SorterRecord, recording: RecordingRecord) -> hi.Job:
    if sorter.sorter_name not in KNOWN_SORTERS.keys():
        raise Exception(f'Sorter {sorter.sorter_name} was requested but is not recognized.')
    sort_fn = KNOWN_SORTERS[sorter.sorter_name]

    base_recording = sv.LabboxEphysRecordingExtractor(recording.recording_uri, download=True)
    params = {
        'recording_object': base_recording.object()
    }
    return hi.Job(sort_fn, params)

def sorting_loop(sorting_matrix: SortingMatrixDict) -> Generator[SortingJob, None, None]:
    for sorter_name in sorting_matrix.keys():
        print_per_verbose(3, f"Queueing sort for sorter {sorter_name}")
        (sorter, recordings) = sorting_matrix[sorter_name]
        for recording in recordings:
            yield SortingJob(
                recording_name   = recording.recording_name,
                recording_uri    = recording.recording_uri,
                ground_truth_uri = recording.ground_truth_uri,
                study_name       = recording.study_name,
                sorter_name      = sorter.sorter_name,
                params           = sorter.sorting_parameters,
                sorting_job      = queue_sort(sorter, recording)
            )

def make_output_record(job: SortingJob) -> OutputRecord:
    errored = job.sorting_job.status == "error"
    if (errored):
        stored_sorting = None
    else:
        sorting = sv.LabboxEphysSortingExtractor(job.sorting_job.result.return_value)
        stored_sorting = sv.LabboxEphysSortingExtractor.store_sorting(sorting)
    console = kc.store_json(job.sorting_job._console_lines)
    try:
        elapsed = job.sorting_job.timestamp_completed - job.sorting_job.timestamp_started
    except:
        elapsed = 0.0

    # Can't do this--sorting_job is not json-serializable.
    # TODO: Implement a __str__ method for hi2.Job
    # print_per_verbose(3, f"sorting_job: {json.dumps(job.sorting_job, indent=4)}")

    record: OutputRecord = {
        'recordingName': job.recording_name,
        'studyName': job.study_name,
        'sorterName': job.sorter_name,
        'sortingParameters': job.params,
        'consoleOutUri': console,
        'cpuTimeSec': elapsed,
        'errored': errored,
        'startTime': _fmt_time(job.sorting_job.timestamp_started),
        'endTime': _fmt_time(job.sorting_job.timestamp_completed),
        'sortingOutput': stored_sorting,
        'recordingUri': job.recording_uri,
        'groundTruthUri': job.ground_truth_uri
    }
    return record

def make_json_output_record(record: OutputRecord) -> str:
    return json.dumps(record, indent=4)

def output_records(results: List[str], std_args: StandardArgs) -> None:
    if std_args['outfile'] is not None and std_args['outfile'] != '':
        with open(std_args['outfile'], "a") as file:
            json.dump(results, file, indent=2)
    else:
        print(json.dumps(results, indent=4))

def main():
    (args, std_args) = init_configuration()
    study_sets = load_study_records(args['study_source_file'])
    study_matrix = parse_sorters(args['sorter_spec_file'], list(study_sets.keys()))
    sorting_matrix = populate_sorting_matrix(study_matrix, study_sets)

    hither_config = extract_hither_config(std_args)
    try:
        with hi.Config(**hither_config):
            sortings = list(sorting_loop(sorting_matrix))
        hi.wait(None)
    finally:
        call_cleanup(hither_config)
    results: List[OutputRecord] = [make_output_record(job) for job in sortings]
    output_records(results, std_args)


if __name__ == "__main__":
    main()
