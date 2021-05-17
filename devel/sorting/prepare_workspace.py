import argparse
import json
import numpy as np
import spikeextractors as se
from typing import Any, Dict, Generator, List, NamedTuple, Union

import labbox_ephys as le
import kachery_p2p as kp

## TODO: Create new workspace?
## TODO: Handle sample rate more gracefully?
## TODO: Need to do error checking on output ids?

TRUE_SORT_LABEL = "Ground Truth"

class RecordingEntry(NamedTuple):
    study_set_label:  str
    recording_name:   str
    recording_uri:    str
    # TODO SAMPLE RATE??
    sorting_true_uri: str
    sorting_object:   Dict[any, any]
    sorting_label:    str

class Params(NamedTuple):
    workspace: str
    sortings:  Any
    dry_run:   bool

# TODO: Idempotency--if you add the same recording/sorting twice, should not get double entries.

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

def add_entry_to_workspace(entry: RecordingEntry,
                           workspace: Union[le.Workspace, None],
                           dry_run: bool = True) -> None:
    recording = le.LabboxEphysRecordingExtractor(entry.recording_uri, download=True)
    recording_label = entry.study_set_label + "\\" + entry.recording_name
    # TODO: SAMPLE RATE -- assumed 30k, need to fix that!!!
    sample_rate = 30000
    sorting_true = le.LabboxEphysSortingExtractor(entry.sorting_true_uri, samplerate=sample_rate)
    sorting = le.LabboxEphysSortingExtractor(entry.sorting_object, samplerate=sample_rate)
    if dry_run:
        print(f"Adding {recording.get_num_channels()}-channel recording with label {recording_label}")
        print(f"Adding GT at {len(sorting_true.get_unit_ids())} units with label {TRUE_SORT_LABEL}")
        print(f"Adding sorting of {len(sorting.get_unit_ids())} unit(s) with label {entry.sorting_label}")
        return
    # TODO: CHECK IF RECORDING/SORTING ALREADY IN WORKSPACE
    R_id = workspace.add_recording(recording=recording, label=recording_label)
    GT_id = workspace.add_sorting(sorting=sorting_true, recording_id=R_id, label=TRUE_SORT_LABEL)
    # TODO: CHECK IF RECORDING/SORTING ALREADY IN WORKSPACE
    s_id = workspace.add_sorting(sorting=sorting, recording_id=R_id, label=entry.sorting_label)
    # TODO: Do something useful with the result codes here?


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
            sorting_label    = f"{s['sorterName']}--{name}"
        )

def main():
    (workspace_uri, sortings_json, dry_run) = init()
    if not dry_run:
        workspace = le.load_workspace(workspace_uri)
    loaded = 0
    for r in parse_sortings(sortings_json):
        add_entry_to_workspace(entry=r, workspace=workspace, dry_run=dry_run)
        loaded += 1
    print(f"Loaded {loaded} recording sets to workspace {workspace_uri}")

if __name__ == "__main__":
    main()