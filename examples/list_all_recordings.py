import json
import spikeforest as sf


def main():
    all_recordings = sf.load_spikeforest_recordings()

    for R in all_recordings:
        print('=========================================================')
        print(f'{R.study_set_name}/{R.study_name}/{R.recording_name}')
        print(f'Num. channels: {R.num_channels}')
        print(f'Duration (sec): {R.duration_sec}')
        print(f'Sampling frequency (Hz): {R.sampling_frequency}')
        print(f'Num. true units: {R.num_true_units}')
        print(f'Sorting true object: {json.dumps(R.sorting_true_object)}')
        print('')

if __name__ == '__main__':
    main()