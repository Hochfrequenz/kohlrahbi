"""
This module contains the UnfoldedAhbTableMetaData class.
"""

from pydantic import BaseModel


# pylint: disable=too-few-public-methods
class UnfoldedAhbTableMetaData(BaseModel):
    """
    This class represents the metadata of an unfolded AHB table.
    """

    pruefidentifikator: str
    beschreibung: str | None
    kommunikation_von: str | None
