from tabnanny import verbose
import spikeforest as sf
import spikeinterface as si
import spikeinterface.sorters as ss


# For this example you will need to install mountainsort4: pip install mountainsort4
# See also this example notebook: https://spikeinterface.readthedocs.io/en/latest/modules/sorters/plot_1_sorters_example.html#sphx-glr-modules-sorters-plot-1-sorters-example-py

def main():
    R = sf.load_spikeforest_recording(study_name='paired_boyden32c', recording_name='1103_1_1')
    print(f'{R.study_set_name}/{R.study_name}/{R.recording_name}')
    print(f'Num. channels: {R.num_channels}')
    print(f'Duration (sec): {R.duration_sec}')
    print(f'Sampling frequency (Hz): {R.sampling_frequency}')
    print('')

    recording = R.get_recording_extractor()

    sorter_params = {
        'detect_sign': -1,
        'adjacency_radius': 25,
        'freq_min': 300,  # Use None for no bandpass filtering
        'freq_max': 6000,
        'filter': False,
        'whiten': True,  # Whether to do channel whitening as part of preprocessing
        'num_workers': 4,
        'clip_size': 50,
        'detect_threshold': 3,
        'detect_interval': 10
    }
    sorting: si.BaseSorting = ss.run_mountainsort4(
        recording,
        verbose=True,
        **sorter_params
    )

    print(f'Sorting extractor info: unit ids = {sorting.get_unit_ids()}, {sorting.get_sampling_frequency()} Hz')
    print('')
    for unit_id in sorting.get_unit_ids():
        st = sorting.get_unit_spike_train(unit_id=unit_id)
        print(f'Unit {unit_id}: {len(st)} events')
    print('')
    


if __name__ == '__main__':
    main()