import os
import spikeforest as sf
from StudyInfo import StudyInfo
from RecordingInfo import RecordingInfo
from _prepare_recording import _prepare_recording


def main():
    # create a directory for the dandiset
    root_folder = 'spikeforest_dandiset'
    os.makedirs(root_folder, exist_ok=True)

    paired_kampff_uri = 'sha1://b8b571d001f9a531040e79165e8f492d758ec5e0?paired-kampff-spikeforest-recordings.json'
    recordings = sf.load_spikeforest_recordings(uri=paired_kampff_uri)

    study_info = StudyInfo(
        experimenter=['Neto, Joana P.', 'Lopes, Gonçalo', 'Frazão, João', 'Nogueira, Joana', 'Lacerda, Pedro', 'Baião, Pedro', 'Aarts, Arno', 'Andrei, Alexandru', 'Musa, Silke', 'Fortunato, Elvira', 'Barquinha, Pedro', 'Kampff, Adam R.'],
        experiment_description='Paired juxtacellular and silicon probe recording',
        lab='Kampff Lab',
        institution='Champalimaud Centre for the Unknown'
    )

    for R in recordings:
        if R.recording_name == '2014_11_25_Pair_3_0':
            recording_info = RecordingInfo(
                device_name='Neuronexus poly32nn',
                device_description='Neuronexus poly32nn (25 um spacing, staggered three columns)'
            )
        elif R.recording_name == '2015_09_03_Pair_9_0A':
            recording_info = RecordingInfo(
                device_name='IMEC Neuroseeker probe',
                device_description='IMEC Neuroseeker probe (four columns, 20 um spacing). Subsampled half the electrodes (staggered four columns, neuropixels probe layout)'
            )
        elif R.recording_name == '2015_09_03_Pair_9_0B':
            recording_info = RecordingInfo(
                device_name='IMEC Neuroseeker probe',
                device_description='IMEC Neuroseeker probe, subsampled the other half of the electrodes'
            )
        elif R.recording_name.startswith('c'):
            recording_info = RecordingInfo(
                device_name='Neuropixels probe',
                device_description='Neuropixels probe (four columns staggered, 20 um vertical spacing, 28 um horizontal spacing). 12 cell pairs available.'
            )
        else:
            raise Exception(f'Unexpected recording name: {R.recording_name}')

        recording_folder = f'{root_folder}/{R.study_set_name}/{R.study_name}'
        os.makedirs(recording_folder, exist_ok=True)
        nwb_fname = f'{recording_folder}/{R.recording_name}.nwb'
        _prepare_recording(R, nwb_fname=nwb_fname, study_info=study_info, recording_info=recording_info, overwrite=True)

if __name__ == "__main__":
    main()