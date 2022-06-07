import json
import spikeforest as sf


def main():
    franklab_manual_uri = 'ipfs://QmYo54whckFsVxtc1Hv48aKzXyggmK25MBhXb4VpJDVrWz?spikeforest-recordings.json'

    # the default URI includes the PAIRED_BOYDEN, PAIRED_CRCNS_HC1,
    # PAIRED_ENGLISH, PAIRED_KAMPFF, and PAIRED_MEA64C_YGER recordings.
    all_recordings = sf.load_spikeforest_recordings()

    # Other recording sets are being migrated to the new data distribution protocol as needed.
    # To load the Franklab-Manual data set, use the following:
    # all_recordings = sf.load_spikeforest_recordings(franklab_manual_uri)

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