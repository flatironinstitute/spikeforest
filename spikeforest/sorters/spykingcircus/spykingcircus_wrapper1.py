import os
import hither2 as hi
import kachery_cloud as kc

thisdir = os.path.dirname(os.path.realpath(__file__))

class num_workers_hook(hi.RuntimeHook):
    def precontainer(self, context: hi.PreContainerContext):
        # context.kwargs can also be used to pull in variable values
        # setting environment variables to ensure we are using only one thread
        context.set_env('NUM_WORKERS', '1')
        context.set_env('MKL_NUM_THREADS', '1')
        context.set_env('NUMEXPR_NUM_THREADS', '1')
        context.set_env('OMP_NUM_THREADS', '1')

@hi.function(
    'spykingcircus_wrapper1', '0.1.4',
    image=hi.DockerImageFromScript(name='magland/spyking-circus', dockerfile=f'{thisdir}/docker/Dockerfile'),
    modules=['sortingview', 'spikeforest'],
    kachery_support=True,
    runtime_hooks=[num_workers_hook()]
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
    import sortingview as sv
    import spikesorters as ss

    recording = sv.LabboxEphysRecordingExtractor(recording_object)
    
    # Sorting
    with kc.TemporaryDirectory(prefix='tmp_spykingcircus') as tmpdir:
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

        return sv.LabboxEphysSortingExtractor.store_sorting(sorting=sorting).object()
