import os
from typing import Dict, List
import hither2 as hi
import kachery_client as kc
from spikeforest.sorters._matlab_license_hook import matlab_license_hook

expected_kilosort2_commit = '1a030bf8ca460899dfc0294005f2f971cf63c9e7'
        
thisdir = os.path.dirname(os.path.realpath(__file__))
image = hi.DockerImageFromScript(
    name='magland/kilosort2',
    dockerfile=f'{thisdir}/docker/Dockerfile'
)

@hi.function(
    'kilosort2_wrapper1', '0.1.1',
    image=image,
    modules=['labbox_ephys', 'labbox', 'spikeforest'],
    kachery_support=True,
    nvidia_support=True,
    runtime_hooks=[matlab_license_hook()]
)
def kilosort2_wrapper1(
    recording_object: dict,
) -> dict:
    import sortingview as sv

    with kc.TemporaryDirectory(prefix='tmp_kilosort2') as tmpdir:
        ######################################################################################################################################################
        # Make sure kilosort is installed, compiled and at the right commit
        if os.getenv('HITHER_IN_CONTAINER') == '1':
            kc.ShellScript(f'''
            cd {tmpdir}/Kilosort2/CUDA
            mexGPUall
            ''').write(f'{tmpdir}/compile_ks.m')

            compile_script = kc.ShellScript(f'''
            #!/bin/bash
            set -e

            # copy the source code over to the working directory so we don't have permissions issues during compilation
            cp -r /src/Kilosort2 {tmpdir}/

            cd {tmpdir}
            matlab -batch compile_ks
            ''')
            compile_script.start()
            retval = compile_script.wait()
            assert (retval == 0)
            kilosort2_path = f'{tmpdir}/Kilosort2'
            os.environ['KILOSORT2_PATH'] = kilosort2_path
        else:
            kilosort2_path = os.getenv('KILOSORT2_PATH', None)
            if not kilosort2_path:
                raise Exception(f'Environment variable not set: KILOSORT2_PATH')
        if not os.path.isdir(kilosort2_path):
            raise Exception(f'Not a directory: {kilosort2_path}')

        # important to import this after KILOSORT2_PATH is set
        import spikesorters as ss

        mex_paths = [f'{kilosort2_path}/CUDA/{fname}' for fname in ['mexClustering2.mexa64', 'mexDistances2.mexa64', 'mexFilterPCs.mexa64', 'mexGetSpikes2.mexa64', 'mexMPnu8.mexa64']] # sampling of some of the files
        for mex_path in mex_paths:
            if not os.path.isfile(mex_path):
                raise Exception(f'Kilosort2 not compiled. File not found: {mex_path}')
        scr = kc.ShellScript(f'''
        #!/bin/bash
        set -e
        cd {kilosort2_path}
        if [ `git rev-parse HEAD` == "{expected_kilosort2_commit}" ]; then
            # at the expected commit
            exit 0
        fi
        exit 1
        ''')
        scr.start()
        if scr.wait() != 0:
            raise Exception(f'Git repo not at the expected commit: {expected_kilosort2_commit}')
        ######################################################################################################################################################

        recording = sv.LabboxEphysRecordingExtractor(recording_object)
        
        # Sorting
        print('Sorting...')
        sorter = ss.Kilosort2Sorter(
            recording=recording,
            output_folder=f'{tmpdir}/working',
            delete_output_folder=True
        )

        sorter.set_params(
        )     
        timer = sorter.run()
        print('#SF-SORTER-RUNTIME#{:.3f}#'.format(timer))
        sorting = sorter.get_result()

        return sv.LabboxEphysSortingExtractor.store_sorting(sorting=sorting)
