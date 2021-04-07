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
expected_spiketoolkit_version = '0.7.4'
expected_spikecomparison_version = '0.3.2'

class ArgsDict(TypedDict):
    verbose: int
    test: int
    sortingsfile: str
    recordingset: str
    outfile: str
    workercount: int
    job_cache: Union[str, None]
    use_container: bool
    use_slurm: bool
    slurm_max_jobs_per_alloc: int
    slurm_max_simultaneous_allocs: int
    slurm_command: str

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
        help="If set, determines the number of worker threads for a parallel job handler. Ignored if using slurm.")
    parser.add_argument('--job_cache', action='store', type=str, default='default-job-cache',
        help="If set, indicates the feed name for the job cache feed.")
    parser.add_argument('--no_job_cache', action='store_true', default=False,
        help="If set, job cache will not be used, and any value for --job_cache will be ignored.")
    parser.add_argument('--use_container', '-C', action='store_true', default=False,
        help='If set, hither calls will use containerization. If unset, containerization may still be used if ' +
        'environment variable HITHER_USE_CONTAINER is set to "1" or "TRUE".')
    parser.add_argument('--no_container', action='store_true', default=False,
        help='Override HITHER_USE_CONTAINER environment variable to suppress container use. Ignored if --use_container is set.')
    parser.add_argument('--use_slurm', action='store_true', default=False,
        help='If set, this script will use a SlurmJobHandler and attempt to run jobs on the configured cluster. The exact ' +
        'call used by the slurm job handler to acquire resources can be customized with command-line arguments.')
    parser.add_argument('--slurm_partition', action='store', type=str, default="ccm",
        help='If set, slurm will use the specified text as a partition name to request. Note that slurm must be explicitly ' +
        'requested with the --use_slurm flag; if it is not, this value is ignored.')
    parser.add_argument('--slurm_accept_shared_nodes', action='store_true', default=False,
        help='If set, slurm calls will be made without --exclusive. Note that slurm must still be explicitly ' +
        'requested with the --use_slurm flag; if it is not, this value is ignored.')
    parser.add_argument('--slurm_jobs_per_allocation', action='store', type=int, default=6,
        help='Controls the max length of job processing queues for slurm nodes. Default 6.')
    parser.add_argument('--slurm_max_simultaneous_allocations', action='store', type=int, default=5,
        help='The maximum number of job processing queues/slurm nodes to be requested. Default 5.')
    parser.add_argument('--check_config', action='store_true', default=False,
        help='Debugging tool. If set, program will simply quit with a description of the parsed configuration.')
    parsed = parser.parse_args()
    return parsed

def init_configuration():
    args: ArgsDict = {
        'verbose': 0,
        'test': 0,
        'sortingsfile': '',
        'recordingset': '',
        'outfile': '',
        'workercount': 0,
        'job_cache': 'default-job-cache',
        'use_container': False,
        'use_slurm': False,
        'slurm_max_jobs_per_alloc': 6,
        'slurm_max_simultaneous_allocs': 5,
        'slurm_command': ""
    }
    parsed = init_args()
    # We would very much like to avoid this manual copying, unfortunately the argsparse module and the typing module
    # don't play at all nicely with each other. For a more robust script, we'd want to try a different solution,
    # maybe the Tap/Typed Argument Parser module
    args['verbose'] = parsed.verbose or 0
    args['test'] = parsed.test
    args['sortingsfile'] = parsed.sortingsfile
    args['recordingset'] = parsed.recordingset
    args['outfile'] = parsed.outfile
    args['workercount'] = max(parsed.workercount, 1)
    args['job_cache'] = None if parsed.no_job_cache else parsed.job_cache
    args['use_container'] = parsed.use_container or ((not parsed.no_container) and os.getenv('HITHER_USE_CONTAINER') in ['TRUE', '1'])
    args['use_slurm'] = parsed.use_slurm
    args['slurm_max_jobs_per_alloc'] = parsed.slurm_jobs_per_allocation
    args['slurm_max_simultaneous_allocs'] = parsed.slurm_max_simultaneous_allocations
    # example srun_command: srun --exclusive -n 1 -p <partition>
    args['slurm_command'] = f"srun -n 1 -p {parsed.slurm_partition} {'--exclusive' if not parsed.slurm_accept_shared_nodes else ''}"
    if parsed.outfile is not None and parsed.outfile != '' and os.path.exists(parsed.outfile) and parsed.outfile != "/dev/null":
        raise Exception('Error: Requested to write to an existing output file. Aborting to avoid overwriting file.')
    if(parsed.check_config):
        print(f"""Received the following environment vars:
            HITHER_USE_CONTAINER: {os.getenv('HITHER_USE_CONTAINER')}
            HITHER_USE_SINGULARITY: {os.getenv('HITHER_USE_SINGULARITY')}
        """)
        print(f"\n\tFinal configuration:\n{json.dumps(args, indent=4)}")
        exit()
    # configure verbosity for the run
    print_per_verbose.__dict__['verbosity_level'] = args['verbose']
    return args

def print_per_verbose(lvl: int, msg: str):
    # verbosity_level is a static value, initialized from command-line argument at setup time in init_configuration().
    # This does not play nicely with containerization, but global arguments variables don't either; rather than passing
    # needless verbosity parameters around, we're just going to bail if the verbosity_level property isn't set.
    if ('verbosity_level' not in print_per_verbose.__dict__): return
    if (print_per_verbose.verbosity_level < lvl): return
    tabs = max(0, lvl - 1)
    print("\t" * tabs + msg)

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

def main():
    args = init_configuration()
    use_container = args['use_container']
    if args['test'] != 0: print(f"\tRunning in TEST MODE--Execution will stop after processing {args['test']} sortings!\n")
    sortings = load_sortings(args['sortingsfile'])
    if args['recordingset'] is not None and args['recordingset'] != '':
        sortings = [s for s in sortings if s['studyName'] == args['recordingset']]

    if use_container:
        print_per_verbose(1, f"Using {'Singularity' if os.getenv('use_singularity') else 'Docker'} containers.")
    else:
        print_per_verbose(1, "Running without containers.")

    # Define job cache and job handler
    jc = None if args['job_cache'] == None else hi.JobCache(feed_name=args['job_cache'])
    if args['use_slurm']:
        jh = hi.SlurmJobHandler(
            num_jobs_per_allocation=args['slurm_max_jobs_per_alloc'],
            max_simultaneous_allocations=args['slurm_max_simultaneous_allocs'],
            srun_command=args['slurm_command']
        )
    else:
        jh = hi.ParallelJobHandler(num_workers=args['workercount'])

    try:
        print(f"\t\tScript execution beginning at {time.ctime()}")
        count = 0
        comparison_list = []
        start_time = time.time()
        log = hi.Log()
        with hi.Config(job_cache=jc, job_handler=jh, use_container=use_container, log=log):
            for sorting_record in sortings:
                print_per_verbose(2, f"Creating job-pair {count + 1} ({extract_sorting_reference_name(sorting_record)})")
                process_sorting_record(sorting_record, comparison_list)
                count += 1
                if args['test'] > 0 and count >= args['test']: break
        print_per_verbose(1, f'{count*2} jobs have been queued. Now waiting for them to complete.')
        hi.wait(None)
    finally:
        jh.cleanup()

    output_results(comparison_list, args['outfile'])
    print(f"\n\n\t\tElapsed time: {time.time() - start_time:.3f} sec")
    print(f"\t\tScript execution complete at {time.ctime()}")


if __name__ == "__main__":
    main()
