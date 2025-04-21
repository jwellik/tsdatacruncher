import sys, os, time
from obspy.core import UTCDateTime
from tsdatacruncher.packages.ffrsam import ffrsam as ffrsam_utils

ffrsam_sds = "/VDAP-NAS/jwellik/DATA/AVO/SDS_ffrsam"
output_filepath = "./avo_rsam.html"

# determine start and end times
ltt1 = UTCDateTime("2025-01-01")  # start of long-term plot
t1 = UTCDateTime("2025-04-08")  # start of zoomed-in plot
t2 = UTCDateTime("2025-04-15")

networks = [
    {
        "name": "Gareloi",
        "id": ["AV.GANO..BHZ", "AV.GANE..BHZ", "AV.GAKI..BHZ", "AV.GAEA..BHZ", "AV.GALA..BHZ", "AV.GASW..BHZ"]
    },
    {
        "name": "Spurr",
        "id": ["AV.SPCP..BHZ", "AV.SPCL..BHZ", "AV.SPBG..BHZ", "AV.SPCN..BHZ", "AV.N20K..BHZ"]
    },
]

rsam_period = 10  # (minutes) interpolate 1' RSAM archive to this sample rate


def main():

    print("Create bokeh page for RSAM")

    import pandas as pd

    from bokeh.layouts import column
    from bokeh.models import RangeTool, Legend, Div, Range1d
    from bokeh.plotting import figure, output_file, save
    from bokeh.palettes import Colorblind8

    PLOTW=1000
    PLOTH=300

    FIGURES = []
    FIGURES.append(Div(text='<h1>{0}</h1>'.format("AVO RSAM"), width=PLOTW))

    # Loop through each page in html_configuration
    for net in networks:

        data = ffrsam_utils.get_ffrsam(ffrsam_sds, net["id"], ltt1, t2, freq=[None, [1, 5]])

        stLT = data["0100-0500"]
        stLT = stLT.merge(fill_value=0.0).interpolate((1 / (60 * rsam_period)))  # what does interpolate do? sum, average, st-else?
        st = stLT.copy()
        st = st.slice(t1, t2)


        TITLE = "{} ({} minute RSAM)".format(net["name"], rsam_period)

        # Set up main figure
        p = figure(title=TITLE, height=PLOTH, width=PLOTW,
                   tools="save,xpan,yzoom_in,yzoom_out,box_zoom,reset", toolbar_location="right",
                   # toolbar_options=dict(logo=None),
                   # x_axis_type="datetime", x_axis_location="below",
                   background_fill_color="#efefef",
                   x_range=(pd.Timestamp(t1.datetime), pd.Timestamp(t2.datetime)),
                   y_range=(0, 10000)
                   )
        p.add_layout(Legend(orientation="horizontal"), 'above')

        # Set up long-term dataselect window
        select = figure(height=75, width=PLOTW,
                        y_range=(0, 5000),
                        x_axis_type="datetime", x_axis_location="below", y_axis_type=None,
                        x_range=(pd.Timestamp(ltt1.datetime), pd.Timestamp(t2.datetime)),
                        tools="", toolbar_location=None, background_fill_color="#efefef"
        )

        # Plot data to main panel
        i = 0
        for tr in stLT:
            clr = Colorblind8[i]

            # times = [t.datetime for t in tr.times("utcdatetime").data[~tr.times("utcdatetime").mask]]
            # data  = tr.data.data[~tr.data.mask] * rsam_period
            times = [t.datetime for t in tr.times("utcdatetime")]
            data = tr.data * rsam_period
            # select.scatter(times, data, color=clr, line_color="black", alpha=0.9, size=10)
            # select.circle(times, data, color=clr, line_color="black", alpha=0.9, size=10)
            select.line(times, data, color=clr, line_width=2)

            tmp = tr.slice(ltt1, t2)
            # times = [t.datetime for t in tmp.times("utcdatetime").data[~tmp.times("utcdatetime").mask]]
            # data  = tmp.data.data[~tmp.data.mask] * rsam_period
            times = [t.datetime for t in tr.times("utcdatetime")]
            data = tr.data * rsam_period
            # p.scatter(times, data, color=clr, line_color="black", alpha=0.9, size=10, legend_label=tr.id)
            p.line(times, data, color=clr, line_width=2, legend_label=tr.id)
            i += 1

        # ax[0].set_title("{} (1-5 Hz)".format(net["name"]))
        # ax[0].set_xlim(t1.matplotlib_date, t2.matplotlib_date)
        # ax[0].set_ylim(bottom=0)
        # _set_xaxis_obspy_dates(ax[0])

        p.yaxis.axis_label = 'RSAM'
        # p.x_range = Range1d(mysqldf.iloc[-7*24*6]["Time"], mysqldf.iloc[-1]["Time"])  # Last 7 days
        p.x_range = Range1d(t1.datetime, t2.datetime)  # Last 7 days

        range_tool = RangeTool(x_range=p.x_range)
        range_tool.overlay.fill_color = "yellow"
        range_tool.overlay.fill_alpha = 0.2

        select.ygrid.grid_line_color = None
        select.add_tools(range_tool)
        # select.toolbar.active_multi = range_tool

        p.legend.click_policy = "hide"

        FIGURES.append(p)
        FIGURES.append(select)
        FIGURES.append(Div(text="", width=PLOTW))

    # Add message at the bottom that prints UTC timestamp of last exection
    last_execution_msg = "Last execution: {}".format(UTCDateTime.utcnow())
    FIGURES.append(Div(text=last_execution_msg, width=PLOTW))

    # output = column(select, p)
    output = column(FIGURES)
    output_filename = output_filepath
    output_file(output_filename, title="AVO RSAM")
    save(output)
    print("Saving file: {}".format(output_filename))


if __name__ == "__main__":
    main()
