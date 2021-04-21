import os
import hither2 as hi

class matlab_license_hook(hi.RuntimeHook):
    def precontainer(self, context: hi.PreContainerContext):
        # Matlab license stuff ##########################
        hither_matlab_lnu_credentials_path = os.getenv('HITHER_MATLAB_LNU_CREDENTIALS_PATH', None)
        hither_matlab_mlm_license_file = os.getenv('HITHER_MATLAB_MLM_LICENSE_FILE', None)
        if hither_matlab_lnu_credentials_path:
            if not os.path.isdir(hither_matlab_lnu_credentials_path):
                raise Exception(f'No such directory: {hither_matlab_lnu_credentials_path}')
            context.add_bind_mount(hi.BindMount(source=hither_matlab_lnu_credentials_path, target='/root/.matlab/MathWorks/MATLAB/LNUCredentials', read_only=True))
        elif hither_matlab_mlm_license_file:
            context.set_env('MLM_LICENSE_FILE', hither_matlab_mlm_license_file)
        else:
            raise Exception('No matlab license specified. Set one of the following environment variables: HITHER_MATLAB_MLM_LICENSE_FILE or HITHER_MATLAB_LNU_CREDENTIALS_PATH.')
        #################################################