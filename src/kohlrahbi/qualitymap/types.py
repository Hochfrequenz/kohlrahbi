"""
This module contains some types used in the quality map subpackage.
"""

from enum import StrEnum


class OutputFormat(StrEnum):
    """
    Enum for the output format of the scraped AHB documents.
    """

    CSV = "csv"
    EXCEL = "excel"
    C_SHARP_EXTRACT = "csharp-extract"
