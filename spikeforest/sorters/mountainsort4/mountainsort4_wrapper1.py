import os
import time
import hither2 as hi
import kachery_client as kc

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
    'mountainsort4_wrapper1', '0.1.0',
    image=hi.DockerImageFromScript(name='magland/mountainsort4', dockerfile=f'{thisdir}/docker/Dockerfile'),
    modules=['labbox_ephys', 'labbox', 'spikeforest'],
    kachery_support=True,
    runtime_hooks=[num_workers_hook()]
)
def mountainsort4_wrapper1(
    recording_object: dict,
    detect_sign=-1,
    adjacency_radius=50,
    clip_size=50,
    detect_threshold=3,
    detect_interval=10,
    freq_min=300,
    freq_max=6000,
    whiten=True,
    filter=True
) -> dict:
    # test import
    import mountainsort4 as ms4

    import sortingview as sv
    import spiketoolkit as st

    recording = sv.LabboxEphysRecordingExtractor(recording_object)
    
    # Sorting
    print('Sorting...')
    with kc.TemporaryDirectory(prefix='tmp_mountainsort4') as tmpdir:
        num_workers = 1

        # preprocessing
        if filter:
            recording = st.preprocessing.bandpass_filter(
                recording=recording,
                freq_min=freq_min,
                freq_max=freq_max,
                chunk_size=int(recording.get_sampling_frequency() * 30),
                cache_chunks=False
            )
        if whiten:
            recording = st.preprocessing.whiten(
                recording=recording,
                chunk_size=int(recording.get_sampling_frequency() * 30),
                cache_chunks=False,
                seed=1
            )
        
        timer = time.time()
        sorting = ms4.mountainsort4(
            recording=recording,
            detect_sign=detect_sign,
            adjacency_radius=adjacency_radius,
            clip_size=clip_size,
            detect_threshold=detect_threshold,
            detect_interval=detect_interval,
            num_workers=num_workers,
            verbose=True
        ) 
        elapsed = time.time() - timer
        print('#SF-SORTER-RUNTIME#{:.3f}#'.format(timer))

        return sv.LabboxEphysSortingExtractor.store_sorting(sorting=sorting)
