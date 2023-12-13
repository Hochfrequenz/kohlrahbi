"""
This module contains the UnfoldedAhbTableMetaData class.
"""

from attrs import define


# pylint: disable=too-few-public-methods
@define(auto_attribs=True, kw_only=True)
class UnfoldedAhbTableMetaData:
    """
    This class represents the metadata of an unfolded AHB table.
    """

    pruefidentifikator: str
    beschreibung: str | None
    kommunikation_von: str | None
