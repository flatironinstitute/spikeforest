import os
from typing import Any, List
import kachery_cloud as kc
import sortingview as sv

# This script should run on a computer that has access to all the spikeforest v1 data in kachery (e.g., FI workstation)

# What it does:
# Creates one sortingview workspace per study and prints out the corresponding figURLs
# It uses a caching mechanism to retrieve already created workspaces

def main():
    # Check environment variables
    if not os.getenv('FIGURL_CHANNEL'):
        raise Exception(f'Environment variable not set: FIGURL_CHANNEL')

    # Load list of all spikeforest (v1) sorting outputs (aka sortings)
    uri = 'sha1://52f24579bb2af1557ce360ed5ccc68e480928285/file.txt?manifest=5bfb2b44045ac3e9bd2a8fe54ef67aa932844f58'
    X = kc.load_json(uri)

    # Get the list of study names
    study_names = unique_list([a['studyName'] for a in X])

    # exclude some studies
    study_names = [sn for sn in study_names if 'neurocube' not in sn]
    # For testing: limit to only a few studies
    # study_names = study_names[:2]
    # study_names = ['paired_kampff']
    

    all_figurls = []

    for study_name in study_names:
        print(f'STUDY: {study_name}')

        # Load all the records associated with this study
        X_study = [a for a in X if a['studyName'] == study_name]
        # Get the list of recordings (note that there are multiple records per recording)
        recording_names = unique_list([a['recordingName'] for a in X_study])
        # limit for now
        recording_names = recording_names[:3]

        for recording_name in recording_names[:3]:
            label = study_name + '/' + recording_name
            print(f'RECORDING: {study_name}/{recording_name}')
            # Get all records for the recording
            X_recording = [a for a in X_study if a['recordingName'] == recording_name]
        
            # Lookup this workspace (if found, we don't want to re-create)
            workspace_key={'type': 'spikeforest-workspace', 'version': 3, 'studyName': study_name, 'recordingName': recording_name, 'label': label}
            workspace_uri = kc.get(workspace_key)
            if workspace_uri is not None:
                # The workspace was created previously
                W = sv.load_workspace(workspace_uri)
            else:
                # The workspace needs to be created
                # Create the new workspace
                W = sv.create_workspace(label=label)
                # The first record is all we need to determine recordingUri and sortingTrueUri (same for every record associated with the recording)
                x = X_recording[0]
                recording_uri = x['recordingUri']
                sorting_true_uri = x['sortingTrueUri']

                # Load the recording/sortingTrue extractors
                try:
                    recording = sv.LabboxEphysRecordingExtractor(recording_uri)
                    sorting_true = sv.LabboxEphysSortingExtractor(sorting_true_uri)
                    ok = True
                except Exception as e:
                    print('Problem loading recording', str(e))
                    ok = False

                if ok:
                    # Add recording and true sorting to the workspace
                    rid = W.add_recording(label=recording_name, recording=recording)
                    W.add_sorting(recording_id=rid, label='true', sorting=sorting_true)

                    # Finally add each of the sortings
                    for a in X_recording:
                        if 'firings' in a: # if the sorting crashed, firings will not be a field in the record
                            try:
                                S = sv.LabboxEphysSortingExtractor({
                                    'sorting_format': 'mda',
                                    'data': {
                                        'firings': a['firings'],
                                        'samplerate': 30000 # hard-coded for now
                                    }
                                })
                                W.add_sorting(recording_id=rid, label=a['sorterName'], sorting=S)
                            except Exception as e2:
                                print('Problem adding sorting', e2)
                # Save this workspace for future lookup
                kc.set(workspace_key, W.uri)
            # Get the figURL and print
            F = W.figurl()
            url = F.url(label=W.label)
            all_figurls.append({'label': W.label, 'url': url})
            print(f'Workspace {W.label}: {url}')
    print('##############################################################')
    for r in all_figurls:
        print(f"{r['label']}: {r['url']}")

def unique_list(a: List[str]):
    return sorted(list(set(a)))

if __name__ == '__main__':
    main()