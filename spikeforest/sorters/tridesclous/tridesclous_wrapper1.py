import os
import hither2 as hi
import kachery_client as kc

thisdir = os.path.dirname(os.path.realpath(__file__))

@hi.function(
    'tridesclous_wrapper1', '0.1.0',
    image=hi.DockerImageFromScript(name='magland/tridesclous', dockerfile=f'{thisdir}/docker/Dockerfile'),
    modules=['sortingview', 'spikeforest'],
    kachery_support=True
)
def tridesclous_wrapper1(
    recording_object: dict,
) -> dict:
    # test importing tridesclous here - easier to troubleshoot if there are errors
    import tridesclous

    import sortingview as sv
    import spikesorters as ss
    # test importing tridesclous (best to get exceptions here)

    recording = sv.LabboxEphysRecordingExtractor(recording_object)
    
    # Sorting
    print('Sorting...')
    with kc.TemporaryDirectory(prefix='tmp_tridesclous') as tmpdir:
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

        return sv.LabboxEphysSortingExtractor.store_sorting(sorting=sorting).object()
