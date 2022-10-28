import kachery_cloud as kc
import kachery_cloud as kcl
import spikeinterface.extractors as sie


def load_sorting_extractor(sorting_object: dict):
    if 'firings' in sorting_object:
        return load_sorting_extractor(dict(
            sorting_format='mda',
            data=dict(
                firings=sorting_object['firings'],
                samplerate=sorting_object.get('samplerate', None)
            )
        ))
    sorting_format = sorting_object['sorting_format']
    data = sorting_object['data']
    if sorting_format == 'mda':
        firings_uri = data['firings']
        if firings_uri.startswith('ipfs://'):
            firings_path = kcl.load_file(firings_uri, verbose=True)
        else:
            firings_path = kc.load_file(firings_uri)
        samplerate = data.get('samplerate', None)
        if samplerate is None:
            raise Exception('samplerate is None')
        assert firings_path is not None, f'Unable to load firings file: {firings_uri}'
        return sie.MdaSortingExtractor(firings_path, samplerate)
    else:
        raise Exception(f'Unexpected sorting format: {sorting_format}')