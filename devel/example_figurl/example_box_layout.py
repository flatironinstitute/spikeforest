# 10/12/22
# https://figurl.org/f?v=gs://figurl/spikesortingview-10&d=sha1://3ee2df1ea84baa665ffe9f6ea7ee4cafe1d730c4&label=Box%20layout%20example

import sortingview.views as vv
import spikeinterface.extractors as se
import kachery_cloud as kcl
import spikeinterface as si
from example_autocorrelograms import example_autocorrelograms
from example_cross_correlograms import example_cross_correlograms
from example_raster_plot import example_raster_plot
from example_average_waveforms import example_average_waveforms
from example_units_table import example_units_table


def main():
    kcl.use_sandbox()
    R, S = se.toy_example(num_units=12, duration=300, seed=0, num_segments=1)

    view = example_box_layout(recording=R, sorting=S)

    url = view.url(
        label='Box layout example'
    )
    print(url)

def example_box_layout(recording: si.BaseRecording, sorting: si.BaseSorting, height=800):
    R = recording
    S = sorting
    v_units_table = example_units_table(recording=R, sorting=S)
    v_raster_plot = example_raster_plot(recording=R, sorting=S)
    v_autocorrelograms = example_autocorrelograms(sorting=S)
    v_average_waveforms = example_average_waveforms(recording=R, sorting=S)
    v_cross_correlograms = example_cross_correlograms(sorting=S, hide_unit_selector=True)

    view = vv.Box(
        height=height,
        direction='vertical',
        show_titles=True,
        items=[
            vv.LayoutItem(
                vv.Box(
                    direction='horizontal',
                    show_titles=True,
                    items=[
                        vv.LayoutItem(
                            v_units_table,
                            stretch=1,
                            title='Units'
                        ),
                        vv.LayoutItem(
                            v_raster_plot,
                            stretch=2,
                            title='Raster'
                        )
                    ]
                ),
                title="top"
            ),
            vv.LayoutItem(
                vv.Box(
                    direction='horizontal',
                    items=[
                        vv.LayoutItem(
                            v_autocorrelograms,
                            min_size=300,
                            max_size=350
                        ),
                        vv.LayoutItem(
                            v_average_waveforms
                        ),
                        vv.LayoutItem(
                            v_cross_correlograms
                        )
                    ]
                ),
                title="bottom"
            )
        ]
    )

    return view

if __name__ == '__main__':
    main()
