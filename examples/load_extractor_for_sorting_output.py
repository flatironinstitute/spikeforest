import json
import spikeforest as sf


def main():
    X = sf.load_spikeforest_sorting_output(study_name='paired_boyden32c', recording_name='1103_1_1', sorter_name='SpykingCircus')
    print('=========================================================')
    print(f'{X.study_name}/{X.recording_name}/{X.sorter_name}')
    print(f'CPU time (sec): {X.cpu_time_sec}')
    print(f'Return code: {X.return_code}')
    print(f'Timed out: {X.timed_out}')
    print(f'Sorting true object: {json.dumps(X.sorting_object)}')
    print('')

    sorting = X.get_sorting_extractor()

    print(f'Sorting extractor info: unit ids = {sorting.get_unit_ids()}, {sorting.get_sampling_frequency()} Hz')
    print('')
    for unit_id in sorting.get_unit_ids():
        st = sorting.get_unit_spike_train(unit_id=unit_id)
        print(f'Unit {unit_id}: {len(st)} events')
    print('')


if __name__ == '__main__':
    main()