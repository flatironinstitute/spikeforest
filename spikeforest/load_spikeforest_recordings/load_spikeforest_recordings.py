import kachery_cloud as kcl
from .SFRecording import SFRecording

# prepared via: https://github.com/scratchrealm/prepare-spikeforest-ipfs
default_uri = 'ipfs://bafkreiharnfwm5ntcui4rsex4zkvxfjbytodkserudpvfsnsx5us7tciuq?spikeforest-recordings.json'

def load_spikeforest_recordings(uri: str=default_uri):
    x = kcl.load_json(uri)
    recording_records = x['recordings']
    return [
        SFRecording(rec)
        for rec in recording_records
    ]