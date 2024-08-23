"""
This module contains the class EdifactStrukturCell
"""

import re

import pandas as pd
from docx.table import _Cell
from pydantic import BaseModel, ConfigDict

_segment_group_pattern = re.compile(r"^SG\d+$")
_segment_pattern = re.compile(r"^[A-Z]{3}$")
_data_element_pattern = re.compile(r"^\d{4}$")
_segment_id_pattern = re.compile(r"^[A-Z\d]\d{4}$")


# pylint: disable=too-few-public-methods
class EdifactStrukturCell(BaseModel):
    """
    EdifactStrukturCell contains all information and a method
    to extract the segment name, segment group, segment and data element.
    """

    table_cell: _Cell
    edifact_struktur_cell_left_indent_position: int

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def parse(self, ahb_row_dataframe: pd.DataFrame) -> pd.DataFrame:
        """Parses a paragraph in the edifact struktur column and puts the information into the appropriate columns

        Args:
            table_cell (Cell): edifact struktur cell
            dataframe (pd.DataFrame): Contains all infos
            row_index (int): Current index of the DataFrame
            edifact_struktur_cell_left_indent_position (int): Position of the left indent from the indicator edifact
                struktur cell
        """

        joined_text = " ".join(p.text for p in self.table_cell.paragraphs)
        splitted_text_at_tabs = joined_text.split("\t")

        row_index = ahb_row_dataframe.index.max()

        for text in splitted_text_at_tabs:
            if _segment_group_pattern.match(text):
                ahb_row_dataframe.at[row_index, "Segment Gruppe"] = text
            elif _segment_pattern.match(text):
                ahb_row_dataframe.at[row_index, "Segment"] = text
            elif _data_element_pattern.match(text):
                ahb_row_dataframe.at[row_index, "Datenelement"] = text
            elif _segment_id_pattern.match(text):
                ahb_row_dataframe.at[row_index, "Segment ID"] = text
            elif text != "":
                ahb_row_dataframe.at[row_index, "Segment Gruppe"] = text
        return ahb_row_dataframe
