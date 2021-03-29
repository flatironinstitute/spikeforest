#!/usr/bin/python

import argparse
import json
import os
import time
from typing import Any, Dict, List, TypedDict, Union, cast
import spikeextractors as se
import hither2 as hi
import kachery_p2p as kp
import labbox_ephys as le

thisdir = os.path.dirname(os.path.realpath(__file__))
spiketoolkit_image = hi.DockerImageFromScript(name='magland/spiketoolkit', dockerfile=f'{thisdir}/docker/Dockerfile')

class ArgsDict(TypedDict):
    verbose: int
    test: int
    sortingsfile: str
    recordingset: str
    outfile: str
    workercount: int

args: Union[ArgsDict, None] = None

RECORDING_URI_KEY = 'recordingUri'
GROUND_TRUTH_URI_KEY = 'sortingTrueUri'
SORTING_FIRINGS_URI_KEY = 'firings'
QUALITY_METRICS = [
    "num_spikes",
    "firing_rate",
    "presence_ratio",
    "isi_violation",
    "amplitude_cutoff",
    "snr",
    "max_drift",
    "cumulative_drift",
    "silhouette_score",
    "isolation_distance",
    "l_ratio",
    "nn_hit_rate",
    "nn_miss_rate",
    "d_prime"
]

def init_args():
    args: ArgsDict = {
        'verbose': 0,
        'test': 0,
        'sortingsfile': '',
        'recordingset': '',
        'outfile': '',
        'workercount': 0
    }
    parser = argparse.ArgumentParser(description="Compute ground-truth comparisons and quality metrics for SpikeForest records.")
    parser.add_argument('--verbose', '-v', action='count', default=0)
    parser.add_argument('--test', '-t', action='store', type=int, default=0,
        help="If non-zero, this will set a maximum number of iterations before quitting, " +
        "to give a usable sample without processing the entire data set.")
    parser.add_argument('--sortingsfile', '-s', action='store',
        default='sha1://31ea996f4aa43e1cb8719848753ebfed3a184503/example.json',
        help="The path or kachery URI for the JSON file which contains the sortings. The sortings file content " +
            "should be equivalent to the output of an API call to SpikeForest.")
    parser.add_argument('--recordingset', '-r', action='store', default='',
        help='If set, will limit processing to the set of recordings named in the variable (e.g. "paired_kampff").')
    parser.add_argument('--outfile', '-o', action='store', default=None,
        help='If set, JSON output (but not warnings/messages) will be written to this file (instead of to STDOUT).')
    parser.add_argument('--workercount', '-w', action='store', type=int, default=4,
        help="If set, determines the number of worker threads for a parallel job handler.")
    parsed = parser.parse_args()
    # We would very much like to avoid this, unfortunately the argsparse module and the typing module don't play
    # at all nicely with each other. For a more robust script, we'd want to try a different solution,
    # maybe the Tap/Typed Argument Parser module
    args['verbose'] = parsed.verbose
    args['test'] = parsed.test
    args['sortingsfile'] = parsed.sortingsfile
    args['recordingset'] = parsed.recordingset
    args['outfile'] = parsed.outfile
    args['workercount'] = parsed.workercount
    if args['workercount'] < 1: args['workercount'] = 1
    if parsed.outfile is not None and parsed.outfile != '' and os.path.exists(parsed.outfile):
        raise Exception('Error: Requested to write to an existing output file. Aborting to avoid overwriting file.')
    return args

def print_per_verbose(lvl: int, msg: str):
    if args and (args['verbose'] < lvl): return
    tabs = max(0, lvl - 1)
    print("\t" * tabs + msg)

def load_sortings() -> List[Dict[str, Any]]:
    hydrated_sortings = kp.load_json(args['sortingsfile'])
    assert hydrated_sortings is not None
    return cast(List[Dict[str, Any]], hydrated_sortings)

def compute_quality_metrics(recording: se.RecordingExtractor, sorting: se.SortingExtractor) -> str:
    # import within function in case we don't have spiketoolkit installed outside the container
    import spiketoolkit as st
    expected_version = '0.7.4'
    assert st.__version__ == expected_version, f'Unexpected spiketoolkit version: {st.__version__} <> {expected_version}'
    return st.validation.compute_quality_metrics(
        sorting, recording,
        metric_names=QUALITY_METRICS, as_dataframe=True).to_dict()

