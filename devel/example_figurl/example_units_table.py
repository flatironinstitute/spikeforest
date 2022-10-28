# 8/31/22
# https://figurl.org/f?v=gs://figurl/spikesortingview-8&d=sha1://3bd6d3c6b77428cca467bc1afb48c5f272d7b4e6&label=Units%20table%20example

from typing import List
import sortingview.views as vv
import spikeinterface as si
import spikeinterface.extractors as se
import kachery_cloud as kcl


def main():
    kcl.use_sandbox()
    recording, sorting = se.toy_example(num_units=12, duration=300, seed=0, num_segments=1)

    view = example_units_table(recording=recording, sorting=sorting)

    url = view.url(label='Units table example')
    print(url)

def example_units_table(*, recording: si.BaseRecording, sorting: si.BaseSorting, height=600):
    columns: List[vv.UnitsTableColumn] = [
        vv.UnitsTableColumn(
            key='unitId',
            label='Unit',
            dtype='int'
        ),
        vv.UnitsTableColumn(
            key='numEvents',
            label='Num. events',
            dtype='int'
        ),
        vv.UnitsTableColumn(
            key='firingRateHz',
            label='Firing rate (Hz)',
            dtype='float'
        )
    ]
    rows: List[vv.UnitsTableRow] = []
    for unit_id in sorting.get_unit_ids():
        spike_train = sorting.get_unit_spike_train(unit_id=unit_id)
        rows.append(
            vv.UnitsTableRow(
                unit_id=unit_id,
                values={
                    'unitId': unit_id,
                    'numEvents': len(spike_train),
                    'firingRateHz': len(spike_train) / (recording.get_num_frames() / recording.get_sampling_frequency())
                }
            )
        )
    view = vv.UnitsTable(
        columns=columns,
        rows=rows,
        height=height
    )
    return view

if __name__ == '__main__':
    main()
