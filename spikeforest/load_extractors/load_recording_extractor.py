import kachery_cloud as kc
import kachery_cloud as kcl
from .MdaRecordingExtractorV2.MdaRecordingExtractorV2 import MdaRecordingExtractorV2


def load_recording_extractor(recording_object: dict):
    if 'raw' in recording_object:
        return load_recording_extractor(dict(
            recording_format='mda',
            data=dict(
                raw=recording_object['raw'],
                geom=recording_object['geom'],
                params=recording_object['params']
            )
        ))
    recording_format = recording_object['recording_format']
    data = recording_object['data']
    if recording_format == 'mda':
        raw_uri = data['raw']
        if raw_uri.startswith('ipfs://'):
            raw_path = kcl.load_file(raw_uri, verbose=True)
        else:
            raw_path = kc.load_file(raw_uri)
        geom = data.get('geom', None)
        params = data.get('params', None)
        assert raw_path is not None, f'Unable to load raw file: {raw_uri}'
        return MdaRecordingExtractorV2(raw_path=raw_path, params=params, geom=geom)
    else:
        raise Exception(f'Unexpected recording format: {recording_format}')