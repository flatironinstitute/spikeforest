import kachery_p2p as kp
import pandas as pd
import labbox_ephys as le
import spikeextractors as se

def main():
    # Load the index of SpikeForest sorting outputs into a pandas dataframe
    x = kp.load_object('sha1://52f24579bb2af1557ce360ed5ccc68e480928285/file.txt?manifest=5bfb2b44045ac3e9bd2a8fe54ef67aa932844f58')
    df = pd.DataFrame(x)
    print(x[0].keys())

    # Print the dataframe
    print('***************************************************************')
    print(df)
    print('***************************************************************')

    # Inspect the first 10 results
    for index in range(10):
        study_name = df['studyName'][index]
        recording_name = df['recordingName'][index]
        sorter_name = df['sorterName'][index]
        firings_uri = df['firings'][index]
        sorting_object = {
            'sorting_format': 'mda',
            'data': {
                'firings': firings_uri,
                'samplerate': 30000
            }
        }
        sorting = le.LabboxEphysSortingExtractor(sorting_object)
        print(f'=========================================================')
        print(f'{study_name}/{recording_name} {sorter_name}')
        print(f'Num. units: {len(sorting.get_unit_ids())}')

if __name__ == '__main__':
    main()