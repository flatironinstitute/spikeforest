import os
from typing import Dict, List
import hither2 as hi
import kachery_p2p as kp
from ..kilosort2.kilosort2_wrapper1 import matlab_license_hook

expected_kilosort3_commit = 'a1fccd9abf13ce5dc3340fae8050f9b1d0f8ab7a'
    
thisdir = os.path.dirname(os.path.realpath(__file__))
image = hi.DockerImageFromScript(
    name='magland/kilosort3',
    dockerfile=f'{thisdir}/docker/Dockerfile'
)

@hi.function(
    'kilosort3_wrapper1', '0.1.1',
    image=image,
    modules=['labbox_ephys', 'labbox'],
    kachery_support=True,
    nvidia_support=True,
    runtime_hooks=[matlab_license_hook()]
)
def kilosort3_wrapper1(
    recording_object: dict,
) -> dict:
    import labbox_ephys as le

    with kp.TemporaryDirectory(prefix='tmp_kilosort3') as tmpdir:
        ######################################################################################################################################################
        # Make sure kilosort is installed, compiled and at the right commit
        if os.getenv('HITHER_IN_CONTAINER') == '1':
            kp.ShellScript(f'''
            cd {tmpdir}/Kilosort3/CUDA
            mexGPUall
            ''').write(f'{tmpdir}/compile_ks.m')

            compile_script = kp.ShellScript(f'''
            #!/bin/bash
            set -e

            # copy the source code over to the working directory so we don't have permissions issues during compilation
            cp -r /src/Kilosort3 {tmpdir}/

            cd {tmpdir}
            matlab -batch compile_ks
            ''')
            compile_script.start()
            retval = compile_script.wait()
            assert (retval == 0)
            kilosort3_path = f'{tmpdir}/Kilosort3'
            os.environ['KILOSORT3_PATH'] = kilosort3_path
        else:
            kilosort3_path = os.getenv('KILOSORT3_PATH', None)
            if not kilosort3_path:
                raise Exception(f'Environment variable not set: KILOSORT3_PATH')
        if not os.path.isdir(kilosort3_path):
            raise Exception(f'Not a directory: {kilosort3_path}')
            
        # important to import this after KILOSORT3_PATH is set
        import spikesorters as ss

        mex_paths = [f'{kilosort3_path}/CUDA/{fname}' for fname in ['mexClustering2.mexa64', 'mexDistances2.mexa64', 'mexFilterPCs.mexa64', 'mexGetSpikes2.mexa64']] # sampling of some of the files
        for mex_path in mex_paths:
            if not os.path.isfile(mex_path):
                raise Exception(f'Kilosort3 not compiled. File not found: {mex_path}')
        scr = kp.ShellScript(f'''
        #!/bin/bash
        set -e
        cd {kilosort3_path}
        if [ `git rev-parse HEAD` == "{expected_kilosort3_commit}" ]; then
            # at the expected commit
            exit 0
        fi
        exit 1
        ''')
        scr.start()
        if scr.wait() != 0:
            raise Exception(f'Git repo not at the expected commit: {expected_kilosort3_commit}')
        ######################################################################################################################################################

        recording = le.LabboxEphysRecordingExtractor(recording_object)
    
    # Sorting
        print('Sorting...')
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
