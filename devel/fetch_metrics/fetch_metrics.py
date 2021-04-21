#!/usr/bin/python

import argparse
import json
import os
import time
from typing import Any, Dict, List, TypedDict, cast
from spikeforest._common.calling_framework import add_standard_args, call_cleanup, extract_hither_config, parse_shared_configuration, print_per_verbose
import spikeextractors as se
import hither2 as hi
import kachery_p2p as kp
import labbox_ephys as le

thisdir = os.path.dirname(os.path.realpath(__file__))
spiketoolkit_image = hi.DockerImageFromScript(name='magland/spiketoolkit', dockerfile=f'{thisdir}/docker/Dockerfile')
expected_spiketoolkit_version = '0.7.4'
expected_spikecomparison_version = '0.3.2'

class ArgsDict(TypedDict):
    sortingsfile: str
    recordingset: str

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
    parser = argparse.ArgumentParser(description="Compute ground-truth comparisons and quality metrics for SpikeForest records.")
    parser.add_argument('--sortingsfile', '-s', action='store',
        default='sha1://31ea996f4aa43e1cb8719848753ebfed3a184503/example.json',
        help="The path or kachery URI for the JSON file which contains the sortings. The sortings file content " +
            "should be equivalent to the output of an API call to SpikeForest.")
    parser.add_argument('--recordingset', '-r', action='store', default='',
        help='If set, will limit processing to the set of recordings named in the variable (e.g. "paired_kampff").')
    parsed = add_standard_args(parser)
    return parsed

def init_configuration():
    args: ArgsDict = {
        'sortingsfile': '',
        'recordingset': '',
    }
    parsed = init_args()
    args['sortingsfile'] = parsed.sortingsfile
    args['recordingset'] = parsed.recordingset
    std_args = parse_shared_configuration(parsed)
    if (parsed.check_config):
        print(f"""Received the following environment vars:
            HITHER_USE_CONTAINER: {os.getenv('HITHER_USE_CONTAINER')}
            HITHER_USE_SINGULARITY: {os.getenv('HITHER_USE_SINGULARITY')}
        """)
        print(f"\n\tFinal Shared configuration:\n{json.dumps(std_args, indent=4)}")
        print(f"\n\tFinal configuration:\n{json.dumps(args, indent=4)}")
        exit()
    return (args, std_args)

def load_sortings(sortingsfile: str) -> List[Dict[str, Any]]:
    hydrated_sortings = kp.load_json(sortingsfile)
    assert hydrated_sortings is not None
    return cast(List[Dict[str, Any]], hydrated_sortings)

def compute_quality_metrics(recording: se.RecordingExtractor, sorting: se.SortingExtractor) -> str:
    # import within function in case we don't have spiketoolkit installed outside the container
    import spiketoolkit as st
    assert st.__version__ == expected_spiketoolkit_version, f'Unexpected spiketoolkit version: {st.__version__} <> {expected_spiketoolkit_version}'
    return st.validation.compute_quality_metrics(
        sorting, recording,
        metric_names=QUALITY_METRICS, as_dataframe=True).to_dict()

def compare_with_ground_truth(sorting: se.SortingExtractor, gt_sorting: se.SortingExtractor):
    # import within function in case we don't have spikecomparison installed outside the container
    import spikecomparison as sc
    assert sc.__version__ == expected_spikecomparison_version, f'Unexpected spiketoolkit version: {sc.__version__} <> {expected_spikecomparison_version}'
    ground_truth_comparison = sc.GroundTruthComparison(gt_sorting, sorting)

    return {"best_match_21": ground_truth_comparison.best_match_21.to_list(),
            "best_match_12": ground_truth_comparison.best_match_12.to_list(),
            "agreement_scores": ground_truth_comparison.agreement_scores.to_dict()}

@hi.function(
    'compute_quality_metrics_hi', '0.1.1',
    image=spiketoolkit_image,
    kachery_support=True,
    modules=['labbox_ephys', 'labbox', 'spikeforest']
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
    modules=['labbox_ephys', 'labbox', 'spikeforest']
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

def output_results(comparison_list, outfile):
    for comparison_object in comparison_list:
        quality_job = comparison_object['quality_metric']
        ground_truth_comparison_job = comparison_object['ground_truth_comparison']
        if quality_job.status == 'finished' and ground_truth_comparison_job.status == 'finished':
            comparison_object['quality_metric'] = quality_job.result.return_value
            comparison_object['ground_truth_comparison'] = ground_truth_comparison_job.result.return_value
            continue
        if quality_job.status == 'error':
            print(f"WARNING: quality job for {extract_sorting_reference_name(comparison_object)} had an error.")
        elif quality_job.status != 'finished':
            print(f"WARNING: unfinished non-errored quality job in {extract_sorting_reference_name(comparison_object)}--possible hither error")
        if ground_truth_comparison_job.status == 'error':
            print(f"WARNING: comparison job for {extract_sorting_reference_name(comparison_object)} had an error.")
        elif ground_truth_comparison_job.status != 'finished':
            print(f"WARNING: unfinished non-errored comparison job in {extract_sorting_reference_name(comparison_object)}--possible hither error")
            
        # Replace problematic jobs with an error message (since we can't serialize the job itself)
        comparison_object['quality_metric'] = f"Job status: {quality_job.status}"
        comparison_object['ground_truth_comparison'] = f"Job status: {ground_truth_comparison_job.status}"

    if outfile is not None and outfile != '':
        with open(outfile, 'x') as f:
            print(json.dumps(comparison_list, indent=4), file=f)
    else:
        print(f"Results:\n{json.dumps(comparison_list, indent=4)}")

def extraction_loop(sortings, comparison_list, max_iterations = 0):
    count = 0
    for sorting_record in sortings:
        print_per_verbose(2, f"Creating job-pair {count + 1} ({extract_sorting_reference_name(sorting_record)})")
        process_sorting_record(sorting_record, comparison_list)
        count += 1
        if max_iterations > 0 and count >= max_iterations: break
    print_per_verbose(1, f'{count*2} jobs have been queued. Now waiting for them to complete.')

def main():
    (args, std_args) = init_configuration()
    sortings = load_sortings(args['sortingsfile'])
    if args['recordingset'] is not None and args['recordingset'] != '':
        sortings = [s for s in sortings if s['studyName'] == args['recordingset']]
    hither_config = extract_hither_config(std_args)
    comparison_list = []
    try:
        print(f"\t\tScript execution beginning at {time.ctime()}")
        start_time = time.time()
        with hi.Config(**hither_config):
            extraction_loop(sortings, comparison_list, std_args['test'])
        hi.wait(None)
    finally:
        call_cleanup(hither_config)

    output_results(comparison_list, std_args['outfile'])
    print(f"\n\n\t\tElapsed time: {time.time() - start_time:.3f} sec")
    print(f"\t\tScript execution complete at {time.ctime()}")


if __name__ == "__main__":
    main()
