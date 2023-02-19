"""
This module contains the enumeration for the colors of different row types
"""

from enum import StrEnum


class RowTypeColor(StrEnum):
    """
    Colors for each RowType in rgb hex notation
    """

    HEADER = "de324c"  #: e.g. "EDIFACT Struktur"
    SEGMENTNAME = "f4895f"  #: e.g. "Nachrichten-Kopfsegment"
    SEGMENTGRUPPE = "f8e16f"  #: e.g. "SG2"
    SEGMENT = "95cf92"  #: e.g. "    UNH" or "SG2  NAD"
    DATENELEMENT = "369acc"  #: e.g. "    UNH 0062"
    EMPTY = "9656a2"  #: e.g. ""
