#!/usr/bin/python

import datetime
import os
from typing import Any, TypedDict, NamedTuple, Union
import hither2 as hi


# NamedTuple is probably cleaner, but keeping a dict is more convenient for screen output.
class StandardArgs(TypedDict):
    test: int
    timeout_min: int
    outfile: str
    workercount: int
    job_cache: Union[str, None]
    use_container: bool
    use_slurm: bool
    slurm_max_jobs_per_alloc: int
    slurm_max_simultaneous_allocs: int
    slurm_command: str

class HitherConfiguration(TypedDict):
    job_handler: Any
    job_cache: Any
    use_container: bool
    log: Any


RECORDING_URI_KEY = 'recordingUri'
GROUND_TRUTH_URI_KEY = 'sortingTrueUri'
SORTING_FIRINGS_URI_KEY = 'firings'

def add_standard_args(parser: Any) -> Any:
    """Adds standard command-line arguments for interacting with hither/slurm calling conventions.
    Included arguments are --verbose (-v|vv|vvv...), --test (-t), --outfile (-o), --workercount (-w),
    --job-cache, --no-job-cache, --use-container, --no-container, --use-slurm, --slurm-partition,
    --slurm-accept-shared-nodes, --slurm-jobs-per-allocation, --slurm-max-simultaneous-allocations,
    --slurm-gpus-per-node, --timeout-min, and --check-config.

    Args:
        parser (Any): An initialized argparse ArgumentParser to extend.

    Returns:
        (Any): Formally untyped, this function returns the result of calling parser.parse_args().
    """
    parser.add_argument('--verbose', '-v', action='count', default=0,
        help="Set verbosity level. Add vs for more verbosity.")
    # Note: Whatever 'number of iterations' means for your application should be locally defined.
    parser.add_argument('--test', '-t', action='store', type=int, default=0,
        help="If non-zero, this will set a maximum number of iterations before quitting, " +
        "to give a usable sample without processing the entire data set.")
    parser.add_argument('--timeout-min', '-T', action='store', type=int, default=0,
        help="If non-zero, this will set a maximum duration for any job before it is cancelled.")
    parser.add_argument('--outfile', '-o', action='store', default=None,
        help='If set, output (but not warnings/messages) will be written to this file (instead of to STDOUT). ' +
             'Any existing file will NOT be overwritten; the program will abort instead.')
    parser.add_argument('--workercount', '-w', action='store', type=int, default=4,
        help="If set, determines the number of worker threads for a parallel job handler. Ignored if using slurm.")
    parser.add_argument('--job-cache', action='store', type=str, default='default-job-cache',
        help="If set, indicates the feed name for the job cache feed.")
    parser.add_argument('--no-job-cache', action='store_true', default=False,
        help="If set, job cache will not be used, and any value for --job-cache will be ignored.")
    parser.add_argument('--use-container', '-C', action='store_true', default=False,
        help='If set, hither calls will use containerization. If unset, containerization may still be used if ' +
        'environment variable HITHER_USE_CONTAINER is set to "1" or "TRUE".')
    parser.add_argument('--no-container', action='store_true', default=False,
        help='Override HITHER_USE_CONTAINER environment variable to suppress container use. Ignored if --use-container is set.')
    parser.add_argument('--use-slurm', action='store_true', default=False,
        help='If set, this script will use a SlurmJobHandler and attempt to run jobs on the configured cluster. The exact ' +
        'call used by the slurm job handler to acquire resources can be customized with command-line arguments.')
    parser.add_argument('--slurm-partition', action='store', type=str, default="ccm",
        help='If set, slurm will use the specified text as a partition name to request. Note that slurm must be explicitly ' +
        'requested with the --use-slurm flag; if it is not, this value is ignored.')
    parser.add_argument('--slurm-accept-shared-nodes', action='store_true', default=False,
        help='If set, slurm calls will be made without --exclusive. Note that slurm must still be explicitly ' +
        'requested with the --use-slurm flag; if it is not, this value is ignored.')
    parser.add_argument('--slurm-jobs-per-allocation', action='store', type=int, default=6,
        help='Controls the max length of job processing queues for slurm nodes. Default 6.')
    parser.add_argument('--slurm-max-simultaneous-allocations', action='store', type=int, default=5,
        help='The maximum number of job processing queues/slurm nodes to be requested. Default 5.')
    parser.add_argument('--slurm-gpus-per-node', action='store', type=int, default=0,
        help='If set, slurm commands will require this many GPUs per allocated node.')
    parser.add_argument('--check-config', action='store_true', default=False,
        help='Debugging tool. If set, program will simply quit with a description of the parsed configuration.')
    parsed = parser.parse_args()
    return parsed

