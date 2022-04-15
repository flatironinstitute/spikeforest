import kachery_cloud as kcl
from .SFRecording import SFRecording


default_uri = 'ipfs://bafkreiantrq7v7tboepsqlvvzqytmvfqe5nrlsyy2g2ztf6xubqlxtz7ae?spikeforest-recordings.json'

def load_spikeforest_recordings(uri: str=default_uri):
    x = kcl.load_json(uri)
    recording_records = x['recordings']
    return [
        SFRecording(rec)
        for rec in recording_records
    ]