<img src="https://github.com/jwellik/tsdatacruncher/blob/main/img/trex.png" width=1510 alt="TREX!" />

## Overview
TIMESERIES DATACRUNCHER (TSDATACRUNCHER OR TSDC) creates a simple configuration file, command line input parses, and time loop to process time-series data. Any processing code can be put in this loop to take advantage of the setup. The default package included produces RSAM miniseed files from filtered seismic data.

## Installation
Download or clone the git repository to your local machine. Navigate to the 


```
$ conda create -n tsdc311 python=3.11 obspy bokeh psutil
$ cd /home/jwellik   # or your download directory
$ mv tsdatacruncher-main tsdatacruncher  # rename if downloaded from git
$ cd tsdatacruncher  # enter top level directory
$ pip install .      # install as a package
$ 
```

## Configuration file
This program reads YAML configuration files.
Please see ./results/ffrsam/gareloi/gareloi.yaml for an example and documentation.


## Usage
Example usage:
```
$ cd /home/jwellik/tsdatacruncher  # enter top level directory
$ conda activate tsdc311
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