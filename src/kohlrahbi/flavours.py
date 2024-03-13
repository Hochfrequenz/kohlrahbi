from enum import Enum


class Flavour(str, Enum):
    """
    Enum for the different kohlrahbi flavours.
    """

    PRUEFI = "PRUEFI"
    CHANGEHISTORY = "CHANGEHISTORY"
    CONDITIONS = "CONDITIONS"
