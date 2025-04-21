# tsdatacruncher/utils/logging_utils.py
import logging
import os
from typing import Optional

# Dictionary to store loggers by name
loggers = {}


def setup_logger(
        logger_name: str,
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        console_output: bool = True
) -> logging.Logger:
    """
    Set up and return a logger with the specified configuration.

    Args:
        logger_name: Unique name for the logger
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file; if None, no file logging
        console_output: Whether to output logs to console

    Returns:
        Configured logger instance
    """
    # If logger already exists with this name, return it
    if logger_name in loggers:
        return loggers[logger_name]

    # Create new logger
    logger = logging.getLogger(logger_name)

    # Set logging level
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)

    # Define formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Clear any existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()

    # Add file handler if log file is specified
    if log_file:
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Add console handler if specified
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Store logger in dictionary
    loggers[logger_name] = logger

    return logger


def get_logger(logger_name: str) -> logging.Logger:
    """
    Get an existing logger by name, or create a basic one if it doesn't exist.

    Args:
        logger_name: Name of the logger to retrieve

    Returns:
        Logger instance
    """
    if logger_name in loggers:
        return loggers[logger_name]
    else:
        # Create a basic logger if one doesn't exist yet
        return setup_logger(logger_name)