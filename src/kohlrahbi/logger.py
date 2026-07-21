"""
This module provides a logger instance for kohlrahbi.
"""

import logging

from rich.logging import RichHandler

logger = logging.getLogger("kohlrahbi")


def setup_logging(*, verbose: bool) -> None:
    """
    Configure logging level and handler.
    Default: WARNING (quiet, only progress bars visible).
    Verbose: DEBUG with rich-formatted log output.
    """
    level = logging.DEBUG if verbose else logging.WARNING
    logger.setLevel(level)
    logger.handlers.clear()
    if verbose:
        handler = RichHandler(rich_tracebacks=True, show_path=False)
        handler.setLevel(level)
        logger.addHandler(handler)
