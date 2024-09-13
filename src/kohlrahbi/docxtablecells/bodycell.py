"""
This module contains the class BodyCell
"""

import pandas as pd
from docx.table import _Cell
from docx.text.paragraph import Paragraph
from pydantic import BaseModel, ConfigDict

from kohlrahbi.models.flat_ahb_reader import FlatAhbCsvReader
from kohlrahbi.table_header import get_tabstop_positions

INDEX_OF_CODES_AND_QUALIFIER_COLUMN = 4


class BodyCell(BaseModel):
    """
    BodyCell contains all information and a method
    to extract dataelement/qualifier, the name of the dataelement
    as well as the conditions for each Prüfidentifikator.
    """

    table_cell: _Cell
    left_indent_position: int
    indicator_tabstop_positions: list[int]

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # I see why pylint is not happy about this many branches, but at the moment I have no clue how to avoid them.
    # pylint: disable=too-many-branches
    def parse(self, ahb_row_dataframe: pd.DataFrame) -> pd.DataFrame:
        """Parses a paragraph in the middle column and puts the information into the appropriate columns

        Args:
            paragraph (Paragraph): Current paragraph in the edifact struktur cell
            dataframe (pd.DataFrame): Contains all infos
            left_indent_position (int): Position of the left indent from the indicator middle cell
            tabstop_positions (list[int]): All tabstop positions of the indicator middle cell
        """

        def handle_code_or_qualifier_entry(
            splitted_text_at_tabs: list[str], row_index: int, is_first_iteration: bool
        ) -> int:
            if (  # pylint: disable=protected-access
                FlatAhbCsvReader._is_value_pool_entry(candidate=splitted_text_at_tabs[0])
                and len(splitted_text_at_tabs) >= 2
            ):
                if not is_first_iteration:
                    ahb_row_dataframe.loc[ahb_row_dataframe.index.max() + 1, :] = ""
                    row_index += 1
            ahb_row_dataframe.iat[row_index, INDEX_OF_CODES_AND_QUALIFIER_COLUMN] += splitted_text_at_tabs.pop(0)
            return row_index

        def handle_tab_stops(
            paragraph: Paragraph, splitted_text_at_tabs: list[str], row_index: int, column_indezes: list[int]
        ) -> None:
            tab_stops_in_current_paragraph = get_tabstop_positions(paragraph=paragraph)
            for tabstop in tab_stops_in_current_paragraph:
                for indicator_tabstop_position, column_index in zip(self.indicator_tabstop_positions, column_indezes):
                    if len(tab_stops_in_current_paragraph) == 1:
                        if indicator_tabstop_position in (tabstop, paragraph.paragraph_format.left_indent):
                            ahb_row_dataframe.iat[row_index, column_index] += splitted_text_at_tabs.pop(0)
                    else:
                        if tabstop == indicator_tabstop_position:
                            ahb_row_dataframe.iat[row_index, column_index] += splitted_text_at_tabs.pop(0)

        def handle_no_tab_stops(splitted_text_at_tabs: list[str], row_index: int) -> None:
            if splitted_text_at_tabs:
                ahb_row_dataframe.at[row_index, "Beschreibung"] += splitted_text_at_tabs.pop(0)

        cell_is_empty = self.table_cell.paragraphs[0].text == ""
        if cell_is_empty:
            return ahb_row_dataframe

        is_first_iteration = True

        for paragraph in self.table_cell.paragraphs:
            row_index = ahb_row_dataframe.index.max()
            paragraph.text = paragraph.text.replace("\xa0", "")
            splitted_text_at_tabs = paragraph.text.split("\t")

            if paragraph.paragraph_format.left_indent == self.left_indent_position:
                row_index = handle_code_or_qualifier_entry(splitted_text_at_tabs, row_index, is_first_iteration)
                column_indezes = list(
                    range(
                        INDEX_OF_CODES_AND_QUALIFIER_COLUMN + 1,
                        INDEX_OF_CODES_AND_QUALIFIER_COLUMN + 1 + len(self.indicator_tabstop_positions),
                    )
                )
            else:
                if splitted_text_at_tabs[0] == "":
                    del splitted_text_at_tabs[0]
                column_indezes = list(
                    range(
                        INDEX_OF_CODES_AND_QUALIFIER_COLUMN + 1,
                        INDEX_OF_CODES_AND_QUALIFIER_COLUMN + 1 + len(self.indicator_tabstop_positions),
                    )
                )

            if self.has_paragraph_tabstops(paragraph=paragraph):
                handle_tab_stops(paragraph, splitted_text_at_tabs, row_index, column_indezes)
            else:
                handle_no_tab_stops(splitted_text_at_tabs, row_index)

            is_first_iteration = False

        return ahb_row_dataframe

    def has_paragraph_tabstops(self, paragraph: Paragraph) -> bool:
        """
        Checks if the given paragraph contains tabstops
        """
        tab_stops = list(paragraph.paragraph_format.tab_stops)
        return any(tab_stops)
