from argparse import ArgumentParser, Namespace
import json
from typing import Any, Dict, Generator, List, NamedTuple, Set, Tuple, Union

import sortingview as sv
import kachery_cloud as kc
from spikeforest._common.calling_framework import print_per_verbose

## TODO: Need to do error checking on output ids?

TRUE_SORT_LABEL = "Ground-Truth"

class RecordingEntry(NamedTuple):
    study_set_label:  str
    recording_name:   str
    recording_uri:    str
    sorting_true_uri: str
    sorting_object:   Dict[any, any]
    recording_label:  str
    truth_label:      str
    sorting_label:    str

class FullRecordingEntry(NamedTuple):
    recording_label: str
    ground_truth_label: str
    sorting_label: str
    R_id: str
    recording: sv.LabboxEphysRecordingExtractor
    sorting_true: sv.LabboxEphysSortingExtractor
    sorting: sv.LabboxEphysSortingExtractor
    gt_exists: bool
    sorting_exists: bool

class Params(NamedTuple):
    workspace: str
    sortings:  Any
    dry_run:   bool

def init() -> Params:
    description = "Convert a sortings.json file into a populated Labbox workspace."
    parser = ArgumentParser(description=description)
    parser = init_workspace_args(parser)
    parsed = parser.parse_args()
    return parse_workspace_params(parsed)

def init_workspace_args(parser: ArgumentParser) -> ArgumentParser:
    parser = add_workspace_selection_args(parser)
    parser.add_argument('--sortings-file', '-s', action='store', default=None,
        help="Path to sortings file.")
    parser.add_argument('--sortings-file-kachery-uri', '-k', action='store', default=None,
        help="kachery URI for sortings file. Exactly one of --sortings-file and --sortings-file-kachery-uri "
           + "should be set.")
    parser.add_argument('--dry-run', action='store_true', default=False,
        help="If set, script will only parse the input files and display the workspace commands it would have run.")
    return parser

def add_workspace_selection_args(parser: ArgumentParser) -> ArgumentParser:
    parser.add_argument('--workspace-uri', '-W', action='store', default=None,
        help="URI of workspace to add data to.")
    parser.add_argument('--create-new-workspace', action='store_true', default=False,
        help="If create-new-workspace is set and workspace-uri is not set, then a new " +
             "workspace will be created. Setting both results in an error.")
    return parser

def establish_workspace(parsed: Namespace) -> str:
    if parsed.create_new_workspace:
        if parsed.workspace_uri is not None:
            raise Exception("Error: create-new-workspace flag and workspace-uri flag both set. Aborting.")
        return create_workspace()
    if parsed.workspace_uri is None:
        raise Exception("Error: You must provide either a valid workspace URI or the create-new-workspace flag.")
    workspace = sv.load_workspace(parsed.workspace_uri)
    if workspace == None:
        raise Exception("Error: Requested workspace URI is invalid.")
    return workspace.get_uri()

def create_workspace() -> str:
    workspace = sv.create_workspace(label='sortingview-default')
    kc.set('sortingview-default-workspace', workspace.uri)
    return workspace.uri

def parse_workspace_params(parsed: Namespace) -> Params:
    if parsed.dry_run:
        workspace_uri = parsed.workspace_uri
    else:
        workspace_uri = establish_workspace(parsed)
    if ((parsed.sortings_file is None and parsed.sortings_file_kachery_uri is None)
         or (parsed.sortings_file is not None and parsed.sortings_file_kachery_uri is not None)):
        raise Exception("Exactly one of sortings_file and sortings_file_kachery_uri must be set.")
    if parsed.sortings_file is not None:
        with open(parsed.sortings_file) as fp:
            sortings = json.load(fp)
    else:
        sortings = kc.load_json(parsed.sortings_file_kachery_uri)
    return Params(workspace_uri, sortings, parsed.dry_run)

def get_known_recording_id(workspace: Union[sv.Workspace, None], recording_label: str) -> str:
    if workspace is None: return None
    for (_, v) in workspace._recordings.items():
        if v['recordingLabel'] == recording_label:
            return v['recordingId']
    return None

def sortings_are_in_workspace(workspace: Union[sv.Workspace, None], gt: str, comp: str) -> Tuple[bool, bool]:
    if workspace is None: return (False, False)
    sortings = [workspace._sortings[key]['sortingLabel'] for key in workspace._sortings.keys()]
    return (gt in sortings, comp in sortings)

