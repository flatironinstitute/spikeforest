#!/usr/bin/env python

# pip install --upgrade kachery

import json
import argparse
import numpy as np
import kachery_cloud as ka
import os
import spikeforest as sf
from spikeforest.load_extractors.MdaRecordingExtractorV2.MdaRecordingExtractorV2 import readmda

def main():
    """
    This function reads all the recordings from spikeforest recording dataset.
    creates a directory tree that stores the data by study set name -> study name.
    it downloads each datasets parameters (fire rate, sample rate etc), and than each recording raw data.

    kachery_cloud downloads all the raw data to .kachery-cloud directory in your home directory.

    so we the download and copying of the data to the script generated directory tree, it deletes it from the .kachery-cloud,
    inorder to avoid duplication for files across your file system
    """
    parser = argparse.ArgumentParser(
        description="down load all the raw data recordings from spikeforest datasets")
    parser.add_argument('--output_dir', help='The output directory (e.g., recordings)')
    # parser.add_argument('--verbose', action='store_true', help='Turn on verbose output')

    args = parser.parse_args()
    output_dir = args.output_dir
    all_recordings = sf.load_spikeforest_recordings()

    basedir = output_dir
    if not os.path.exists(basedir):
        os.mkdir(basedir)
    studySets = []
    raw_data_paths = []
    for R in all_recordings:
        studyset_name = R.study_set_name
        studysetdir_local = os.path.join(basedir, studyset_name)
        if not os.path.exists(studysetdir_local):
            os.mkdir(studysetdir_local)
        study_name = R.study_name
        print('STUDY: {}/{}'.format(studyset_name, study_name))
        studydir_local = os.path.join(studysetdir_local, study_name)
        if not os.path.exists(studydir_local):
            os.mkdir(studydir_local)
        recname = R.recording_name
        recfile = os.path.join(studydir_local, recname + '.json')
        obj = _json_serialize(R.recording_object)
        obj['self_reference'] = ka.store_json(obj,
                                              label='{}/{}/{}.json'.format(studyset_name, study_name,
                                                                           recname))
        with open(recfile, 'w') as f:
            json.dump(obj, f, indent=4)
        firings_true_file = os.path.join(studydir_local, recname + '.firings_true.json')
        obj2 = R.sorting_true_object
        obj2['self_reference'] = ka.store_json(obj2, label='{}/{}/{}.firings_true.json'.format(studyset_name,
                                                                                               study_name,
                                                                                               recname))
        with open(firings_true_file, 'w') as f:
            json.dump(obj2, f, indent=4)
        study = {}
        study['self_reference'] = ka.store_json(study, label='{}.json'.format(study_name))
        with open(os.path.join(studydir_local, study_name + '.json'), 'w') as f:
            json.dump(study, f, indent=4)
        studyset = {}
        studyset['self_reference'] = ka.store_json(studyset, label='{}.json'.format(studyset_name))
        with open(os.path.join(studysetdir_local, studyset_name + '.json'), 'w') as f:
            json.dump(studyset, f, indent=4)
        print('getting raw data for {}/{}'.format(studyset_name, study_name))
        rec = R.get_recording_extractor()
        readmda(rec._kwargs['raw_path']).tofile(os.path.join(studydir_local, recname + '.dat'))
        raw_data_paths.append(rec._kwargs['raw_path'])
        studySets.append(studyset)
    studysets_obj = dict(
        StudySets=studySets
    )
    studysets_path = ka.store_json(studysets_obj, label='studysets.json')
    with open(os.path.join(basedir, 'studysets'), 'w') as f:
        f.write(studysets_path)
    for p in raw_data_paths:
        os.remove(p)

# def patch_recording_geom(recording, geom_fname):
#     print(f'PATCHING geom for recording: {recording["name"]}')
#     geom_info = ka.get_file_info(geom_fname)
#     x = recording['directory']
#     y = ka.store_dir(x).replace('sha1dir://', 'sha1://')
#     obj = ka.load_object(y)
#     obj['files']['geom.csv'] = dict(
#         size=geom_info['size'],
#         sha1=geom_info['sha1']
#     )
#     x2 = ka.store_object(obj)
#     recording['directory'] = 'sha1dir://' + ka.get_file_hash(x2) + '.patched'


def _listify_ndarray(x):
    if x.ndim == 1:
        if np.issubdtype(x.dtype, np.integer):
            return [int(val) for val in x]
        else:
            return [float(val) for val in x]
    elif x.ndim == 2:
        ret = []
        for j in range(x.shape[1]):
            ret.append(_listify_ndarray(x[:, j]))
        return ret
    elif x.ndim == 3:
        ret = []
        for j in range(x.shape[2]):
            ret.append(_listify_ndarray(x[:, :, j]))
        return ret
    elif x.ndim == 4:
        ret = []
        for j in range(x.shape[3]):
            ret.append(_listify_ndarray(x[:, :, :, j]))
        return ret
    else:
        raise Exception('Cannot listify ndarray with {} dims.'.format(x.ndim))


def _json_serialize(x):
    if isinstance(x, np.ndarray):
        return _listify_ndarray(x)
    elif isinstance(x, np.integer):
        return int(x)
    elif isinstance(x, np.floating):
        return float(x)
    elif type(x) == dict:
        ret = dict()
        for key, val in x.items():
            ret[key] = _json_serialize(val)
        return ret
    elif type(x) == list:
        ret = []
        for i, val in enumerate(x):
            ret.append(_json_serialize(val))
        return ret
    else:
        return x


if __name__ == '__main__':
    main()
