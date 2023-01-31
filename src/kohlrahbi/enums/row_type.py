"""
This module contains the RowType enumeration.
"""

from enum import StrEnum, auto


class RowType(StrEnum):
    """
    All possible row types.
    The RowType is defined by the first cell in each row.
    Example content for each row type is documented at each enum member.
    """

    HEADER = auto()  #: e.g. "EDIFACT Struktur"
    SEGMENTNAME = auto()  #: e.g. "Nachrichten-Kopfsegment"
    SEGMENTGRUPPE = auto()  #: e.g. "SG2"
    SEGMENT = auto()  #: e.g. "    UNH" or "SG2  NAD"
    DATENELEMENT = auto()  #: e.g. "    UNH 0062"
    EMPTY = auto()  #: e.g. ""
