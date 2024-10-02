"""
This module contains the class BedingungCell
"""

import re

import pandas as pd
from docx.table import _Cell
from pydantic import BaseModel, ConfigDict


class BedingungCell(BaseModel):
    """
    BedingungCell contains all information and a method
    to extract the Bedingungen of an AHB Bedingung cell.
    """

    table_cell: _Cell

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def parse(self, ahb_row_dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        Parses a cell in the Bedingung column and puts the information into the appropriate column of the dataframe.
        """
        bedingung = self.table_cell.text
        bedingung = self.beautify_bedingungen(bedingung)

        row_index = ahb_row_dataframe.index.max()
        ahb_row_dataframe.at[row_index, "Bedingung"] += bedingung
        return ahb_row_dataframe

    # pylint: disable=line-too-long
    @staticmethod
    def beautify_bedingungen(bedingung: str) -> str:
        """
        Beautifies the Bedingungen by removing the given line breaks and insert the line breaks at the correct places.

        Example input:
        [494] Das hier genannte Datum muss der Zeitpunkt sein, zu dem das Dokument erstellt wurde, oder ein Zeitpunkt, der davor liegt\n[931] Format: ZZZ = +00
        result:
        [494] Das hier genannte Datum muss der Zeitpunkt sein, zu dem das Dokument erstellt wurde, oder ein Zeitpunkt, der davor liegt
        [931] Format: ZZZ = +00
        """
        beautified_bedingung = bedingung.replace("\n", " ")

        matches = re.findall(r"\[\d+\]", beautified_bedingung)
        for match in matches[1:]:
            index = beautified_bedingung.find(match)
            beautified_bedingung = beautified_bedingung[:index].rstrip() + "\n" + beautified_bedingung[index:]

        return beautified_bedingung.lstrip()
