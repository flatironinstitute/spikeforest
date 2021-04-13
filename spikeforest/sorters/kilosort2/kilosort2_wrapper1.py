import os
from typing import Dict, List
import hither2 as hi
import kachery_p2p as kp

expected_kilosort2_commit = '1a030bf8ca460899dfc0294005f2f971cf63c9e7'

def get_image(**kwargs):
    thisdir = os.path.dirname(os.path.realpath(__file__))

    # Matlab license stuff ##########################
    bind_mounts: List[hi.BindMount] = []
    environment: Dict[str, str] = {}
    hither_matlab_lnu_credentials_path = os.getenv('HITHER_MATLAB_LNU_CREDENTIALS_PATH', None)
    hither_matlab_mlm_license_file = os.getenv('HITHER_MATLAB_MLM_LICENSE_FILE', None)
    if hither_matlab_lnu_credentials_path:
        if not os.path.isdir(hither_matlab_lnu_credentials_path):
            raise Exception(f'No such directory: {hither_matlab_lnu_credentials_path}')
        bind_mounts.append(hi.BindMount(source=hither_matlab_lnu_credentials_path, target='/root/.matlab/MathWorks/MATLAB/LNUCredentials', read_only=True))
    elif hither_matlab_mlm_license_file:
        environment['MLM_LICENSE_FILE'] = hither_matlab_mlm_license_file
    else:
        raise Exception('No matlab license specified. Set one of the following environment variables: HITHER_MATLAB_MLM_LICENSE_FILE or HITHER_MATLAB_LNU_CREDENTIALS_PATH.')
    #################################################
    
    return hi.DockerImageFromScript(
        name='magland/kilosort2',
        dockerfile=f'{thisdir}/docker/Dockerfile',
        bind_mounts=bind_mounts,
        environment=environment
    )

@hi.function(
    'kilosort2_wrapper1', '0.1.0',
    image=get_image,
    modules=['labbox_ephys', 'labbox'],
    kachery_support=True
)
def kilosort2_wrapper1(
    recording_object: dict,
) -> dict:
    import labbox_ephys as le
    import spikesorters as ss

    with kp.TemporaryDirectory(prefix='tmp_kilosort2') as tmpdir:
        ######################################################################################################################################################
        # Make sure kilosort is installed, compiled and at the right commit
        if os.getenv('HITHER_IN_CONTAINER') == '1':
                kp.ShellScript(f'''
                cd {tmpdir}/Kilosort2/CUDA
                mexGPUall
                ''').write(f'{tmpdir}/compile_ks.m')

                compile_script = kp.ShellScript(f'''
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
                os.environ['KILOSORT2_PATH'] = f'{tmpdir}/Kilosort2'
        kilosort2_path = os.getenv('KILOSORT2_PATH', None)
        if not kilosort2_path:
            raise Exception(f'Environment variable not set: KILOSORT2_PATH')
        if not os.path.isdir(kilosort2_path):
            raise Exception(f'Not a directory: {kilosort2_path}')

        mex_paths = [f'{kilosort2_path}/CUDA/{fname}' for fname in ['mexClustering2.mexa64', 'mexDistances2.mexa64', 'mexFilterPCs.mexa64', 'mexGetSpikes2.mexa64', 'mexMPnu8.mexa64']] # sampling of some of the files
        for mex_path in mex_paths:
            if not os.path.isfile(mex_path):
                raise Exception(f'Kilosort2 not compiled. File not found: {mex_path}')
        scr = kp.ShellScript(f'''
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

        recording = le.LabboxEphysRecordingExtractor(recording_object)
        
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

        return le.LabboxEphysSortingExtractor.store_sorting(sorting=sorting)
