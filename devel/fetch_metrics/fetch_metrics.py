#!/usr/bin/python

import argparse
import json
import os
from spikeextractors import RecordingExtractor, SortingExtractor
from spikecomparison import GroundTruthComparison
import spiketoolkit as st
from typing import Any, Dict, List, TypedDict, Union

import hither2 as hi
import kachery_p2p as kp
import labbox_ephys as le

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
        default='/home/jsoules/src/spikeforest_recordings/sortings.json',
        help="The full path for the JSON file which contains the sortings. The sortings file content " +
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
    if args['verbose'] < lvl: return
    tabs = max(0, lvl - 1)
    print("\t" * tabs + msg)

def slurp(filename: str) -> str:
    as_one_string = ''
    with open(filename) as f:
        while True:
            line = f.readline().rstrip()
            if not line: break
            as_one_string += line
    return as_one_string

def load_sortings() -> List[Dict[str, Any]]:
    hydrated_sortings = json.loads(slurp(args['sortingsfile']))
    return hydrated_sortings

def compute_quality_metrics(recording: RecordingExtractor, sorting: SortingExtractor) -> str:
    return st.validation.compute_quality_metrics(
        sorting, recording,
        metric_names=QUALITY_METRICS, as_dataframe=True).to_dict()

def compare_with_ground_truth(sorting: SortingExtractor, gt_sorting: SortingExtractor):
    ground_truth_comparison = GroundTruthComparison(gt_sorting, sorting)

    return {"best_match_21": ground_truth_comparison.best_match_21.to_list(),
            "best_match_12": ground_truth_comparison.best_match_12.to_list(),
            "agreement_scores": ground_truth_comparison.agreement_scores.to_dict()}

@hi.function(
    'compute_quality_metrics_hi', '0.1.0',
    kachery_support=True
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
    return compute_quality_metrics(recording, sorting)

@hi.function(
    'compute_ground_truth_comparison_hi', '0.1.0',
    kachery_support=True
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
    return compare_with_ground_truth(sorting, gt_sorting)

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
        if quality_job.status == 'error' or ground_truth_comparison_job.status == 'error':
            print(f"ERROR: comparison {extract_sorting_reference_name(comparison_object)} had an errored job.")
        elif quality_job.status != 'finished' or ground_truth_comparison_job.status != 'finished':
            print(f"ERROR: unfinished non-errored job in {extract_sorting_reference_name(comparison_object)}--possible hither error")
        # Replace problematic jobs with an error message (since the job itself cannot be serialized)
        comparison_object['quality_metric'] = f"Job status: {quality_job.status}"
        comparison_object['ground_truth_comparison'] = f"Job status: {ground_truth_comparison_job.status}"

    if args['outfile'] is not None and args['outfile'] != '':
        with open(args['outfile'], 'x') as f:
            print(json.dumps(comparison_list, indent=4), file=f)
    else:
        print(f"Results:\n{json.dumps(comparison_list, indent=4)}")

def main():
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

    with hi.Config(job_cache=jc, job_handler=jh):
        for sorting_record in sortings:
            print_per_verbose(2, f"Creating job-pair {count + 1} ({extract_sorting_reference_name(sorting_record)})")
            process_sorting_record(sorting_record, comparison_list)
            count += 1
            if args['test'] > 0 and count >= args['test']: break

    print_per_verbose(1, f'{count*2} jobs have been queued. Now waiting for them to complete.')
    hi.wait(None)
    output_results(comparison_list)



if __name__ == "__main__":
    main()
