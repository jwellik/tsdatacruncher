

def welcome(logger=None):
    """
    Display welcome message with system information and runtime environment.

    Args:
        logger: A logging instance to use. If None, information is only returned.
    """
    import os
    import sys
    import platform
    import psutil
    import getpass
    import datetime

    # Get current time and format it
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # System information
    os_info = f"{platform.system()} {platform.release()} ({platform.version()})"
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    # Memory information
    mem = psutil.virtual_memory()
    total_memory_gb = mem.total / (1024 ** 3)
    available_memory_gb = mem.available / (1024 ** 3)

    # User and directory information
    current_user = getpass.getuser()
    current_dir = os.getcwd()

    # Create the welcome message
    welcome_msg = f"""
{'=' * 80}
TIMESERIES DATA PROCESSING TOOL
{'=' * 80}

Runtime Information:
  - Date/Time    : {current_time}
  - Working Dir  : {current_dir}
  - User         : {current_user}

System Information:
  - OS           : {os_info}
  - Python       : {python_version}
  - Memory       : {available_memory_gb:.2f} GB available / {total_memory_gb:.2f} GB total
  - CPU Cores    : {psutil.cpu_count(logical=False)} physical, {psutil.cpu_count()} logical

{'=' * 80}
"""
    # Log the welcome message if logger is provided
    if logger:
        logger.info(welcome_msg)