def parse_shared_configuration(parsed: Any):
    """Generates a dictionary of configuration options for running jobs against hither, regardless of back-end.

    Args:
        parsed (Any): parsed ArgParse parser, with at least the keys defined in add_standard_args.

    Raises:
        Exception: Fatal error if attempting to use an existing file as an output.

    Returns:
        StandardArgs: A dictionary of compiled run values, to be passed to future calls from this file.
    """    

    # example srun_command: srun --exclusive -n 1 -p <partition>
    slurm_command = f"srun -n 1 -p {parsed.slurm_partition} {'--exclusive' if not parsed.slurm_accept_shared_nodes else ''}"
    if parsed.slurm_gpus_per_node > 0:
        slurm_command += f" --gpus-per-node={parsed.slurm_gpus_per_node}"
    if parsed.outfile is not None and parsed.outfile != '' and os.path.exists(parsed.outfile) and parsed.outfile != "/dev/null":
        raise Exception('Error: Requested to write to an existing output file. Aborting to avoid overwriting file.')
    # configure verbosity for the run
    print_per_verbose.__dict__['verbosity_level'] = parsed.verbose or 0

    # We would very much like to avoid this manual copying, unfortunately the argsparse module and the typing module
    # don't play at all nicely with each other. Maybe fix this later (keyword TAP/typed arg parser)
    return StandardArgs(
        test                          = parsed.test,
        timeout_min                   = parsed.timeout_min,
        outfile                       = parsed.outfile,
        workercount                   = max(parsed.workercount, 1),
        # As a reminder, argparse converts internal -es to _s to keep the identifiers valid
        job_cache                     = None if parsed.no_job_cache else parsed.job_cache,
        use_container                 = parsed.use_container or \
                                            ((not parsed.no_container) \
                                             and os.getenv('HITHER_USE_CONTAINER') in ['TRUE', '1']),
        use_slurm                     = parsed.use_slurm,
        slurm_max_jobs_per_alloc      = parsed.slurm_jobs_per_allocation,
        slurm_max_simultaneous_allocs = parsed.slurm_max_simultaneous_allocations,
        slurm_command                 = slurm_command
    )

# TODO: print_per_verbose, _fmt_time belong in a different file?
def print_per_verbose(lvl: int, msg: str):
    # verbosity_level is a static value, initialized from command-line argument at setup time in init_configuration().
    # This does not play nicely with containerization, but global arguments variables don't either; rather than passing
    # needless verbosity parameters around, we're just going to stay silent if the verbosity_level property isn't set.
    if ('verbosity_level' not in print_per_verbose.__dict__): return
    if (print_per_verbose.verbosity_level < lvl): return
    tabs = max(0, lvl - 1)
    print("\t" * tabs + msg)

def _fmt_time(t: Union[float, None]):
    if not t: return 'TIME NOT SPECIFIED'
    return datetime.datetime.fromtimestamp(t).isoformat()

def extract_hither_config(args: StandardArgs) -> HitherConfiguration:
    use_container = args['use_container']
    if args['test'] != 0: print(f"\tRunning in TEST MODE--Execution will stop after processing {args['test']} sortings!\n")

    if use_container:
        print_per_verbose(1, f"Using {'Singularity' if os.getenv('HITHER_USE_SINGULARITY') else 'Docker'} containers.")
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
    log = hi.Log()
    timeout_sec = None if args['timeout_min'] == 0 else 60 * args['timeout_min']
    return HitherConfiguration(
        job_cache=jc,
        job_handler=jh,
        use_container=use_container,
        job_timeout_sec=timeout_sec,
        show_console=True,
        log=log
    )
    
def call_cleanup(config: HitherConfiguration) -> None:
    if config['job_handler'] is not None:
        config['job_handler'].cleanup()
