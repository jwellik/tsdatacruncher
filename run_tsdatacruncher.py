""""
TO DO
# TODO RSAM Period
# [x] Clean up input.py -> get Claude help --> clean up how defaults are handled
# [x] clean_data (Same data type)
# TODO RSAMStream object (.plot(), .get_freq())
# [x] station_id.txt: ignore blank lines, ignore comments, allow @inlcude statements
# TODO Command line output  --verbose (?)
# TODO More config stuff in welcome message
# TODO Try to install locally with pip

# FRONTEND
# TODO Easy - Old Bokeh page
"""


import pandas as pd
from obspy import UTCDateTime

import tsdatacruncher.utils.input as tsinput
import tsdatacruncher.utils.tsdata as tsdata
from tsdatacruncher.utils import msg
from tsdatacruncher.packages.ffrsam import ffrsam as ffrsam_utils
from tsdatacruncher.utils.logs import setup_logger


def main(client, station_ids, t1, t2, freq=[None], tload=1440.0, tproc=10.0, tstep=10.0,
         verbose=True, log_file=None, log_level="INFO", config={}):
    """Main processing function."""

    logger = setup_logger("tsdatacruncher", log_level, log_file, console_output=verbose)

    msg.welcome(logger=logger)

    # Create an ObsPy client
    client = tsdata.create_client(client)

    # Download and process data in a single try/except block per time range
    # - time load defines the *maximum* amount of time to load, but tA and tB can be less if the amount of requested
    #   data is less than tload
    for start_load in pd.date_range(start=t1.date.isoformat(), end=t2.date.isoformat(), freq=pd.Timedelta(minutes=tload)):
        tA = UTCDateTime(start_load)  # Earliest *possible* time to load data (UTCDateTime)
        tA = max(tA, t1)  # Earliest load time - Don't load anything earlier than original t1
        tB = min(t2, tA + tload * 60)  # Latest load time - Don't load anything later than original t2
        logger.info(f"Downloading {tA} to {tB}")

        # Get the waveform data (includes a try/except statement)
        st = tsdata.get_waveforms(client, station_ids, tA, tB, logger=logger)

        try:

            if len(st) > 0:
                for st_proc in st.slide(window_length=tproc * 60, step=tstep * 60):
                    tproc1 = min([tmp.stats.starttime for tmp in st_proc])
                    tproc2 = max([tmp.stats.endtime for tmp in st_proc])
                    logger.info(f"- Processing {tproc1} to {tproc2}")

                    # APPLY PROCESSING - YOUR CODE HERE!
                    ffrsam_utils.archive_ffrsam(st_proc, freq=freq, archive=config['archive'], logger=logger)
            else:
                logger.info(f"- No streams to porcess.")

        except Exception as e:
            logger.info(f"-- Error during processing: {e}")
            continue  # Continue with the next time range

    logger.info("Done.")


if __name__ == "__main__":

    # Parses config file and command line arguments
    config = tsinput.load_config_and_cli()

    # Run main function
    main(config["client"],
         config["id"],
         config["t1"],
         config["t2"],
         freq = config["freq"],
         tload = config["tload"],
         tproc = config["tproc"],
         tstep = config["tstep"],
         verbose = config["no-console-log"],
         log_file = config["log_file"],
         log_level=config["log_level"],
         config = config,
    )