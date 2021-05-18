import argparse
import json
from typing import Any, Dict, Generator, List, NamedTuple, Set, Tuple, Union

import labbox_ephys as le
import kachery_p2p as kp

## TODO: Need to do error checking on output ids?

TRUE_SORT_LABEL = "Ground-Truth"

class RecordingEntry(NamedTuple):
    study_set_label:  str
    recording_name:   str
    recording_uri:    str
    sorting_true_uri: str
    sorting_object:   Dict[any, any]
    sorting_label:    str

class FullRecordingEntry(NamedTuple):
    recording_label: str
    ground_truth_label: str
    sorting_label: str
    R_id: str
    recording: le.LabboxEphysRecordingExtractor
    sorting_true: le.LabboxEphysSortingExtractor
    sorting: le.LabboxEphysSortingExtractor
    gt_exists: bool
    sorting_exists: bool

class Params(NamedTuple):
    workspace: str
    sortings:  Any
    dry_run:   bool

def init() -> Params:
    description = "Convert a sortings.json file into a populated Labbox workspace."
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--workspace-uri', '-W', action='store', default=None,
        help="URI of workspace to add data to. If None (default), a new workspace will be created.")
    parser.add_argument('--feed-name', '-F', action='store', default=None,
        help="Name of feed to attach workspace to. If not specified, a new feed will be created. " + 
             "Only used if no workspace uri is set.")
    parser.add_argument('--sortings-file', '-s', action='store', default=None,
        help="Path to sortings file.")
    parser.add_argument('--sortings-file-kachery-uri', '-k', action='store', default=None,
        help="kachery URI for sortings file. Exactly one of --sortings-file and --sortings-file-kachery-uri "
           + "should be set.")
    parser.add_argument('--dry-run', action='store_true', default=False,
        help="If set, script will only parse the input files and display the workspace commands it would have run.")
    parsed = parser.parse_args()

    if parsed.dry_run:
        workspace_uri = 'Dry run, no workspace actually used'
    else:
        workspace_uri = parsed.workspace_uri or create_workspace()
    if ((parsed.sortings_file is None and parsed.sortings_file_kachery_uri is None)
         or (parsed.sortings_file is not None and parsed.sortings_file_kachery_uri is not None)):
        raise Exception("Exactly one of sortings_file and sortings_file_kachery_uri must be set.")
    if parsed.sortings_file is not None:
        with open(parsed.sortings_file) as fp:
            sortings = json.load(fp)
    else:
        sortings = kp.load_json(parsed.sortings_file_kachery_uri)
    return Params(workspace_uri, sortings, parsed.dry_run)

def create_workspace() -> str:
    workspace = le.create_workspace(label='sortingview-default')
    kp.set('sortingview-default-workspace', workspace.uri)
    return workspace.uri

def get_known_recording_id(workspace: Union[le.Workspace, None], recording_label: str) -> str:
    if workspace is None: return None
    for (_, v) in workspace._recordings.items():
        if v['recordingLabel'] == recording_label:
            return v['recordingId']
    return None

def sortings_are_in_workspace(workspace: Union[le.Workspace, None], gt: str, comp: str) -> Tuple[bool, bool]:
    if workspace is None: return (False, False)
    sortings = [workspace._sortings[key]['sortingLabel'] for key in workspace._sortings.keys()]
    return (gt in sortings, comp in sortings)

def get_labels(entry: RecordingEntry) -> Tuple[str, str]:
    recording_label = entry.study_set_label + "\\" + entry.recording_name
    ground_truth_label = f'{TRUE_SORT_LABEL}\{recording_label}'
    return (recording_label, ground_truth_label)

def populate_extractors(entry: RecordingEntry) -> Tuple[le.LabboxEphysRecordingExtractor, le.LabboxEphysSortingExtractor, le.LabboxEphysSortingExtractor]:
    recording = le.LabboxEphysRecordingExtractor(entry.recording_uri, download=True)
    sample_rate = recording.get_sampling_frequency()
    sorting_true = le.LabboxEphysSortingExtractor(entry.sorting_true_uri, samplerate=sample_rate)
    sorting = le.LabboxEphysSortingExtractor(entry.sorting_object, samplerate=sample_rate)
    return (recording, sorting_true, sorting)

def add_entry_to_workspace(re: FullRecordingEntry, workspace: le.Workspace) -> None:
    if re.R_id is None:
        re.R_id = workspace.add_recording(recording=re.recording, label=re.recording_label)
    if not re.gt_exists:
        GT_id = workspace.add_sorting(sorting=re.sorting_true, recording_id=re.R_id, label=re.ground_truth_label)
    if not re.sorting_exists:
        s_id = workspace.add_sorting(sorting=re.sorting, recording_id=re.R_id, label=re.sorting_label)
    # TODO: Do something useful with the result codes here?

def add_entry_dry_run(re: FullRecordingEntry) -> None:
    if re.R_id is not None:
        print(f"Not adding {re.recording_label} as it is already in the workspace.")
    else:
        print(f"Would add {re.recording.get_num_channels()}-channel recording with label {re.recording_label}")
    if re.gt_exists:
        print(f"Not adding {re.ground_truth_label} as it is already in the workspace.")
    else:
        print(f"Would add GT at {len(re.true_sort.get_unit_ids())} units with label {re.ground_truth_label}")
    if re.sorting_exists:
        print(f"Not adding {re.sorting_label} as it is already in the workspace.")
    else:
        print(f"Would add sorting of {len(re.sorting.get_unit_ids())} unit(s) with label {re.sorting_label}")

def parse_sortings(sortings: List[Any]) -> Generator[RecordingEntry, None, None]:
    for s in sortings:
        if 'sortingOutput' not in s: continue # when the underlying job errored
        name = s['recordingName']
        yield RecordingEntry(
            study_set_label  = s['studyName'],
            recording_name   = name,
            recording_uri    = s['recordingUri'],
            sorting_true_uri = s['groundTruthUri'],
            sorting_object   = s['sortingOutput'],
            sorting_label    = f"{s['sorterName']}\\{s['studyName']}\\{name}"
        )

def main():
    (workspace_uri, sortings_json, dry_run) = init()
    workspace = None if dry_run else le.load_workspace(workspace_uri)
    loaded = 0
    for r in parse_sortings(sortings_json):
        (recording_label, ground_truth_label) = get_labels(r)
        (recording, sorting_true, sorting) = populate_extractors(r)
        R_id = get_known_recording_id(workspace, recording_label)
        (gt_exists, sorting_exists) = sortings_are_in_workspace(workspace, ground_truth_label, r.sorting_label)
        entry = FullRecordingEntry(
            recording_label, ground_truth_label, r.sorting_label,
            R_id, recording, sorting_true, sorting,
            gt_exists, sorting_exists
        )
        if dry_run:
            add_entry_dry_run(re=entry, workspace=workspace)
        else:
            add_entry_to_workspace(re=entry)
        loaded += 1
    print(f"Loaded {loaded} recording sets to workspace {workspace_uri}")

if __name__ == "__main__":
    main()