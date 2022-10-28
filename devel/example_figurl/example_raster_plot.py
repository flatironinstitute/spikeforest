# 8/31/22
# https://figurl.org/f?v=gs://figurl/spikesortingview-8&d=sha1://f2d35eb108e7c1a5f6ae0ba196d61bb9b7a889df&label=Raster%20plot%20example

from typing import List
import numpy as np
import sortingview.views as vv
import spikeinterface as si
import spikeinterface.extractors as se
import kachery_cloud as kcl


def main():
    kcl.use_sandbox()
    recording, sorting = se.toy_example(num_units=12, duration=300, seed=0, num_segments=1)

    view = example_raster_plot(recording=recording, sorting=sorting)

    url = view.url(label='Raster plot example')
    print(url)

def example_raster_plot(*, recording: si.BaseRecording, sorting: si.BaseSorting, height=500):
    plot_items: List[vv.RasterPlotItem] = []
    for unit_id in sorting.get_unit_ids():
        spike_times_sec = np.array(sorting.get_unit_spike_train(segment_index=0, unit_id=unit_id)) / sorting.get_sampling_frequency()
        plot_items.append(
            vv.RasterPlotItem(
                unit_id=unit_id,
                spike_times_sec=spike_times_sec.astype(np.float32)
            )
        )

    view = vv.RasterPlot(
        start_time_sec=0,
        end_time_sec=recording.get_num_frames(segment_index=0) / recording.get_sampling_frequency(),
        plots=plot_items,
        height=height
    )
    return view

if __name__ == '__main__':
    main()