def compare_with_ground_truth(sorting: se.SortingExtractor, gt_sorting: se.SortingExtractor):
    # import within function in case we don't have spikecomparison installed outside the container
    import spikecomparison as sc
    expected_sc_version = '0.3.2'
    assert sc.__version__ == expected_sc_version, f'Unexpected spiketoolkit version: {sc.__version__} <> {expected_sc_version}'
    ground_truth_comparison = sc.GroundTruthComparison(gt_sorting, sorting)

    return {"best_match_21": ground_truth_comparison.best_match_21.to_list(),
            "best_match_12": ground_truth_comparison.best_match_12.to_list(),
            "agreement_scores": ground_truth_comparison.agreement_scores.to_dict()}

@hi.function(
    'compute_quality_metrics_hi', '0.1.1',
    image=spiketoolkit_image,
    kachery_support=True,
    modules=['labbox_ephys', 'labbox']
)
def compute_quality_metrics_hi(recording_uri, gt_uri, firings_uri):
    # gt_uri is not needed, but including it lets this method and the ground truth comparison use the same consistent kwargs parameters.
    print_per_verbose(1, f"Computing quality metrics for recording {recording_uri} and sorting {firings_uri}. Fetching Extractors...")
    print_per_verbose(2, f"Execting le.LabboxEphysRecordingExtractor({recording_uri})")
    recording = le.LabboxEphysRecordingExtractor(recording_uri)
    sample_rate = recording.get_sampling_frequency()
    print_per_verbose(2, f"Found sample rate {sample_rate}.")
    sorting_object = {
        'sorting_format': 'mda',
        'data': {
            'firings': firings_uri,
            'samplerate': sample_rate
        }
    }
    print_per_verbose(2, f"(Comparison evaluation) Executing le.labboxEphysSortingExtractor({json.dumps(sorting_object)})")
    sorting = le.LabboxEphysSortingExtractor(sorting_object)
    print_per_verbose(2, f"Executing quality metrics")
    try:
        qm = compute_quality_metrics(recording, sorting)
    except Exception as e:
        print(f"WARNING: Problem in compute_quality_metrics:\n{e}")
        qm = f"Quality metric computation for recording {recording_uri} sorting {firings_uri} returned error:\n{e}"
    return qm

@hi.function(
    'compute_ground_truth_comparison_hi', '0.1.1',
    image=spiketoolkit_image,
    kachery_support=True,
    modules=['labbox_ephys', 'labbox']
)
def compute_ground_truth_comparison_hi(recording_uri, gt_uri, firings_uri):
    print_per_verbose(1, f"Computing ground truth comparison for ground truth {gt_uri} and sorting {firings_uri} (recording {recording_uri})")
    print_per_verbose(3, f'Fetching sample rate from {recording_uri}')
    recording = le.LabboxEphysRecordingExtractor(recording_uri)
    sample_rate = recording.get_sampling_frequency()
    print_per_verbose(3, f'Got sample rate {sample_rate}')
    print_per_verbose(2, f"Building sorting object for ground truth {gt_uri}")
    gt_firings = kp.load_json(gt_uri)['firings']
    print_per_verbose(2, f"Got ground truth firings {gt_firings}")
    gt_sorting_obj = {
        'sorting_format': 'mda',
        'data': {
            'firings': gt_firings,
            'samplerate': sample_rate
        }
    }
    gt_sorting = le.LabboxEphysSortingExtractor(gt_sorting_obj)
    print_per_verbose(2, f"Building sorting object for sorting with firings {firings_uri}")
    sorting_obj = {
        'sorting_format': 'mda',
        'data': {
            'firings': firings_uri,
            'samplerate': sample_rate
        }
    }
    sorting = le.LabboxEphysSortingExtractor(sorting_obj)
    print_per_verbose(2, f"Executing ground-truth comparison")
    try:
        gt = compare_with_ground_truth(sorting, gt_sorting)
    except Exception as e:
        print(f"WARNING: Problem in compute_ground_truth_comparison:\n{e}")
        gt = f"Ground truth comparison for gt {gt_uri} and sorting {firings_uri} returned error:\n{e}"
    return gt

