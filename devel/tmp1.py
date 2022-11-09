import kachery_cloud as kcl

x = kcl.load_json('ipfs://bafybeibiqb7znwr7vaidri2dicqtfx6zd7u3szj6swg3iuhrozzvxtqd7u?studysets.json')

studyset = [s for s in x['StudySets'] if s['name'] == 'SYNTH_MONOTRODE'][0]

studies = studyset['studies']
for s in studies:
    print('STUDY:', s['name'])
    for r in s['recordings']:
        print(r['name'])