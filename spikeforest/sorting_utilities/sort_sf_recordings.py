from argparse import ArgumentParser
from typing import Any, Tuple, NamedTuple

import hither2 as hi
import labbox_ephys as le

from spikeforest._common.calling_framework import GROUND_TRUTH_URI_KEY, StandardArgs, add_standard_args, call_cleanup, parse_shared_configuration, print_per_verbose
from spikeforest.sorting_utilities.run_sortings import init_sorting_args, parse_argsdict, load_study_records, parse_sorters, extract_hither_config, sorting_loop, SortingJob
from spikeforest.sorting_utilities.prepare_workspace import FullRecordingEntry, add_entry_to_workspace, create_workspace, get_known_recording_id, get_labels, TRUE_SORT_LABEL, sortings_are_in_workspace

class Params(NamedTuple):
    study_source_file: str
    sorter_spec_file:  str
    workspace_uri:     str

class HydratedObjects(NamedTuple):
    workspace: le.Workspace
    recording: le.LabboxEphysRecordingExtractor
    gt_sort:   le.LabboxEphysSortingExtractor
    sorting:   le.LabboxEphysSortingExtractor

def init_configuration() -> Tuple[Params, StandardArgs]:
    description = "Runs all known sorters against configured SpikeForest recordings, and loads the " + \
        "results into a (new or existing) workspace for display."
    parser = ArgumentParser(description=description)
    parser.add_argument('--workspace-uri', '-W', action="store", default=None,
        help="URI of workspace to add data to. If None (default), a new workspace will be created.")
    parser = init_sorting_args(parser)
    parser = add_standard_args(parser)
    parsed = parser.parse_args()
    sortings_args = parse_argsdict(parsed)
    std_args = parse_shared_configuration(parsed)
    workspace_uri = parsed.workspace_uri
    if workspace_uri is None:
        workspace_uri = create_workspace()
    params = Params(
        study_source_file = sortings_args["study_source_file"],
        sorter_spec_file  = sortings_args["sorter_spec_file"],
        workspace_uri     = workspace_uri
    )
    return (params, std_args)

def populate_extractors(workspace_uri: str, rec_uri: str, gt_uri: str, sorting_result: Any) -> HydratedObjects:
    workspace = le.load_workspace(workspace_uri)
    recording = le.LabboxEphysRecordingExtractor(rec_uri, download=True)
    sample_rate = recording.get_sampling_frequency()
    gt_sort = le.LabboxEphysSortingExtractor(gt_uri, samplerate=sample_rate)
    sorting = le.LabboxEphysSortingExtractor(sorting_result, samplerate=sample_rate)
    return HydratedObjects(
        workspace = workspace,
        recording = recording,
        gt_sort   = gt_sort,
        sorting   = sorting
    )

@hi.function(
    'hi_post_result_to_workspace', '0.1.0',
    modules=['labbox_ephys', 'spikeforest'],
    kachery_support=True
)
def hi_post_result_to_workspace(
    sorting_entry: SortingJob,
    workspace_uri: str
) -> None:
    if (sorting_entry.sorting_job.status == "error"):
        print(f"Errored job: {sorting_entry.recording_name} {sorting_entry.sorter_name}")
        return
    items = populate_extractors(workspace_uri,
                                sorting_entry.recording_uri,
                                sorting_entry.ground_truth_uri,
                                sorting_entry.sorting_job.result.return_value)
    (r_label, gt_label, s_label) = get_labels(sorting_entry.study_name,
                                              sorting_entry.recording_name,
                                              GROUND_TRUTH_URI_KEY,
                                              sorting_entry.sorter_name)
    R_id = get_known_recording_id(items.workspace, r_label)
    (gt_exists, sorting_exists) = sortings_are_in_workspace(items.workspace, gt_label, s_label)
    entry = FullRecordingEntry(
        r_label, gt_label, s_label, R_id,
        items.recording, items.gt_sort, items.sorting,
        gt_exists, sorting_exists
    )
    add_entry_to_workspace(re=entry, workspace=items.workspace)

def main():
    (params, std_args) = init_configuration()
    study_sets = load_study_records(params.study_source_file)
    sorting_matrix = parse_sorters(params.sorter_spec_file, list(study_sets.keys()))
    hither_config = extract_hither_config(std_args)
    jobs: hi.Job = []

    try:
        with hi.Config(job_handler=None, job_cache=None):
            with hi.Config(**hither_config):
                sortings = list(sorting_loop(sorting_matrix, study_sets))
            for sorting in sortings:
                p = {
                    'sorting_entry': sorting,
                    'workspace_uri': params.workspace_uri
                }
                jobs.append(hi.Job(hi_post_result_to_workspace, p))
        hi.wait(None)
    finally:
        call_cleanup(hither_config)


if __name__ == "__main__":
    main()