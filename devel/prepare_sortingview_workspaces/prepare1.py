import sortingview as sv
from sfsortingresults import SFSortingResults

def main():
    SF = SFSortingResults()

    study_name = 'synth_magland_noise10_K10_C4'
    recording_name = '001_synth'
    print('=========================================================')
    print(f'{study_name}/{recording_name}')

    recording = SF.get_gt_recording(study_name, recording_name)
    sorting_true = SF.get_gt_sorting_output(study_name, recording_name)
    sortings = {}
    for sorter_name in SF.get_sorting_output_names(study_name, recording_name):
        sortings[sorter_name] = SF.get_sorting_output(study_name, recording_name, sorter_name)

    W = sv.create_workspace()
    rid = W.add_recording(label=f'{study_name}/{recording_name}', recording=recording)
    W.add_sorting(recording_id=rid, label='true', sorting=sorting_true)
    for k, v in sortings.items():
        W.add_sorting(recording_id=rid, label=k, sorting=sortings[k])
    
    F = W.figurl()
    url = F.url(label=f'{study_name}/{recording_name}')
    print(url)

# Then refresh the page on the web app

if __name__ == "__main__":
    main()