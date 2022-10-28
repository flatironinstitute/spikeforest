import kachery_cloud as kcl
from .SFRecording import SFRecording

# prepared using: https://github.com/scratchrealm/prepare-spikeforest-ipfs
# default_uri = 'ipfs://bafkreiharnfwm5ntcui4rsex4zkvxfjbytodkserudpvfsnsx5us7tciuq?spikeforest-recordings.json'

# prepared using: devel/migrate_script1
default_uri = 'sha1://1d343ed7e876ffd73bd8e0daf3b8a2c4265b783c?spikeforest-recordings.json'

def load_spikeforest_recordings(uri: str=default_uri):
    x = kcl.load_json(uri)
    recording_records = x['recordings']
    return [
        SFRecording(rec)
        for rec in recording_records
    ]