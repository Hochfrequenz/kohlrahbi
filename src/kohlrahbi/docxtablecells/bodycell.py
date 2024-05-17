"""
This module contains the class BodyCell
"""

import pandas as pd
from docx.table import _Cell
from docx.text.paragraph import Paragraph
from maus.reader.flat_ahb_reader import FlatAhbCsvReader
from pydantic import BaseModel, ConfigDict

from kohlrahbi.table_header import get_tabstop_positions

INDEX_OF_CODES_AND_QUALIFIER_COLUMN = 3


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
            tabstop_positions (List[int]): All tabstop positions of the indicator middle cell
        """

        cell_is_empty = self.table_cell.paragraphs[0].text == ""

        if cell_is_empty:
            return ahb_row_dataframe

        is_first_iteration = True

        for paragraph in self.table_cell.paragraphs:
            row_index = ahb_row_dataframe.index.max()
            paragraph.text = paragraph.text.replace("\xa0", "")
            splitted_text_at_tabs = paragraph.text.split("\t")

            if paragraph.paragraph_format.left_indent == self.left_indent_position:
                # code or qualifier

                if (
                    FlatAhbCsvReader._is_value_pool_entry(  # pylint: disable=protected-access
                        candidate=splitted_text_at_tabs[0]
                    )
                    and len(splitted_text_at_tabs) >= 2
                    # the second check makes sure, that we parse ORDER\nS correct e.g. in 17001
                ):
                    # code entry
                    if not is_first_iteration:
                        # a new code and it is not the first.
                        # So we add a new row in dataframe and increase the row_index
                        ahb_row_dataframe.loc[ahb_row_dataframe.index.max() + 1, :] = ""
                        row_index = row_index + 1

                else:
                    # qualifier entry
                    pass

                ahb_row_dataframe.iat[row_index, INDEX_OF_CODES_AND_QUALIFIER_COLUMN] += splitted_text_at_tabs.pop(0)
                column_indezes = list(range(4, 4 + len(self.indicator_tabstop_positions)))

            else:
                if splitted_text_at_tabs[0] == "":
                    del splitted_text_at_tabs[0]
                column_indezes = list(range(4, 4 + len(self.indicator_tabstop_positions)))

            paragraph_contains_tabstops: bool = self.has_paragraph_tabstops(paragraph=paragraph)

            if paragraph_contains_tabstops:
                tab_stops_in_current_paragraph = get_tabstop_positions(paragraph=paragraph)

                for tabstop in tab_stops_in_current_paragraph:
                    for indicator_tabstop_position, column_index in zip(
                        self.indicator_tabstop_positions, column_indezes
                    ):
                        if tabstop == indicator_tabstop_position:
                            ahb_row_dataframe.iat[row_index, column_index] += splitted_text_at_tabs.pop(0)

            elif not paragraph_contains_tabstops and splitted_text_at_tabs:
                # in splitted_text_at_tabs list must be an entry
                ahb_row_dataframe.at[row_index, "Beschreibung"] += splitted_text_at_tabs.pop(0)
            elif not paragraph_contains_tabstops:
                pass
            else:
                raise NotImplementedError(f"Could not parse paragraph in middle cell with {paragraph.text}")

            # recognize that the first loop is over
            is_first_iteration = False

        return ahb_row_dataframe

    def has_paragraph_tabstops(self, paragraph: Paragraph) -> bool:
        """
        Checks if the given paragraph contains tabstops
        """
        tab_stops = list(paragraph.paragraph_format.tab_stops)
        return any(tab_stops)
