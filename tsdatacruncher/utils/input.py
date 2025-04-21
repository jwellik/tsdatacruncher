#!/usr/bin/env python3
import argparse
import os
import sys
import yaml
from typing import Dict, Any, List

import pandas as pd
import datetime
import time
from obspy import UTCDateTime


def deep_update(original, update):
    """
    Recursively update a dictionary without overwriting entire nested dicts.
    """
    for key, value in update.items():
        if key in original and isinstance(original[key], dict) and isinstance(value, dict):
            deep_update(original[key], value)
        else:
            original[key] = value


def parse_ids(id_input, verbose=True):
    """Parse station IDs from a list, file, or comma-separated string.

    Features:
    - Removes comments (anything after "#")
    - Processes nested files referenced with "@/file/path"
    - Ensures unique IDs in the output
    """

    print("Parsing station ids...")

    # Function to process a file and handle nested includes with relative paths
    def process_file(filepath, processed_files=None):
        if processed_files is None:
            processed_files = set()

        # Convert to absolute path to avoid duplicates in processed_files
        abs_filepath = os.path.abspath(filepath)

        # Avoid infinite recursion
        if abs_filepath in processed_files:
            return []

        print("Parsing station id file: {}".format(abs_filepath))

        processed_files.add(abs_filepath)
        result = []

        # Get the directory of the current file for resolving relative paths
        file_dir = os.path.dirname(abs_filepath)

        with open(filepath, 'r') as f:
            for line in f:
                # Strip whitespace
                line = line.strip()
                if not line:
                    continue

                # Remove comments
                if '#' in line:
                    line = line.split('#', 1)[0].strip()
                    if not line:
                        continue

                # Handle nested file inclusion
                if line.startswith('@'):
                    nested_file = line[1:]  # Remove the '@' prefix

                    # Resolve path relative to the current file's directory
                    nested_file_path = os.path.join(file_dir, nested_file)

                    if os.path.isfile(nested_file_path):
                        result.extend(process_file(nested_file_path, processed_files))
                else:
                    result.append(line)

        return result

    # If already a list, just return it (after ensuring uniqueness)
    if isinstance(id_input, list):
        return list(dict.fromkeys(id_input))  # Preserve order while removing duplicates

    # Process file
    if os.path.isfile(id_input):
        ids = process_file(id_input)
    else:
        # Treat as comma-separated string
        ids = [item.strip() for item in id_input.split(',') if item.strip()]

    # Ensure uniqueness while preserving order
    unique_ids = list(dict.fromkeys(ids))
    print('\n'.join(unique_ids))
    return unique_ids

def parse_freq(freq):
    if isinstance(freq, str):
        # If freq is a comma-separated string, convert it to a list
        freq = freq.split(',')

    if isinstance(freq, list):
        # If freq is a list, process each element
        for i in range(len(freq)):
            if freq[i] == "None":
                freq[i] = None
            elif isinstance(freq[i], str):
                # Split the string by "-" and convert to a list of floats
                parts = freq[i].split('-')
                freq[i] = [float(part) for part in parts]

    return freq


def verify_t1_t2(t1=None, t2=None, default_minutes=10):
    """Returns a time range given any combination of t1 and t2 (or neither)"""

    def dtfloor(dt, minutes=default_minutes):
        """Round down a datetime to the nearest n minutes."""
        return dt - datetime.timedelta(
            minutes=dt.minute % minutes,
            seconds=dt.second,
            microseconds=dt.microsecond
        )

    def dtceil(dt, minutes=default_minutes):
        """Round up a datetime to the nearest n minutes."""
        floored = dtfloor(dt, minutes)
        if floored < dt:
            return floored + datetime.timedelta(minutes=minutes)
        return floored

    now = datetime.datetime.utcnow()

    t1 = None if t1=="None" else t1
    t2 = None if t2=="None" else t2

    if t1 is None and t2 is None:  # no inputs provided
        t2 = dtceil(now) - datetime.timedelta(minutes=default_minutes)
        t1 = t2 - datetime.timedelta(minutes=default_minutes)
    elif t1 is None:  # Only t2 provided
        t2 = dtceil(UTCDateTime(t2).datetime)
        t1 = t2 - datetime.timedelta(minutes=default_minutes)
    elif t2 is None:  # Only t1 provided
        t1 = dtfloor(UTCDateTime(t1).datetime)
        t2 = t1 + datetime.timedelta(minutes=default_minutes)
    else:  # Both t1 and t2 provided
        t1 = dtfloor(UTCDateTime(t1).datetime)
        t2 = dtceil(UTCDateTime(t2).datetime)

    # Switch t1 and t2 if t1 is greater (later)
    if t1 > t2:
        tmp = t1
        t1 = t2
        t2 = tmp
        print("NOTE: t2 must be greater than t1. Switching time arguments: {}-{}".format(t1, t2))

    return UTCDateTime(t1), UTCDateTime(t2)


def parse_time_delta(value):
    """Convert a value that could be a Timedelta string, int, or float to a float value in minutes"""

    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        try:
            # Try to parse as pandas Timedelta
            td = pd.Timedelta(value)
            return td.total_seconds() / 60  # Convert to minutes
        except ValueError:
            # If it's not a valid Timedelta string, try direct conversion
            try:
                return float(value)
            except ValueError:
                print(f"Warning: Could not parse time value '{value}' - using default")
                return None

    return None  # Is this line necessary; should only get here if not str, int, float


