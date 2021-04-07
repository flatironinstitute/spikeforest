#!/usr/bin/env python3

import spikeforest as sf
from test_sorting import test_sorting

def main():
    test_sorting(sf.mountainsort4_wrapper1)

if __name__ == '__main__':
    main()