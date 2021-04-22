import os
import hither2 as hi
import kachery_p2p as kp

thisdir = os.path.dirname(os.path.realpath(__file__))

@hi.function(
    'spykingcircus_wrapper1', '0.1.2',
    image=hi.DockerImageFromScript(name='magland/spyking-circus', dockerfile=f'{thisdir}/docker/Dockerfile'),
    modules=['labbox_ephys', 'labbox', 'spikeforest'],
    kachery_support=True
)
def spykingcircus_wrapper1(
    recording_object: dict,
    detect_sign=-1,
    adjacency_radius=100,
    detect_threshold=6,
    template_width_ms=3,
    filter=True,
    merge_spikes=True,
    auto_merge=0.75,
    whitening_max_elts=1000,
    clustering_max_elts=10000
) -> dict:
    import labbox_ephys as le
    import spikesorters as ss
    from datetime import datetime

    recording = le.LabboxEphysRecordingExtractor(recording_object)
    
    # Sorting
    DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'
    print('BEGINNING SpyKingCircus sort: ' + datetime.now().strftime(DATE_FORMAT))
    with kp.TemporaryDirectory(prefix='tmp_spykingcircus') as tmpdir:
        sorter = ss.SpykingcircusSorter(
            recording=recording,
            output_folder=f'{tmpdir}/working',
            delete_output_folder=True
        )

        num_workers = 1

        sorter.set_params(
            detect_sign=detect_sign,
            adjacency_radius=adjacency_radius,
            detect_threshold=detect_threshold,
            template_width_ms=template_width_ms,
            filter=filter,
            merge_spikes=merge_spikes,
            auto_merge=auto_merge,
            num_workers=num_workers,
            whitening_max_elts=whitening_max_elts,
            clustering_max_elts=clustering_max_elts
        )     
        timer = sorter.run()
        print('#SF-SORTER-RUNTIME#{:.3f}#'.format(timer))
        sorting = sorter.get_result()
        print('COMPLETED SpyKingCircus sort: ' + datetime.now().strftime(DATE_FORMAT))

        return le.LabboxEphysSortingExtractor.store_sorting(sorting=sorting)
