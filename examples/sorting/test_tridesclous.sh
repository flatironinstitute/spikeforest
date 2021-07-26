#!/bin/bash

# uncomment this if you want to keep all temporary files for debugging purposes
# export KACHERY_KEEP_TEMP_FILES=1

# Use singularity rather than docker
export HITHER_USE_SINGULARITY=1

./test_tridesclous.py