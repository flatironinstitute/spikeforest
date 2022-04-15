import kachery_cloud as kcl
from .SFSortingOutput import SFSortingOutput

# prepared via: https://github.com/scratchrealm/prepare-spikeforest-ipfs
default_uri = 'ipfs://bafkreiaeqg3vtca6c6j2xbsbppcnfrkm2w46jgc3bfbny6as6mxiy3jine?spikeforest-sorting-outputs.json'

def load_spikeforest_sorting_outputs(uri: str=default_uri):
    x = kcl.load_json(uri)
    sorting_output_records = x['sortingOutputs']
    return [
        SFSortingOutput(rec)
        for rec in sorting_output_records
    ]