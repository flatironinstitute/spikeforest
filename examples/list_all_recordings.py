import json
import spikeforest as sf


def main():
    hybrid_janelia_uri = 'sha1://43298d72b2d0860ae45fc9b0864137a976cb76e8?hybrid-janelia-spikeforest-recordings.json'
    synth_monotrode_uri = 'sha1://3b265eced5640c146d24a3d39719409cceccc45b?synth-monotrode-spikeforest-recordings.json'
    paired_boyden_uri = 'sha1://849e53560c9241c1206a82cfb8718880fc1c6038?paired-boyden-spikeforest-recordings.json'
    paired_kampff_uri = 'sha1://b8b571d001f9a531040e79165e8f492d758ec5e0?paired-kampff-spikeforest-recordings.json'
    paired_english_uri = 'sha1://dfb1fd134bfc209ece21fd5f8eefa992f49e8962?paired-english-spikeforest-recordings.json'

    # the default URI includes the PAIRED_BOYDEN, PAIRED_CRCNS_HC1,
    # PAIRED_ENGLISH, PAIRED_KAMPFF, and PAIRED_MEA64C_YGER recordings.
    all_recordings = sf.load_spikeforest_recordings()

    # Other recording sets are being migrated to the new data distribution protocol as needed.
    # E.G. to load the Hybrid Janelia data set, use the following:
    # all_recordings = sf.load_spikeforest_recordings(hybrid_janelia_uri)

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
