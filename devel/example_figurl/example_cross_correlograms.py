# 8/31/22
# https://figurl.org/f?v=gs://figurl/spikesortingview-8&d=sha1://a72e243cf44f94ecfd2fd9d828157e9ad05adce1&label=Cross%20correlograms%20example

from typing import List
import sortingview.views as vv
import spikeinterface as si
import spikeinterface.extractors as se
import kachery_cloud as kcl
from helpers.compute_correlogram_data import compute_correlogram_data


def main():
    kcl.use_sandbox()
    _, sorting = se.toy_example(num_units=12, duration=300, seed=0, num_segments=1)

    view = example_cross_correlograms(sorting=sorting)
    url = view.url(label='Cross correlograms example')
    print(url)

def example_cross_correlograms(*, sorting: si.BaseSorting, hide_unit_selector: bool=False, height=500):
    cross_correlogram_items: List[vv.CrossCorrelogramItem] = []
    for unit_id1 in sorting.get_unit_ids():
        for unit_id2 in sorting.get_unit_ids():
            if unit_id1 != unit_id2 + 1:
                a = compute_correlogram_data(sorting=sorting, unit_id1=unit_id1, unit_id2=unit_id2, window_size_msec=50, bin_size_msec=1)
                bin_edges_sec = a['bin_edges_sec']
                bin_counts = a['bin_counts']
                cross_correlogram_items.append(
                    vv.CrossCorrelogramItem(
                        unit_id1 = unit_id1,
                        unit_id2 = unit_id2,
                        bin_edges_sec = bin_edges_sec,
                        bin_counts = bin_counts
                    )
                )

    view = vv.CrossCorrelograms(
        cross_correlograms=cross_correlogram_items,
        hide_unit_selector=hide_unit_selector,
        height=height
    )
    return view

if __name__ == '__main__':
    main()