def process_sorting_record(sorting_record, comparison_result_list):
    try:
        params = {
            'recording_uri': sorting_record[RECORDING_URI_KEY],
            'gt_uri': sorting_record[GROUND_TRUTH_URI_KEY],
            'firings_uri': sorting_record[SORTING_FIRINGS_URI_KEY]
        }
        quality_metric_job = hi.Job(compute_quality_metrics_hi, params)
        ground_truth_comparison_job = hi.Job(compute_ground_truth_comparison_hi, params)
        comparison = make_comparison_entry(sorting_record, quality_metric_job, ground_truth_comparison_job)
        comparison_result_list.append(comparison)
    except KeyError:
        print(f"One of sorting/recording/gt-sorting keys missing from {json.dumps(sorting_record)}. Skipping...")

def make_comparison_entry(sorting_record, quality_metric_job, gt_comparison_job):
    return {
        'studyName': sorting_record['studyName'],
        'recordingName': sorting_record['recordingName'],
        'sorterName': sorting_record['sorterName'],
        'quality_metric': quality_metric_job,
        'ground_truth_comparison': gt_comparison_job
    }

def extract_sorting_reference_name(comparison_object) -> str:
    return f"({comparison_object['studyName']} {comparison_object['recordingName']} {comparison_object['sorterName']})"

def output_results(comparison_list):
    for comparison_object in comparison_list:
        quality_job = comparison_object['quality_metric']
        ground_truth_comparison_job = comparison_object['ground_truth_comparison']
        if quality_job.status == 'finished' and ground_truth_comparison_job.status == 'finished':
            comparison_object['quality_metric'] = quality_job.result.return_value
            comparison_object['ground_truth_comparison'] = ground_truth_comparison_job.result.return_value
            continue
        if quality_job.status == 'error':
            # This should no longer happen
            print(f"WARNING: quality job for {extract_sorting_reference_name(comparison_object)} had an error.")
        elif quality_job.status != 'finished':
            print(f"WARNING: unfinished non-errored quality job in {extract_sorting_reference_name(comparison_object)}--possible hither error")
        if ground_truth_comparison_job.status == 'error':
            # This should no longer happen
            print(f"WARNING: comparison job for {extract_sorting_reference_name(comparison_object)} had an error.")
        elif ground_truth_comparison_job.status != 'finished':
            print(f"WARNING: unfinished non-errored comparison job in {extract_sorting_reference_name(comparison_object)}--possible hither error")
            
        # Replace problematic jobs with an error message (since the job itself cannot be serialized)
        comparison_object['quality_metric'] = f"Job status: {quality_job.status}"
        comparison_object['ground_truth_comparison'] = f"Job status: {ground_truth_comparison_job.status}"

    if args['outfile'] is not None and args['outfile'] != '':
        with open(args['outfile'], 'x') as f:
            print(json.dumps(comparison_list, indent=4), file=f)
    else:
        print(f"Results:\n{json.dumps(comparison_list, indent=4)}")

def main():
    use_container = os.getenv('HITHER_USE_CONTAINER') in ['TRUE', '1']
    if use_container:
        if os.getenv('HITHER_USE_SINGULARITY'):
            print('Using singularity containers')
        else:
            print('Using docker containers')
    else:
        print('Not using containers.')
        print('To use container set one or both of the following environment variables:')
        print('HITHER_USE_CONTAINER=1')
        print('HITHER_USE_SINGULARITY=1')

    print(f"\t\tScript execution beginning at {time.ctime()}")
    start_time = time.time()
    global args
    args = init_args()
    if args['test'] != 0: print(f"\tRunning in TEST MODE--Execution will stop after processing {args['test']} sortings!\n")
    count = 0
    sortings = load_sortings()
    comparison_list = []

    if args['recordingset'] is not None and args['recordingset'] != '':
        sortings = [s for s in sortings if s['studyName'] == args['recordingset']]

    # Define job cache and (parallel) job handler
    jc = hi.JobCache(feed_name='default-job-cache')
    jh = hi.ParallelJobHandler(num_workers=args['workercount'])

    with hi.Config(job_cache=jc, job_handler=jh, use_container=use_container):
        for sorting_record in sortings:
            print_per_verbose(2, f"Creating job-pair {count + 1} ({extract_sorting_reference_name(sorting_record)})")
            process_sorting_record(sorting_record, comparison_list)
            count += 1
            if args['test'] > 0 and count >= args['test']: break

    print_per_verbose(1, f'{count*2} jobs have been queued. Now waiting for them to complete.')
    hi.wait(None)
    output_results(comparison_list)
    print(f"\n\n\t\tElapsed time: {time.time() - start_time:.3f} sec")
    print(f"\t\tScript execution complete at {time.ctime()}")


if __name__ == "__main__":
    main()
