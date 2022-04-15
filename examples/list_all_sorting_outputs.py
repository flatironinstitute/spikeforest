import json
import spikeforest as sf


def main():
    all_sorting_outputs = sf.load_spikeforest_sorting_outputs()

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