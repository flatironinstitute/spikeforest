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

    console_out = X.get_console_out()

    print(console_out)


if __name__ == '__main__':
    main()