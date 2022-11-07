import json
import spikeforest as sf


def main():
    hybrid_janelia_uri = 'sha1://9259d3ec1d981560e35c2ca41e59c39f2af3d37e?label=spikeforest-sorting-outputs.json'

    # the default URI includes the PAIRED_BOYDEN, PAIRED_CRCNS_HC1,
    # PAIRED_ENGLISH, PAIRED_KAMPFF, and PAIRED_MEA64C_YGER recordings.
    all_sorting_outputs = sf.load_spikeforest_sorting_outputs()

    # Other recording sets are being migrated to the new data distribution protocol as needed.
    # E.G. to load the Hybrid Janelia data set, use the following:
    # all_sorting_outputs = sf.load_spikeforest_sorting_outputs(hybrid_janelia_uri)


    for X in all_sorting_outputs:
        print('=========================================================')
        print(f'{X.study_name}/{X.recording_name}/{X.sorter_name}')
        print(f'CPU time (sec): {X.cpu_time_sec}')
        print(f'Return code: {X.return_code}')
        print(f'Timed out: {X.timed_out}')
        print(f'Sorting true object: {json.dumps(X.sorting_object)}')
        print('')

if __name__ == '__main__':
    main()