"""
This module defines an enum class representing the available export file formats for AhbExport.
"""

from enum import StrEnum


class AhbExportFileFormat(StrEnum):
    """
    Enum class representing the available export file formats for AhbExport.

    Attributes:
        FLATAHB (str): The FLATAHB file format.
        CSV (str): The CSV file format.
        XLSX (str): The XLSX file format.
    """

    FLATAHB = "flatahb"
    CSV = "csv"
    XLSX = "xlsx"
