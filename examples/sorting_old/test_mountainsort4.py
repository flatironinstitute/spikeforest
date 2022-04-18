#!/usr/bin/env python3

import spikeforest as sf
import hither2 as hi
from test_sorting import test_sorting

def main():
    pjh = hi.ParallelJobHandler(num_workers=4)
    test_sorting(sf.mountainsort4_wrapper1, show_console=False, job_handler=pjh)

if __name__ == '__main__':
    main()