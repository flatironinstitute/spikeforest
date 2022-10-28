import kachery_cloud as kcl
# import sortingview as sv
# from spikeinterface.core.old_api_utils import OldToNewRecording
# from spikeinterface.toolkit.preprocessing import bandpass_filter
# from nwb_conversion_tools.utils.spike_interface import write_recording
import yaml


def main():
    x = kcl.load_json('ipfs://bafybeibiqb7znwr7vaidri2dicqtfx6zd7u3szj6swg3iuhrozzvxtqd7u?studysets.json')
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    print(config)
    recording_records = []
    for study in config['studies']:
        study_set_name = study['study_set_name']
        study_name = study['study_name']
        for recording_name in study['recording_names']:
            print(recording_name)
            k = f'spikeforest-{study_name}-{recording_name}-recording'
            print(k)
            recording_rec_uri = kcl.get_mutable_local(k)
            if recording_rec_uri is not None:
                try:
                    recording_rec = kcl.load_json(recording_rec_uri)
                except:
                    print(f'Problem downloading recording record: {recording_rec_uri}')
                    recording_rec = None
            else:
                recording_rec = None
            if recording_rec is None:
                recording_rec = _find_recording(x, study_set_name, study_name, recording_name)
                print(recording_rec)

                sorting_true_uri = recording_rec['sortingTrueUri']
                sorting_true_obj = kcl.load_json(sorting_true_uri)
                firings_uri = sorting_true_obj['firings']
                firings_true_local_path = kcl.load_file(firings_uri)
                print(f'Storing firings_true.mda for {study_name}/{recording_name}')
                sorting_true_obj['firings'] = kcl.store_file(firings_true_local_path,  label='firings_true.mda')
                sorting_true_obj['samplerate'] = recording_rec['sampleRateHz']
                recording_rec['sortingTrueObject'] = sorting_true_obj

                recording_uri = recording_rec['recordingUri']
                recording_obj = kcl.load_json(recording_uri)
                raw_uri = recording_obj['raw']
                raw_local_path = kcl.load_file(raw_uri)
                print(f'Storing raw.mda for {study_name}/{recording_name}')
                recording_obj['raw'] = kcl.store_file(raw_local_path, label='raw.mda')
                recording_rec['recordingObject'] = recording_obj

                kcl.set_mutable_local(k, kcl.store_json(recording_rec))
            recording_records.append(recording_rec)
    spikeforest_recordings_uri = kcl.store_json({'recordings': recording_records}) + '?spikeforest-recordings.json'
    # kcl.set_mutable_local('spikeforest-recordings', spikeforest_recordings_uri)
    print(spikeforest_recordings_uri)

            
# def _create_recording_nwb(recording_uri):
#     with kc.TemporaryDirectory() as tmpdir:
#         recording_nwb_path = f'{tmpdir}/recording.nwb'

#         print('Loading recording...')
#         recording_object = kc.load_json(recording_uri)
#         assert recording_object is not None, f'Unable to load recording: {recording_uri}'
#         recording = sv.LabboxEphysRecordingExtractor(recording_object)
#         recording = OldToNewRecording(recording)
#         recording.clear_channel_groups()

#         recording = bandpass_filter(recording=recording, freq_min=300., freq_max=6000., margin_ms=5.0, dtype='float32')

#         print('Writing recording nwb...')
#         write_recording(recording, save_path=recording_nwb_path, compression=None, compression_opts=None)
#         print('Storing recording nwb...')
#         recording_nwb_uri = kcl.store_file(recording_nwb_path)
#         return recording_nwb_uri

def _find_recording(x: dict, study_set_name: str, study_name: str, recording_name: str):
    study_set = [b for b in x['StudySets'] if b['name'] == study_set_name][0]
    study = [b for b in study_set['studies'] if b['name'] == study_name][0]
    recording = [b for b in study['recordings'] if b['name'] == recording_name][0]
    return recording
    

if __name__ == '__main__':
    main()