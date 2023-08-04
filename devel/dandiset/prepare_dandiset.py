import os
import spikeforest as sf
from StudyInfo import StudyInfo
from spikeforest.load_spikeforest_recordings.SFRecording import SFRecording
from RecordingInfo import RecordingInfo
from pynwb.file import Subject
from datetime import datetime
from dateutil.tz import tzlocal
from _prepare_recording import _prepare_recording


def main():
    # create a directory for the dandiset
    root_folder = 'spikeforest_dandiset'
    os.makedirs(root_folder, exist_ok=True)

    overwrite = True

    paired_boyden_uri = 'sha1://849e53560c9241c1206a82cfb8718880fc1c6038?paired-boyden-spikeforest-recordings.json'
    paired_kampff_uri = 'sha1://b8b571d001f9a531040e79165e8f492d758ec5e0?paired-kampff-spikeforest-recordings.json'
    paired_english_uri = 'sha1://dfb1fd134bfc209ece21fd5f8eefa992f49e8962?paired-english-spikeforest-recordings.json'

    uri_list = [
        paired_boyden_uri,
        paired_kampff_uri,
        paired_english_uri
    ]

    for uri in uri_list:
        recordings = sf.load_spikeforest_recordings(uri=uri)
        study_info = _get_study_info(study_set_name=recordings[0].study_set_name)

        for R in recordings:
            recording_info = _get_recording_info(R)

            recording_folder = f'{root_folder}/{R.study_set_name}/{R.study_name}'
            os.makedirs(recording_folder, exist_ok=True)
            nwb_fname = f'{recording_folder}/{R.recording_name}.nwb'
            _prepare_recording(R, nwb_fname=nwb_fname, study_info=study_info, recording_info=recording_info, overwrite=overwrite)

def _get_study_info(study_set_name: str):
    if study_set_name == 'PAIRED_KAMPFF':
        study_info = StudyInfo(
            experimenter=['Marques-Smith, André', 'Neto, Joana P.', 'Lopes, Gonçalo', 'Nogueira, Joana', 'Calcaterra, Lorenza', 'Frazão, João', 'Kim, Danbee', 'Phillips, Matthew G.', 'Dimitriadis, George', 'Kampff, Adam R.'],
            experiment_description='Paired juxtacellular and silicon probe recording',
            lab='Kampff Lab',
            institution='Champalimaud Centre for the Unknown',
            keywords=['extracellular action potential', 'spike sorting', 'ground truth', 'juxtacellular recording', 'polytrodes'],
            subject=Subject( # tutorial didn't include this
                subject_id='paired_kampff',
                age='P0Y',
                date_of_birth=datetime(1970, 1, 1, tzinfo=tzlocal()),
                sex='U',
                species='Rattus norvegicus',
                description='Long-Evans strain rat'
            )
        )
    elif study_set_name == 'PAIRED_BOYDEN':
        study_info = StudyInfo(
            experimenter=['Allen, Brian D.', 'Moore-Kochlacs, Caroline', 'Gold Bernstein, Jacob', 'Kinney, Justin', 'Scholvin, Jorg', 'Seoane, Luis', 'Chronopoulos, Chris', 'Lamantia, Charlie', 'Kodandaramaiah, Suhasa B', 'Tegmark, Max', 'Boyden, Edward S.'],
            experiment_description='Automated in vivo patch clamp evaluation of extracellular multielectrode array spike recording capability',
            lab='Boyden Lab',
            institution='Massachusetts Institute of Technology',
            keywords=['action potential', 'bursting', 'multielectrode array', 'patch clamp', 'spike sorting'],
            subject=Subject(
                subject_id='paired_boyden',
                age='P0Y',
                date_of_birth=datetime(1970, 1, 1, tzinfo=tzlocal()),
                sex='U',
                species='Mus musculus',
                description='Anesthetized mouse'
            )
        )
    elif study_set_name == 'PAIRED_ENGLISH':
        paired_english_experiment_description = """# Silicon-juxtacellular hybrid probes
This studyset consists of 29 paired recordings from Silicon-juxtacellular hybrid probes. Juxtacellular electrodes are pulled from 1 mm OD 0.7 mm ID borosilicate glass and have impedances of 8-10 MOhm when filled with 130 mM potassium acetate. These juxtacellular electrodes are glued to 32 channel silicon probes (A1-32-Poly3, Neuronexus) using light-cure dental acrylic. Using the inter-site spacing of the silicon probe as a visual distance guide, the tip of the juxtacellular is fixed at a distance of ~20 micrometers from the nearest silicon probe recording site. The closest site is selected as a site in the middle (top to bottom) of an outer column of recording sites. The close distance between the juxtacellular tip and the recording sites results in both devices recording the same neuron at high probability. 

#  Recording ground truth data in awake behaving mice
Mice are placed in the head-fixed treadmill apparatus and the protective silicon elastomer is removed from the craniotomy, the juxtacellular-silicon hybrid prove is inserted 0.1 mm into the brain, and the craniotomy is covered with silicon fluid to prevent drying and improve stability. The probe is advanced into the brain at ~1-2 micrometers until action potentials are observed on the juxtacellular electrode, at which point movement is ceased and data collection begins.  Electrical signals from the juxtacellular electrode are recorded and amplified through an analog microelectrode amplifier (Cygnus IR-183), then digitized via an Intan RHD2000 system. Signals from the silicon probe are amplified and digitized through the same RHD2000 system, which results in hardware synchronization of the two signals. By converting the digital signals in the RHD2000 to analog voltage and outputting them to a digital microprocessor (CED Power1401), we calculated online the juxtacellular spike triggered average of each channel of the extracellular electrode, and discard recordings in which the triggered average does not contain a spike waveform on any channel.
"""
        study_info = StudyInfo(
            experimenter=['English, D. F.'],
            experiment_description=paired_english_experiment_description,
            lab='English Lab',
            institution='Virginia Tech',
            keywords=['silicon probe', 'juxtacellular', 'ground truth'],
            subject=Subject(
                subject_id='paired_english',
                age='P0Y',
                date_of_birth=datetime(1970, 1, 1, tzinfo=tzlocal()),
                sex='U',
                species='Mus musculus',
                description='Awake behaving mouse'
            )
        )
    else:
        raise Exception(f'Unexpected study set name: {study_set_name}')
    return study_info

def _get_recording_info(R: SFRecording):
    if R.study_set_name == 'PAIRED_KAMPFF':
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
    elif R.study_set_name == 'PAIRED_BOYDEN':
        recording_info = RecordingInfo(
            device_name='Neuronexus polytrode',
            device_description='Neuronexus polytrode (32 channels)'
        )
    elif R.study_set_name == 'PAIRED_ENGLISH':
        recording_info = RecordingInfo(
            device_name='Neuronexus',
            device_description='Neuronexus silicon probe'
        )
    else:
        raise Exception(f'Unexpected study set name: {R.study_set_name}')
    return recording_info

if __name__ == "__main__":
    main()