<img src="https://github.com/jwellik/tsdatacruncher/blob/main/img/trex.png" width=1210 alt="TREX!" />

## Overview
TIMESERIES DATACRUNCHER (TSDATACRUNCHER OR TSDC) creates a simple configuration file, command line input parses, and time loop to process time-series data. Any processing code can be put in this loop to take advantage of the setup. The default package includes methods to filter seismic data, calculate RSAM, and store the results as miniseed files in the SDS filesystem. I hope, however, that this framework allows for any process to be subsituted into run_tsdatacruncher.py to crunch a timeseries however you see fit.

## Installation
Download or clone the git repository to your local machine. Navigate to where you downloaded the package, create the conda environment, and install the package with pip. Here are the steps on my machine:


```
$ conda create -n tsdc311 python=3.11 obspy bokeh psutil
$ cd /home/jwellik   # or your download directory
$ mv tsdatacruncher-main tsdatacruncher  # rename if downloaded from git
$ cd tsdatacruncher  # enter top level directory
$ pip install .      # install as a package 
```

## Configuration file
This program reads YAML configuration files.
Please see ./results/ffrsam/gareloi/gareloi.yaml for an example and documentation.


## Usage
Example usage:
```
$ cd /home/jwellik/tsdatacruncher  # enter top level directory
$ conda activate tsdc311  # activate conda environment
$ python ./run_tsdatacruncher.py --config ./results/ffrsam/gareloi/gareloi.yaml
```

This run will process the last 10 minutes of data from Gareloi Volcano, Alaska. Most of the output should go to the log file.

View the filesystem of miniseed data like this:
```
$ cd /home/jwellik/tsdatacruncher  # enter top level directory
$ cd ./results/SDS_ffrsam
$ ll */*/*/*/*
```

View the log file:
```
$ cd /home/jwellik/tsdatacruncher  # enter top level directory
$ cat ./results/ffrsam/gareloi/gareloi.log
```

An example to retrieve the RSAM data from the unfiltered (raw) seismic data.
```
$ python
> from obspy import UTCDateTime
> from obspy.clients.filesystem.sds import Client
> client = Client("./results/SDS_ffrsam/0000-0000")
> st = client.get_waveforms("AV", "GAEA", "*", "BHZ", UTCDateTime()-86400, UTCDateTime())
> print(st)
> st.plot()
```

To see an example of how to plot many stations using Bokeh, see ./scripts/simple_bokeh.html. This package does not include the required results to run this script, but the example should help you out.

## Running on cron
I run tsdatacruncher on a cronjob to update RSAM values every 10 minutes. The log file is also erased at the beginning of every day.
```
####################################################################################################
# ::: ffrsam - Wellik

*/10 * * * * /home/jwellik/PYTHON/PKG/tsdatacruncher/run_avoffrsam.sh
0 0 * * *    rm /VDAP-NAS/jwellik/DATA/AVO/SDS_ffrsam/avo.log
```
The contents of run_avoffrsam.sh look like this:
```
#!/bin/bash
# Script for running AVO ffrsam

sleep 60  # Pause for sixty seconds to make sure continuous waveform data are populated

# cd to correct path
TSDC=/home/jwellik/PYTHON/PKG/tsdatacruncher
OUTDIR=/VDAP-NAS/jwellik/DATA/AVO/SDS_ffrsam
cd $TSDC

# Run ffrsam
PYTHON=/home/jwellik/miniconda3/envs/seismology311/bin/python
$PYTHON $TSDC/run_tsdatacruncher.py --config $TSDC/results/ffrsam/avo/avo.yaml --id $TSDC/results/ffrsam/avo/avo.id --log-file $OUTDIR/avo.log
```
ID and LOG-FILE are also specified in the CONFIG file, but they are defined explicitly here too.

## StationID files
If you specify stationIDs (net.sta.loc.chan) as a file, the file can include other files. For example, avo.id can look like this:
```
@avo_1sta.id            # Include best station from all networks
@avo_edgecumbe.id
@avo_wrangell.id
@avo_spurr.id
@avo_redoubt.id
@avo_iliamna.id
```
And avo_1sta.id might (partially) look like this:
```
(base) jwellik@lila:~/PYTHON/PKG/tsdatacruncher$ cat $TSDC/results/ffrsam/avo/avo_1sta.id 
# Best station for each volcano
# (Good for quickly backing up data)
AV.EDCR..BHZ  # Edgecumbe
AV.WACK..BHZ  # Wrangell
AV.SPCP..BHZ  # Spurr
AV.RED..BHZ   # Redoubt
AV.ILW..SHZ   # Iliamna
```
After all stationID files are read, duplicate stations will be removed. Allowing nested stationID files makes it easier to target specific networks for back population.
