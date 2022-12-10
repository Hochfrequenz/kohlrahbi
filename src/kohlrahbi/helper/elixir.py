"""
This module provides a class to collect information which of need for all parsing functions
"""

from typing import List

import pandas as pd  # type:ignore[import]
from attrs import define
from docx.table import Table  # type:ignore[import]
from docx.text.paragraph import Paragraph  # type:ignore[import]

from kohlrahbi.enums import RowType


def get_tabstop_positions(paragraph: Paragraph) -> List[int]:
    """Find all tabstop positions in a given paragraph.

    Mainly the tabstop positions of cells from the middle column are determined

    Args:
        paragraph (Paragraph):

    Returns:
        List[int]: All tabstop positions in the given paragraph
    """
    tabstop_positions: List[int] = []
    # pylint: disable=protected-access
    for tabstop in paragraph.paragraph_format.tab_stops._pPr.tabs:
        tabstop_positions.append(tabstop.pos)
    return tabstop_positions


# pylint: disable=too-few-public-methods
@define
class Elixir:
    """
    helper class to store all values to extract the AHB and the final AHB as dataframe
    """

    pruefidentifikatoren: List[str] = []
    soul: pd.DataFrame = pd.DataFrame()
    edifact_struktur_left_indent_position: int = 0
    middle_cell_left_indent_position: int = 0
    tabstop_positions: List[int] = []
    last_two_row_types: List[RowType] = []
    current_df_row_index: int = 0

    # why this classmethod?
    # to decouple the data structure of Elixir from the input data
    # more background can be found on https://www.attrs.org/en/stable/init.html#initialization
    @classmethod
    def from_table(cls, docx_table: Table) -> "Elixir":
        """Prepare DataFrame for a new table with new Prüfidentifikatoren

        Args:
            item (Union[Paragraph, Table]): A paragraph or table from the docx
        """
        header_cells = [cell.text for cell in docx_table.row_cells(0)]
        look_up_term = "Prüfidentifikator"
        cutter_index = header_cells[-1].find(look_up_term) + 1
        # +1 cause of \t after Prüfidentifikator
        pruefidentifikatoren = header_cells[-1][cutter_index + len(look_up_term) :].split("\t")

        # edifact struktur cell
        edifact_struktur_indicator_paragraph = docx_table.cell(row_idx=4, col_idx=0).paragraphs[0]
        edifact_struktur_left_indent_position = edifact_struktur_indicator_paragraph.paragraph_format.left_indent

        # middle cell
        middle_cell_indicator_paragraph = docx_table.cell(row_idx=4, col_idx=1).paragraphs[0]
        middle_cell_left_indent_position = middle_cell_indicator_paragraph.paragraph_format.left_indent
        tabstop_positions = get_tabstop_positions(middle_cell_indicator_paragraph)

        base_column_names: List = [
            "Segment Gruppe",
            "Segment",
            "Datenelement",
            "Codes und Qualifier",
            "Beschreibung",
        ]
        columns = base_column_names + pruefidentifikatoren + ["Bedingung"]

        # Initialize help variables
        last_two_row_types: List = [RowType.EMPTY, RowType.EMPTY]
        current_df_row_index: int = 0

        return cls(
            pruefidentifikatoren=pruefidentifikatoren,
            soul=pd.DataFrame(
                columns=columns,
                dtype="str",
            ),
            edifact_struktur_left_indent_position=edifact_struktur_left_indent_position,
            middle_cell_left_indent_position=middle_cell_left_indent_position,
            tabstop_positions=tabstop_positions,
            last_two_row_types=last_two_row_types,
            current_df_row_index=current_df_row_index,
        )
