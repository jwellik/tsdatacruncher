from obspy import Stream
from obspy.clients.earthworm import Client as EWClient
from obspy.clients.fdsn import Client as FDSNClient
from obspy.clients.fdsn.header import URL_MAPPINGS as FDSN_URL_MAPPINGS
from obspy.clients.seedlink import Client as SeedLinkClient
from obspy.clients.filesystem.sds import Client as SDSClient

from numpy import dtype

def create_client(datasource):

    fdsn_named_clients = [key for key in sorted(FDSN_URL_MAPPINGS.keys())]
    # print(fdsn_named_clients)
    # print(datasource)
    # print(True) if datasource in fdsn_named_clients else print(False)

    # First check if it's a named client
    if datasource in fdsn_named_clients:
        server = FDSN_URL_MAPPINGS[datasource]
        return FDSNClient(server)

    # Handle URLs and other formats
    if '://' not in datasource:
        import os.path

        # Expand user directory if present (e.g., ~/data)
        expanded_path = os.path.expanduser(datasource)

        # Check if this looks like a filesystem path
        if os.path.isabs(expanded_path) or os.path.exists(expanded_path):
            # Assume it's an SDS path
            return SDSClient(expanded_path)

        # Simple host without protocol
        elif '.' not in datasource:
            return FDSNClient(datasource)
        else:
            return EWClient(datasource, datasource)
    else:
        # Extract protocol and server part
        protocol, server_str = datasource.split('://', 1)

        # Handle FDSN protocols
        if protocol in ['fdsn', 'http', 'fdsnws']:
            return FDSNClient(server_str)

        # Handle waveserver protocols
        elif protocol in ['wws', 'waveserver']:
            if ':' in server_str:
                server, port = server_str.split(':', 1)
            else:
                server = server_str
                port = '16022'
            return EWClient(server, int(port))

        # Handle seedlink protocol
        elif protocol == 'seedlink':
            if ':' in server_str:
                server, port = server_str.split(':', 1)
            else:
                server = server_str
                port = '18000'
            return SeedLinkClient(server, port=int(port), timeout=1)

        # Handle SDS protocol
        elif protocol == 'sds':
            return SDSClient(server_str)

        # Unrecognized protocol
        else:
            raise ValueError(f'Unrecognized protocol in server: {datasource}')

def get_waveforms(client, station_id_list, t1, t2, logger=None):

    st = Stream()
    for id in station_id_list:
        try:
            net, sta, loc, cha = id.split(".")  # id needs to be expanded to separate arguments
            st += client.get_waveforms(net, sta, loc, cha, t1, t2)
        except Exception as e:
            logger.info(f"-- No data: {id}")
            continue

    for tr in st:
        # deal with error when sub-traces have different dtypes
        if tr.data.dtype.name != 'int32':
            tr.data = tr.data.astype('int32')
        if tr.data.dtype != dtype('int32'):
            tr.data = tr.data.astype('int32')
        # deal with rare error when sub-traces have different sample rates
        if tr.stats.sampling_rate != round(tr.stats.sampling_rate):
            tr.stats.sampling_rate = round(tr.stats.sampling_rate)

    return st
