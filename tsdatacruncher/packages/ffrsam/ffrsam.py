import os
from obspy import UTCDateTime, Stream, read

# https://www.seiscomp.de/seiscomp3/doc/applications/slarchive/SDS.html
"""
<SDSdir>/Year/NET/STA/CHAN.TYPE/NET.STA.LOC.CHAN.TYPE.YEAR.DAY
Definitions of fields
SDSdir 	:  arbitrary base directory
YEAR 	:  4 digit year
NET 	:  Network code/identifier, up to 8 characters, no spaces
STA 	:  Station code/identifier, up to 8 characters, no spaces
CHAN 	:  Channel code/identifier, up to 8 characters, no spaces
TYPE 	:  1 characters indicating the data type, recommended types are:
	        'D' - Waveform data
	        'E' - Detection data
	        'L' - Log data
	        'T' - Timing data
	        'C' - Calibration data
	        'R' - Response data
	        'O' - Opaque data
LOC 	:  Location identifier, up to 8 characters, no spaces
DAY 	:  3 digit day of year, padded with zeros
The dots, '.', in the file names must always be present regardless if neighboring fields are empty.

Additional data type flags may be used for extended structure definition.
"""
# <SDSdir>/Year/NET/STA/CHAN.TYPE/NET.STA.LOC.CHAN.TYPE.YEAR.DAY
ffrsam_syntax = "{freq_str}/{year}/{net}/{sta}/{cha}.{dtype}/{net}.{sta}.{loc}.{cha}.{dtype}.{year}.{jday:03d}"
freq_none = 0

def rsam(tr, freq=None, period=60, taper_percentage=0.01, fill_value=0):
    """Computes RSAM on a single Trace; returns another Trace object with correct sample rate"""

    import numpy as np
    from obspy import Stream, Trace

    tmp = Stream(tr.copy().split())  # splits Trace (possibly masked) into Stream of multiple Traces
    for m in range(len(tmp)):
        tmp[m].data = np.where(tmp[m].data == -2 ** 31, 0, tmp[m].data)  # remove Winston gaps, if they exist
    tmp.detrend("demean")
    tmp.taper(max_percentage=taper_percentage)
    tmp.merge(fill_value=fill_value)
    if freq:
        tmp.filter("bandpass", freqmin=freq[0], freqmax=freq[1])

    rsam = []
    for st_window in tmp.slide(window_length=period, step=period):
        y = [np.sqrt(np.mean(np.square(tr.data))) for tr in st_window]
        rsam.append(y[0])
    rsam = np.array(rsam)

    stats = tmp[0].stats
    stats["delta"] = period
    stats["npts"] = len(rsam)
    a = Trace(data=rsam, header=stats)
    return a

def freq2str(freq):
    if freq is None:
        f1 = 0
        f2 = 0
    else:
        f1 = int(freq[0] * 100)
        f2 = int(freq[1] * 100)
    return "{:04d}-{:04d}".format(f1, f2)

def archive_ffrsam(st, freq=None, period=60, taper_percentage=0.01, fill_value=0,
                   archive="./", syntax=ffrsam_syntax,
                   logger=None):

    st = st.merge()  # combine by station id

    # loop over streams available
    for tr in st:
        if logger:
            logger.info(f"--Processing station: {tr.id}")

        # Loop over frequency bands
        for f in freq:
            if logger:
                logger.info(f"---Processing frequency band: {f}")

            freq_str = freq2str(f)

            # Define outfile and make directories, if necessary
            sds_syntax = syntax.format(freq_str=freq_str, year=tr.stats.starttime.year,
                                    net=tr.stats.network, sta=tr.stats.station, loc=tr.stats.location,
                                    cha=tr.stats.channel,
                                    dtype='D', jday=tr.stats.starttime.julday)
            fullpath = os.path.join(archive, os.path.dirname(sds_syntax))  # final directory in the SDS filestructure
            outputfilename = os.path.join(archive, sds_syntax)
            os.makedirs(fullpath, exist_ok=True)

            ffrsam_st = Stream()

            # try to load the existing miniseed file - append to existing Stream ffrsam_st
            try:
                existing_stream = read(outputfilename)
                ffrsam_st += existing_stream
                if logger:
                    logger.info(f"----File loaded: {outputfilename}")
            except Exception as e:
                pass

            # compute ffrsam - try
            try:
                ffrsam_st += rsam(tr, freq=f, period=period, taper_percentage=taper_percentage,
                                  fill_value=fill_value)
                if logger:
                    logger.info(f"----RSAM computed.")
            except Exception as e:
                if logger:
                    logger.info(f"----RSAM NOT computed: {e}")

            # merge ffrsam_st
            ffrsam_st.merge(method=1, interpolation_samples=0)

            # Write file
            try:
                ffrsam_st.split().write(outputfilename, format='MSEED')
                if logger:
                    logger.info(f"----File saved: {outputfilename}")
            except Exception as e:
                if logger:
                    logger.info(f"----File failed to save ({outputfilename})\n{e}")

def get_ffrsam(sds, station_id, t1, t2, period=60, freq=None):
    from obspy.clients.filesystem.sds import Client

    t1 = UTCDateTime(t1)
    t2 = UTCDateTime(t2)

    data = dict()

    for f in freq:
        fstr = freq2str(f)
        # freqsds = os.path.join(sds, str(period), fstr)
        freqsds = os.path.join(sds, fstr)
        client = Client(freqsds)

        st = Stream()
        for id  in station_id:
            net, sta, loc, cha = id.split(".")
            st += client.get_waveforms(net, sta, loc, cha, t1, t2)

        data[fstr] = st

    return data
