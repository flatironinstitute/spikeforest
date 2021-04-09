import os
import hither2 as hi
import kachery_p2p as kp

thisdir = os.path.dirname(os.path.realpath(__file__))

@hi.function(
    'kilosort3_wrapper1', '0.1.0',
    # image=hi.DockerImageFromScript(name='magland/kilosort3', dockerfile=f'{thisdir}/docker/Dockerfile'),
    modules=['labbox_ephys', 'labbox'],
    kachery_support=True
)
def kilosort3_wrapper1(
    recording_object: dict,
) -> dict:
    import labbox_ephys as le
    import spikesorters as ss

    recording = le.LabboxEphysRecordingExtractor(recording_object)
    
    # Sorting
    print('Sorting...')
    with kp.TemporaryDirectory(prefix='tmp_kilosort3') as tmpdir:
        sorter = ss.Kilosort3Sorter(
            recording=recording,
            output_folder=f'{tmpdir}/working',
            delete_output_folder=True
        )

        sorter.set_params(
        )     
        timer = sorter.run()
        print('#SF-SORTER-RUNTIME#{:.3f}#'.format(timer))
        sorting = sorter.get_result()

        return le.LabboxEphysSortingExtractor.store_sorting(sorting=sorting)
