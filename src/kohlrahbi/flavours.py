"""
This module contains the enum for the different kohlrahbi flavours.
"""

from enum import Enum


class Flavour(str, Enum):
    """
    Enum for the different kohlrahbi flavours.
    """

    PRUEFI = "PRUEFI"
    CHANGEHISTORY = "CHANGEHISTORY"
    CONDITIONS = "CONDITIONS"
