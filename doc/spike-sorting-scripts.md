# Scripts to run spike sorting in an automated fashion

To encourage reproducibility in producing sorting results, SpikeForest offers two
pipelines for running sorters against the recording set and making the results
visible in a Labbox workspace. These can be run from command line and will
store sorting results to a configured kachery instance, as well as posting
the recordings, known ground-truth, and sorting results to a workspace,
either in a two-step process or as part of an integrated one-step pipeline.

The three relevant scripts are `run_sortings.py`, `prepare_workspace.py`, and
`sort_sf_recordings.py`, all located in the `spikeforest/spikeforest/sorting_utilities`
directory. (TODO: ADD LINK AFTER MERGE)

Either pipeline requires a `json` file that offers a manifest of recordings
(such as `studysets.json` available from the
[spikeforest_recordings](https://github.com/flatironinstitute/spikeforest_recordings/blob/master/recordings/studysets)
repository), and a configuration `yaml` file, which indicates the known
study sets that should appear in the manifest, and describes which
sorters will be run against which study set recordings. An example
configuration file can be viewed at (TKTK).

These files will be checked for mutual compatibility. Both formats are
described below with examples.

## Step-by-Step Process

The two-step process is most appropriate when you want exact control over
the parameters for individual sorting-recording combinations. It operates
in two stages: one stage runs sorting on recordings and produces an
output `json` file with all produced sortings and their metadata. The
second stage parses the output sortings file and loads the results into
a labbox Workspace, which can then be viewed through standard labbox tools. (LINK HERE)

### run_sortings.py

The `run_sortings.py` (INCLUDE LINK AFTER MERGE) command requires a study source file
(in `.json` format, passed using the command flags `--study-source-file` or `-s`) and
a sorter specification file (in `.yaml` format, passed using `--sorter-spec-file` or `-l`).
It can additionally accept the [shared configuration flags described below](#shared-command-line-configuration-for-containerization).

This script builds a matrix of all recordings referenced in the study sets, against all
sorters applied to those study sets. It then creates a hither sorting job for each,
using the wrapper functions defined for each containerized sorter (found in the
[spikeforest/spikeforest/sorters](https://github.com/flatironinstitute/spikeforest/tree/main/spikeforest/sorters)
directory). Based on the shared configuration, the hither sorting jobs can run on cluster
or local environments, with or without containerization, as per the command-line
arguments defined from `calling_framework.py`.

Once all sorting jobs are complete, `run_sortings.py` outputs results in `.json` format
as already used in SpikeForest, to a file specified by the `-o` command-line flag.

The format in question writes a list of sorting instances, where each sorting instance
is expected to have the following keys:

* `recordingName`: the label applied to the individual recording within the study set.
* `studyName`: the name of the study set to which the recording belongs.
* `sorterName`: the name of the sorter which produced this sorting.
* `sortingParameters`: parameters applied to the sorter (currently blank for all sorters).
* `consoleOutUri`: if requested, this is a `.json` file stored in kachery which records
all console output from the sorter during its run.
* `cpuTimeSec`: total elapsed time for sorting this recording. While these should be generally
accurate, we do not claim to run sorters with optimal efficiency settings and may inadvertently
include overhead steps that are not directly related to sorting in this time record. Rigorous
comparsion of sorter processing speeds would require further experimentation.
* `errored`: whether the sorting job failed.
* `startTime`: the time when the sorting job was created.
* `endTime`: the time when the sorting job reported completion.
* `sortingOutput`: an object recording the `sorting_format` (usually `h5_v1`) and the
`data` (usually an `h5_path` to a kachery object). This value can be passed as input
to create a `LabboxEphysSortingExtractor`.
* `recordingUri`: the kachery uri of the recording file.
* `groundTruthUri`: the kachery uri of the ground truth sorting.

### prepare_workspace.py

This script consumes the output file produced by `run_sortings.py` and loads the
resulting sortings into a workspace, skipping any whose standardized names
are already present. Either a valid workspace URI must be provided (using the
`--workspace-uri` flag), or a new one can be created (if the `--create-new-workspace` flag
is set). Passing both or neither will result in an ambiguous situation and an error.

The script also features a convenient `--dry-run` flag that communicates what it would
do, but does not actually take any action. This is useful to verify what recordings and
sortings are already present in the workspace (or that the workspace exists).

Note that `prepare_workspace.py` filters out duplicate sortings based on the standard
label ONLY. If a particular data element exists but needs to be overwritten with a
new copy, it *must be manually deleted from the workspace*.

The pattern for standard recording/sorting names is as follows:

* A recording will be labeled as `STUDY_NAME/RECORDING_NAME`, where `STUDY_NAME` is the
name of the individual study (not the overall study set!) and `RECORDING_NAME` is the
name of the recording within the study.
* A ground-truth sorting will be labeled as `Ground-Truth/STUDY_NAME/RECORDING_NAME`.
* A non-ground-truth sorting will be labeled as `SORTER_NAME/STUDY_NAME/RECORDING_NAME`,
where `SORTER_NAME` is the standardized name of the sorter used in the `spec.yaml` and
the sorter definitions in `run_sortings.py`.

This naming scheme is intended to provide a unique and consistent label for each
recording and sorting across the SpikeForest ecosystem, which allows the scripts
to avoid repeatedly loading the same file into the same workspace. Additionally,
as a convenience, the ground truth sortings appear alphabetically before
the output of any sorter that is currently part of SpikeForest.

## Integrated Process

Stepwise processing provides more control and more of a paper trail when running sortings.
However, manual tracking of files and running of multiple steps is inconvenient.

An integrated pipeline offers convenience, as well as two practical advantages. The
`run_sortings.py` and `prepare_workspaces.py` scripts are intentionally loosely coupled;
combining them allows us to omit re-running any sortings whose results would not be
loaded into the workspace. Additionally, the integrated pipeline allows us to load
results as they become available, instead of requiring all sorting to be complete first.

To ensure consistency, `sort_sf_recordings.py` uses the other two scripts as libraries,
so that nearly all of the shared functionality is achieved by using the same code.

### sort_sf_recordings.py

The parameters for `sort_sf_recordings.py` include both those from `run_sortings.py`
and the workspace management parameters from `prepare_workspace.py`. Note, again,
that existing data is identified only by name, not by contents; if you wish to
replace an existing recording or sorting, you must delete it from the workspace
manually before running the script.

## Shared command-line configuration for containerization

The following arguments are shared across all sorting-processing modules. Note that
all are available, however since `prepare_workspace.py` does not use hither or
write output files, those options have no particular effect.

General options:

* `--verbose` or `-v`: sets verbosity level. More 'v's means more verbosity.
* `--timeout-min` or `-T`: sets a maximum duration for any hither job before it
is cancelled. (Used only by `run_sortings.py`)
* `--outfile` or -`o`: the name of the file to write output to (used only by
`run_sortings.py`). If the file already exists, it will not be overwritten, and
processing will instead abort.
* `--check-config`: A debugging tool. If set, the program should display
final configuration on the command line, then quit.

hither job control:

* `--job-cache`: identifies the name of the job cache for any hither jobs (e.g.
spike-sorting jobs). See hither documentation for more information.
* `--no-job-cache`: if set, no job cache will be used; all processing will be
carried out from scratch.
* `--use-container` or `-C`: if passed, hither calls will use containerization.
This is not the default, but is probably what you want. Note that if this is not
set, containerization may still be used if the `HITHER_USE_CONTAINER` environment
variable is set to 1 or TRUE.
* `--no-container`: If set, no container will be used unless the `--use-container`
variable is explicitly set.
* `--workercount` or `-w`: identifies the maximum number of worker threads for a
parallel job handler (when running hither jobs against a non-cluster resource).
Has no effect when using slurm.

The following options are relevant for slurm and chiefly serve to configure the
`SlurmJobHandler` (see hither documentation for more details). Briefly, a
`SlurmJobHandler` creates a number of `ParallelJobHandler`s on cluster resources,
one per node, each with a defined-length job queue. The overall hither job manager
will feed new processing work into each cluster processor as it becomes available.

* `--use-slurm`: If set, the script will use a SlurmJobHandler instead of a
ParallelJobHandler and will attempt to run jobs on the configured cluster. The below
options can further customize the calls made to slurm (and will have no effect if
the `--use-slurm` flag is unset):
* `--slurm-partition`: the text name of the cluster partition name to request. This
value will be passed directly to the `-p` flag of `srun`.
* `--slurm-accept-shared-nodes`: If unset (the default), slurm `srun` calls will
be made with the `--exclusive` flag.
* `--slurm-jobs-per-allocation`: sets the maximum number of jobs to be queued/processed
simultaneously by each cluster job processor. Default 6.
* `--slurm-max-simultaneous-allocations`: sets the number of cluster job processors
to be created (i.e. the number of nodes to request). Default 5.
* `--slurm-gpus-per-node`: If set, the `srun` command that creates each job handler
will include a `--gpus-per-node` flag with this value. If not set, the job processors
will be created without reference to whether the nodes have GPUs.

## Configuration Files Format

The following are the expected file structures for the inputs to the sorting process.

### spec.yaml

An example is available in [small-spec.yaml](../examples/small-spec.yaml).

This file consists of three sections:

1. The key `studysets` indicates the kachery URI of a `studysets.json` file. This file
will be used if the `--study-source-file` command-line option is not passed.

2. The key `studyset-names` declares the names of the study sets that may be referenced
in the spec file. During parsing, the study sets requested by individual sorters are
compared to this list, which is also cross-referenced against the study sets provided
by the `studysets.json` file. An error will be raised if any declared study sets in
the spec file are not present in the `studysets.json` data source, or if any sorter
requests a study that does not appear in the manifest.

3. The key `spike-sorters` introduces a list of elements, each of which has three
keys. The `name` key identifies the sorter (and should match, case-sensitively,
with the `KNOWN_SORTERS` declared in `run_sortings.py`). The `params` key is arbitrary
data which can be passed to an individual sorter (not presently used).
The `studysets` key introduces a list of study sets which the sorter will process.

To prevent the sorter from processing a particular study set (e.g., to avoid processing
tetrode recordings with sorters that do not support them), simply omit the corresponding
study set from the list.

### studysets.json

This file identifies study sets, the largest groupings of recordings in the SpikeForest
ecosystem. Conceptually, a study set is a collection of one or more studies (usually contributed
by the same contributor and collected with similar parameters), along with some overall
description. Each study may consist of one or more recordings; exact internal structure
is at the contributor's discretion.

A full example of the `studysets.json` format can be found linked from the `spikeforest_recordings`
repository: just load [the studysets.json url](https://github.com/flatironinstitute/spikeforest_recordings/blob/master/recordings/studysets)
in kachery.

At the top level, the `studysets.json` format declares a single object with a single key,
`StudySets`, which points to a list of study set objects.

Each study set object is of the following form:

* `name` key identifies the name of the study set (in all caps).
* `info` key contains metadata about the set, organism being recorded, source of ground truth,
any publication data, etc.
* `description` is a human-readable description of the data, in Markdown format.
* `studies` is a list of studies, described below.
* `self_reference` is a kachery URI which can be used to recover the JSON for the individual
study set.

Each study object has the following form:

* `name` key identifies the name of the individual study.
* `studySetName` key repeats the parent's `name` key (name of overall study set in majuscule).
* `recordings` is a list of recording files making up the study.
* `self_reference` is, again, a kachery uri which can be used to recover the individual study json.

Each recording has the following form:

* `name` identifies the individual recording and should be unique within the study (although ideally
the name scheme will be more unique than this).
* `studyName` gives the value of the parent's `name` key.
* `studySetName` gives the value of the grandparent's `name` key (the study set name in majuscule).
* `sampleRateHz` is the number of frames recorded per second.
* `numChannels` is the number of channels in the recording.
* `durationSec` is the overall recording length in seconds.
* `numTrueUnits` is the unit count from the ground truth sorting.
* `spikeSign` is the overall polarity of the ground-truth recording.
* `recordingUri` is the kachery URI of the recording (and may be fed directly to a
`LabboxEphysRecordingExtractor` constructor).
* `sortingTrueUri` is the kachery URI of a JSON record for the ground-truth sorting. This may
be fed directly to a `LabboxEphysSortingExtractor`.
