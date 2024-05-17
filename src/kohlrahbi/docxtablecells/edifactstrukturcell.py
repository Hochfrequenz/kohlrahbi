"""
This module contains the class EdifactStrukturCell
"""

import re

import pandas as pd
from docx.table import _Cell
from pydantic import BaseModel, ConfigDict

_segment_group_pattern = re.compile(r"^SG\d+$")
_segment_pattern = re.compile(r"^[A-Z]{3}$")


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
        tab_count = joined_text.count("\t")

        row_index = ahb_row_dataframe.index.max()

        # Check if the line starts on the far left
        if (
            self.table_cell.paragraphs[0].paragraph_format.left_indent
            != self.edifact_struktur_cell_left_indent_position
        ):
            if tab_count == 2:
                ahb_row_dataframe.at[row_index, "Segment Gruppe"] = splitted_text_at_tabs[0]
                ahb_row_dataframe.at[row_index, "Segment"] = splitted_text_at_tabs[1]
                ahb_row_dataframe.at[row_index, "Datenelement"] = splitted_text_at_tabs[2]
            elif tab_count == 1:
                ahb_row_dataframe.at[row_index, "Segment Gruppe"] = splitted_text_at_tabs[0]
                ahb_row_dataframe.at[row_index, "Segment"] = splitted_text_at_tabs[1]
            elif tab_count == 0 and joined_text.strip() != "":
                is_segment_gruppe: bool = bool(self.table_cell.paragraphs[0].runs[0].bold) and bool(
                    _segment_group_pattern.match(joined_text)
                )

                is_segment = bool(_segment_pattern.match(joined_text))
                if is_segment_gruppe:
                    # Segmentgruppe: SG8
                    ahb_row_dataframe.at[row_index, "Segment Gruppe"] = splitted_text_at_tabs[0]
                elif is_segment:
                    ahb_row_dataframe.at[row_index, "Segment"] = splitted_text_at_tabs[0]
                else:
                    # Segmentname: Referenzen auf die ID der\nTranche
                    _sg_text = ahb_row_dataframe.at[row_index, "Segment Gruppe"]
                    if _sg_text == "":
                        # Referenzen auf die ID der
                        ahb_row_dataframe.at[row_index, "Segment Gruppe"] = splitted_text_at_tabs[0]
                    else:
                        # Tranche
                        ahb_row_dataframe.at[row_index, "Segment Gruppe"] += " " + splitted_text_at_tabs[0]

        # Now the text should start in middle of the EDIFACT Struktur column
        else:
            if tab_count == 1:
                # Example: "UNH\t0062"
                ahb_row_dataframe.at[row_index, "Segment"] = splitted_text_at_tabs[0]
                ahb_row_dataframe.at[row_index, "Datenelement"] = splitted_text_at_tabs[1]

            elif tab_count == 0:
                # Example: "UNH"
                ahb_row_dataframe.at[row_index, "Segment"] = splitted_text_at_tabs[0]

        return ahb_row_dataframe
