from typing import Any
import kachery_cloud as kcl


spikeforest_recordings_uri = 'ipfs://bafkreiharnfwm5ntcui4rsex4zkvxfjbytodkserudpvfsnsx5us7tciuq?spikeforest-recordings.json'

def main():
    x = kcl.load_json(spikeforest_recordings_uri)
    y = _migrate_recursive(x)

def _migrate_recursive(x: Any):
    if isinstance(x, dict):
        ret = {}
        for k, v in x.items():
            if k == 'studyName':
                print(f'Study: {v}')
            if isinstance(v, str):
                if v.startswith('ipfs://') or v.startswith('sha1://'):
                    if k == 'sortingTrueUri' or k == 'raw' or k == 'firings' or k == 'recordingUri':
                        label = _get_label_from_uri(v)
                        if label is None:
                            raise Exception(f'Label is None for {v}')
                        print(f'Loading {v}')
                        pp = kcl.load_file(v)
                        if pp is None:
                            raise Exception(f'Unable to load: {v}')
                        print(f'Storing {pp} {label}')
                        kcl.store_file(pp, label=label)
                    else:
                        print('=============================', k)
                ret[k] = v
            else:
                ret[k] = _migrate_recursive(v)
        return ret
    elif isinstance(x, list):
        return [_migrate_recursive(a) for a in x]
    elif isinstance(x, str):
        if v.startswith('ipfs://') or v.startswith('sha1://'):
            raise Exception('Unexpected.')
        return x
    else:
        return x

def _get_label_from_uri(uri: str):
    a = uri.split('?')
    if len(a) > 1:
        qq = a[1]
        bb = qq.split('&')
        for cc in bb:
            if cc.split('=')[0] == 'label':
                return cc.split('=')[1]
        if ('&' not in qq) and ('=' not in qq):
            return qq
    else:
        bb = uri.split('/')
        if len(bb) >= 4:
            return bb[-1]
    return None

if __name__ == '__main__':
    main()