import argparse
import json
import numpy as np
import spikeextractors as se
from typing import Any, Dict, List, NamedTuple

import labbox_ephys as le
import kachery_p2p as kp

## TODO: Create new workspace?
## TODO: Handle sample rate more gracefully?
## TODO: Need to do error checking on output ids?

TRUE_SORT_LABEL = "Ground Truth"

class SortingTuple(NamedTuple):
    uri:   str
    label: str

class RecordingSet(NamedTuple):
    study_set_label:  str
    recording_name:   str
    recording_uri:    str
    # TODO SAMPLE RATE??
    sorting_true_uri: str
    sortings:         List[SortingTuple]

class Params(NamedTuple):
    workspace: str
    sortings:  Any
    dry_run:   bool

# TODO: Idempotency--if you add the same recording/sorting twice, should not get double entries.

def init() -> Params:
    description = "Convert a sortings.json file into a populated Labbox workspace."
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--workspace-uri', '-w', action='store', default=None,
        help="URI of workspace to add data to. If None (default), a new workspace will be created.")
    parser.add_argument('--feed-name', '-F', action='store', default=None,
        help="Name of feed to attach workspace to. If not specified, a new feed will be created.")
    parser.add_argument('--sortings-file', '-s', action='store', default=None,
        help="Path to sortings file.")
    parser.add_argument('--sortings-file-kachery-uri', '-k', action='store', default=None,
        help="kachery URI for sortings file. Exactly one of --sortings-file and --sortings-file-kachery-uri "
           + "should be set.")
    parser.add_argument('--dry-run', action='store_true', default=False,
        help="If set, script will only parse the input files and display the workspace commands it would have run.")
    parsed = parser.parse_args()

    workspace = parsed.workspace_uri
    if (not workspace):
        if parsed.dry_run:
            workspace = 'Dry run, no workspace created'
        else:
            # TODO: Create workspace if one is not specified
            raise NotImplementedError("Workspace creation is not yet implemented.")
    if ((parsed.sortings_file is None and parsed.sortings_file_kachery_uri is None)
         or (parsed.sortings_file is not None and parsed.sortings_file_kachery_uri is not None)):
        raise Exception("Exactly one of sortings_file and sortings_file_kachery_uri must be set.")
    if parsed.sortings_file is not None:
        with open(parsed.sortings_file) as fp:
            sortings = json.load(fp)
    else:
        sortings = kp.load_json(parsed.sortings_file_kachery_uri)
    return Params(workspace, sortings, parsed.dry_run)

def create_workspace() -> le.Workspace:
    feed = kp.load_feed('franklab-example-feed', create=True)
    workspace = le.load_workspace(workspace_uri=f'workspace://{feed.get_feed_id()}/default')
    return workspace

def parse_sortings(sortings: Any) -> List[RecordingSet]:
    recording_records: Dict[str, Any] = {}
    for s in sortings:
        name = s['recordingName']
        if name not in recording_records:
            recording_records[s['recordingName']] = RecordingSet(
                study_set_label  = s['studyName'],
                recording_name   = name,
                recording_uri    = s['recordingUri'],
                sorting_true_uri = s['groundTruthUri'],
                sortings         = []
            )
        if 'sortingOutput' not in s: continue # when the underlying job errored
        recording_records[name].sortings.append(SortingTuple(
            uri   = s['sortingOutput']['data']['h5_path'],
            label = f"{s['sorterName']}--{s['recordingName']}"
        ))
    return [recording_records[k] for k in recording_records.keys()]

def main():
    (workspace_uri, sortings_json, dry_run) = init()
    if not dry_run:
        workspace = le.load_workspace(workspace_uri)
        workspace_uri = workspace.get_uri()
    recording_sets = parse_sortings(sortings_json)
    for r in recording_sets:
        recording = le.LabboxEphysRecordingExtractor(r.recording_uri, download=True)
        recording_label = r.study_set_label + "\\" + r.recording_name
        # TODO: SAMPLE RATE -- assumed 30k
        sorting_true = le.LabboxEphysSortingExtractor(r.sorting_true_uri, samplerate=30000)
        if dry_run:
            print(f"Adding {recording.get_num_channels()}-channel recording with label {recording_label}")
            print(f"Adding GT at {len(sorting_true.get_unit_ids())} units with label {TRUE_SORT_LABEL}")
            for s in r.sortings:
                sorting = le.LabboxEphysSortingExtractor(s.uri, samplerate=30000)
                print(f"Adding sorting {len(sorting.get_unit_ids())} with label {s.label}")
        else:
            R_id = workspace.add_recording(recording=recording, label=recording_label)
            GT_id = workspace.add_sorting(sorting=sorting_true, recording_id=R_id, label=TRUE_SORT_LABEL)
            s_ids = [workspace.add_sorting(
                        sorting=le.LabboxEphysSortingExtractor(s.uri, samplerate=30000),
                        recording_id=R_id,
                        label=s.label)
                     for s in r.sortings]
            # TODO: Something useful with these returned ids? Error check?
    print(f"Loaded {len(recording_sets)} recording sets to workspace {workspace_uri}")

if __name__ == "__main__":
    main()