def load_config_and_cli():

    # Parse command line arguments
    args = parse_cli()

    # Convert namespace to dictionary
    cli_args = {k: v for k, v in vars(args).items() if v is not None and k != 'config'}

    # Parse configuration - override config with cli, parse variables
    config = parse_all_input(args.config, cli_args)

    return config


def parse_cli():
    """
    Parse command line arguments
    """

    # Create argument parser
    parser = argparse.ArgumentParser(description='Time Series Data Cruncher [Roar!]')

    # Parse first positional argument (config file)
    parser.add_argument('--config', default='config.yaml', help='Path to configuration file (YAML)')

    # Add options - Data Selection (client, t1, t2, station_id list)
    parser.add_argument('--client', type=str,  # type=create_client (?)
                        help='DataSource (parsed as ObsPy Client)')
    parser.add_argument('--t1', type=str,
                        help='Start time in format YYYY-MM-DDTHH:MM:SS')
    parser.add_argument('--t2', type=str,
                        help='End time in format YYYY-MM-DDTHH:MM:SS')
    parser.add_argument('--id', type=str,
                        help='List of Station IDs (comma separated or file path with one ID per line)')

    # Add options - Processing options
    parser.add_argument('--freq', type=str,
                        help='Frequency bands (e.g., "None,1-5,1-10,2.5-5" (Use None for no filter')
    # - add option for rsam period (1') hard-coded default right now

    # Add options - Processing Timedeltas
    parser.add_argument('--tload', type=str,
                        help='Maximum time to download in one chunk (days or pandas Timedelta string)')
    parser.add_argument('--tproc', type=str,
                        help='Processing time window length (minutes or pandas Timedelta string)')
    parser.add_argument('--tstep', type=str,
                        help='Time between processing chunks (minutes or pandas Timedelta string)')
    parser.add_argument('--latency', type=str,
                        help='Amount of time (in seconds) to pause before executing code (useful in crontab situations)')

    # App options - Overwrite and logging
    parser.add_argument('--log-file', type=str,
                        help='Path to log file (if not specified, logs only to console)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Logging level')
    parser.add_argument(
        "--no-console-log",
        action="store_true",
        help="Disable logging to console"
    )
    parser.add_argument('--archive', type=str,
                        help='Results output directory (SDS Archive)')
    # parser.add_argument('--overwrite', type=bool, help='Whether to overwrite existing output files')

    return parser.parse_args()


def parse_all_input(config_file: str, cli_args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reads config file.
    Fills in missing values with default dict.
    Overrides config/default values with cli.
    Parses and verifies input.
    """

    # Default configuration
    config = {
        "t1": None,
        "t2": None,
        "id": [],  # Default empty list of stations

        "freq": [None, [0.1, 1], [1, 3], [1, 5], [1, 10], [5, 10], [10, 15], [15, 20]],

        "tload": "1D",
        "tproc": "10min",
        "tstep": "10min",
        "latency": 0,

        "archive": "./results/SDS_ffrsam",

        "overwrite": False,
        "no-console-log": False,
        "log_level": "INFO",
        "log_file": "./tsdatacruncher.log",
    }

    # Load configuration from file if it exists
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                file_config = yaml.safe_load(f)

            # Update default config with file config (deep update)
            if file_config:
                deep_update(config, file_config)
        except Exception as e:
            print(f"Error loading config file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Config file {config_file} not found, using default values")

    # Update with CLI arguments (if provided and not None)
    if cli_args.get('client'):
        config['client'] = cli_args['client']
    if cli_args.get('t1'):
        config['t1'] = cli_args['t1']
    if cli_args.get('t2'):
        config['t2'] = cli_args['t2']
    if cli_args.get('id'):
        config['id'] = cli_args['id']

    if cli_args.get('freq'):
        config['freq'] = cli_args['freq']

    if cli_args.get('tload'):
        config['tload'] = cli_args['tload']
    if cli_args.get('tproc'):
        config['tproc'] = cli_args['tproc']
    if cli_args.get('tstep'):
        config['tstep'] = cli_args['tstep']
    if cli_args.get('latency'):
        config['latency'] = cli_args['latency']

    if cli_args.get('overwrite'):
        config['overwrite'] = cli_args['overwrite']
    if cli_args.get('archive'):
        config['archive'] = cli_args['archive']
    if cli_args.get('log_file'):
        config['log_file'] = cli_args['log_file']
    if cli_args.get('log_level'):
        config['log_level'] = cli_args['log_level']
    if cli_args.get('no-consolue-log'):
        config['no-console-log'] = cli_args['no-console-log']

    # Validate and parse all inputs
    config["latency"] = int(config["latency"])
    if config["latency"] > 0:
        print("Waiting for data. Pausing program for {} seconds.".format(config["latency"]))
        time.sleep(config["latency"])

    config["tload"] = parse_time_delta(config["tload"])
    config["tproc"] = parse_time_delta(config["tproc"])
    config["tstep"] = parse_time_delta(config["tstep"])
    config["t1"], config["t2"] = verify_t1_t2(config["t1"], config["t2"], config["tproc"])

    config["id"] = parse_ids(config["id"])

    config["freq"] = parse_freq(config["freq"])

    return config


def config2yaml(config):
    # Convert UTCDateTime objects to ISO format strings
    for key, value in config.items():
        if isinstance(value, UTCDateTime):
            config[key] = value.isoformat()
        elif isinstance(value, list):
            config[key] = [v.isoformat() if isinstance(v, UTCDateTime) else v for v in value]

    print(yaml.dump(config))