def get_labels(study_name: str, recording_name: str, gt_token: str, sorter_name: str) -> Tuple[str, str, str]:
    recording_label    = f'{study_name}/{recording_name}'
    ground_truth_label = f'{gt_token}/{recording_label}'
    sorting_label      = f'{sorter_name}/{recording_label}'
    return (recording_label, ground_truth_label, sorting_label)

def populate_extractors(entry: RecordingEntry) -> Tuple[sv.LabboxEphysRecordingExtractor, sv.LabboxEphysSortingExtractor, sv.LabboxEphysSortingExtractor]:
    recording = sv.LabboxEphysRecordingExtractor(entry.recording_uri, download=True)
    sample_rate = recording.get_sampling_frequency()
    sorting_true = sv.LabboxEphysSortingExtractor(entry.sorting_true_uri, samplerate=sample_rate)
    sorting = sv.LabboxEphysSortingExtractor(entry.sorting_object, samplerate=sample_rate)
    return (recording, sorting_true, sorting)

def add_entry_to_workspace(re: FullRecordingEntry, workspace: sv.Workspace) -> None:
    print_per_verbose(3, f"Hit live-load step. Current re values: r-id {re.R_id}, gt-exists: {re.gt_exists} sorting-exists: {re.sorting_exists}")
    R_id = re.R_id
    if R_id is None:
        R_id = workspace.add_recording(recording=re.recording, label=re.recording_label)
    if not re.gt_exists:
        GT_id = workspace.add_sorting(sorting=re.sorting_true, recording_id=R_id, label=re.ground_truth_label)
    if not re.sorting_exists:
        s_id = workspace.add_sorting(sorting=re.sorting, recording_id=R_id, label=re.sorting_label)
    # TODO: Do something useful with the result codes here?

def add_entry_dry_run(re: FullRecordingEntry) -> None:
    print_per_verbose(3, f"Hit dry-run step. Current re values: r-id {re.R_id}, gt-exists: {re.gt_exists} sorting-exists: {re.sorting_exists}")
    if re.R_id is not None:
        print(f"Not adding {re.recording_label} as it is already in the workspace.")
    else:
        print(f"Would add {re.recording.get_num_channels()}-channel recording with label {re.recording_label}")
    if re.gt_exists:
        print(f"Not adding {re.ground_truth_label} as it is already in the workspace.")
    else:
        print(f"Would add GT at {len(re.sorting_true.get_unit_ids())} units with label {re.ground_truth_label}")
    if re.sorting_exists:
        print(f"Not adding {re.sorting_label} as it is already in the workspace.")
    else:
        print(f"Would add sorting of {len(re.sorting.get_unit_ids())} unit(s) with label {re.sorting_label}")

def parse_sortings(sortings: List[Any]) -> Generator[RecordingEntry, None, None]:
    for s in sortings:
        if 'sortingOutput' not in s: continue # when the underlying job errored
        name = s['recordingName']
        (recording_label, gt_label, sorting_label) = get_labels(s['studyName'], name, TRUE_SORT_LABEL, s['sorterName'])
        yield RecordingEntry(
            study_set_label  = s['studyName'],
            recording_name   = name,
            recording_uri    = s['recordingUri'],
            sorting_true_uri = s['groundTruthUri'],
            sorting_object   = s['sortingOutput'],
            recording_label  = recording_label,
            truth_label      = gt_label,
            sorting_label    = sorting_label
        )

def main():
    (workspace_uri, sortings_json, dry_run) = init()
    workspace = None if workspace_uri is None else sv.load_workspace(workspace_uri)
    if workspace_uri is None and dry_run:
        workspace_uri = "(Dry run, no actual workspace written to)"
    loaded = 0
    for r in parse_sortings(sortings_json):
        (recording, sorting_true, sorting) = populate_extractors(r)
        R_id = get_known_recording_id(workspace, r.recording_label)
        (gt_exists, sorting_exists) = sortings_are_in_workspace(workspace, r.truth_label, r.sorting_label)
        entry = FullRecordingEntry(
            r.recording_label, r.truth_label, r.sorting_label,
            R_id, recording, sorting_true, sorting,
            gt_exists, sorting_exists
        )
        if dry_run:
            add_entry_dry_run(re=entry)
        else:
            add_entry_to_workspace(re=entry, workspace=workspace)
        loaded += 1
    print(f"Parsed {loaded} recording sets for workspace {workspace_uri}")

if __name__ == "__main__":
    main()