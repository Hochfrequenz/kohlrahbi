"""
This module provides a logger instance for kohlrahbi
"""

import logging.config
from pathlib import Path

# Construct the path to the configuration file
logger_config_file: Path = Path(__file__).with_suffix(".ini")

logging.config.fileConfig(logger_config_file)
logger = logging.getLogger("kohlrahbi")
