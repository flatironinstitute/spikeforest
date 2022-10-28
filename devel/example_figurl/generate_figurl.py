from typing import List
from example_box_layout import example_box_layout
import spikeforest as sf
import spikeinterface as si
import sortingview.views as vv


def main():
    R = sf.load_spikeforest_recording(study_name='paired_boyden32c', recording_name='1103_1_1')
    label = f'{R.study_set_name}/{R.study_name}/{R.recording_name}'
    print(label)
    print(f'Num. channels: {R.num_channels}')
    print(f'Duration (sec): {R.duration_sec}')
    print(f'Sampling frequency (Hz): {R.sampling_frequency}')
    print(f'Num. true units: {R.num_true_units}')
    print('')

    recording = R.get_recording_extractor()
    sorting_true = R.get_sorting_true_extractor()

    print(f'Recording extractor info: {recording.get_num_channels()} channels, {recording.get_sampling_frequency()} Hz, {recording.get_total_duration()} sec')
    print(f'Sorting extractor info: unit ids = {sorting_true.get_unit_ids()}, {sorting_true.get_sampling_frequency()} Hz')
    print('')
    for unit_id in sorting_true.get_unit_ids():
        st = sorting_true.get_unit_spike_train(unit_id=unit_id)
        print(f'Unit {unit_id}: {len(st)} events')
    print('')
    print('Channel locations:')
    print('X:', recording.get_channel_locations()[:, 0].T)
    print('Y:', recording.get_channel_locations()[:, 1].T)

    v = example_box_layout(recording=recording, sorting=sorting_true)
    url = v.url(label=f'{label}')
    print(url)

if __name__ == '__main__':
    main()