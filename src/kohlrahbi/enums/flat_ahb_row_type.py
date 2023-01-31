"""
This module contains the enumeration for FlatAHB row types.
"""

from enum import StrEnum, auto


class FlatAhbRowType(StrEnum):
    """
    All possible row types.
    The RowType is defined by the first cell in each row.
    Example content for each row type is documented at each enum member.
    """

    SEGMENTOPENINGLINE = auto()  #: e.g. "Nachrichten-Kopfsegment"
    # SECTIONNAME:
