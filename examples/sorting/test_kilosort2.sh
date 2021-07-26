#!/bin/bash

# uncomment this if you want to keep all temporary files for debugging purposes
# export KACHERY_KEEP_TEMP_FILES=1

# Use singularity rather than docker
export HITHER_USE_SINGULARITY=1

# Use a matlab license server
export HITHER_MATLAB_MLM_LICENSE_FILE=$MLM_LICENSE_FILE

./test_kilosort2.py