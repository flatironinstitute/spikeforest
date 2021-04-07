import os
import hither2 as hi
import kachery_p2p as kp

thisdir = os.path.dirname(os.path.realpath(__file__))

@hi.function(
    'tridesclous_wrapper1', '0.1.0',
    image=hi.DockerImageFromScript(name='magland/tridesclous', dockerfile=f'{thisdir}/docker/Dockerfile'),
    modules=['labbox_ephys', 'labbox'],
    kachery_support=True
)
def tridesclous_wrapper1(
    recording_object: dict,
) -> dict:
    # # do this before importing spikesorters so that importing tridesclous doesn't fail
    # import matplotlib
    # matplotlib.use('agg')
    # from matplotlib import pyplot

    # test importing tridesclous here - easier to troubleshoot if there are errors
    import tridesclous

    import labbox_ephys as le
    import spikesorters as ss
    # test importing tridesclous (best to get exceptions here)

    recording = le.LabboxEphysRecordingExtractor(recording_object)
    
    # Sorting
    print('Sorting...')
    with kp.TemporaryDirectory(prefix='tmp_tridesclous') as tmpdir:
        sorter = ss.TridesclousSorter(
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
