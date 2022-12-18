import attrs
import pandas as pd
from docx.table import _Cell  # type:ignore[import]
from typing import List, Optional

from maus.reader.flat_ahb_reader import FlatAhbCsvReader

index_of_codes_and_qualifier_column = 3


@attrs.define(auto_attribs=True, kw_only=True)
class BodyCell:
    table_cell: _Cell
    left_indent_position: int
    indicator_tabstop_positions: List[int]

    def parse(self, ahb_row_dataframe: pd.DataFrame) -> pd.DataFrame:
        """Parses a paragraph in the middle column and puts the information into the appropriate columns

        Args:
            paragraph (Paragraph): Current paragraph in the edifact struktur cell
            dataframe (pd.DataFrame): Contains all infos
            left_indent_position (int): Position of the left indent from the indicator middle cell
            tabstop_positions (List[int]): All tabstop positions of the indicator middle cell
        """

        if self.table_cell.paragraphs[0].text == "":
            return ahb_row_dataframe

        is_first_iteration = True

        for paragraph in self.table_cell.paragraphs:

            row_index = ahb_row_dataframe.index.max()
            paragraph.text = paragraph.text.replace("\xa0", "")
            splitted_text_at_tabs = paragraph.text.split("\t")

            if paragraph.paragraph_format.left_indent == self.left_indent_position:
                # code or qualifier

                if FlatAhbCsvReader._is_value_pool_entry(candidate=splitted_text_at_tabs[0]):
                    # code entry
                    if not is_first_iteration:
                        # a new code and it is not the first. So we add a new row in dataframe and increase the row_index
                        ahb_row_dataframe.loc[ahb_row_dataframe.index.max() + 1, :] = ""
                        row_index = row_index + 1

                    # ahb_row_dataframe.iat[row_index, index_of_codes_and_qualifier_column] += splitted_text_at_tabs.pop(
                    #     0
                    # )
                    # column_indezes = list(range(4, 4 + len(self.indicator_tabstop_positions)))

                else:
                    # qualifier entry
                    pass

                ahb_row_dataframe.iat[row_index, index_of_codes_and_qualifier_column] += splitted_text_at_tabs.pop(0)
                column_indezes = list(range(4, 4 + len(self.indicator_tabstop_positions)))

            # cases:
            # - left indent AND code
            # - left indent AND qualifier
            # - NOT left indent

            else:
                if splitted_text_at_tabs[0] == "":
                    del splitted_text_at_tabs[0]
                column_indezes: list[int] = list(range(4, 4 + len(self.indicator_tabstop_positions)))

            paragraph_contains_tabstops: bool = self.has_paragraph_tabstops(paragraph=paragraph)

            if paragraph_contains_tabstops:
                tab_stops_in_current_paragraph = [
                    tabstop.pos for tabstop in paragraph.paragraph_format.tab_stops._pPr.tabs
                ]

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

            # else:
            #     # qualifier entry
            #     pass

            # if self.does_paragraph_contain_qualifier(
            #     paragraph=paragraph, left_indent_position=self.left_indent_position
            # ):
            #     pass

            # if self.does_paragraph_contain_code(paragraph=paragraph, left_indent_position=self.left_indent_position):

            #     if not is_first_iteration:
            #         # a new code and it is not the first. So we add a new row in dataframe and increase the row_index
            #         ahb_row_dataframe.loc[ahb_row_dataframe.index.max() + 1, :] = ""
            #         row_index = row_index + 1

            #     ahb_row_dataframe.iat[row_index, index_of_codes_and_qualifier_column] += splitted_text_at_tabs.pop(0)
            #     column_indezes = list(range(4, 4 + len(self.indicator_tabstop_positions)))

            # else:
            #     if splitted_text_at_tabs[0] == "":
            #         del splitted_text_at_tabs[0]
            #     column_indezes = list(range(4, 4 + len(self.indicator_tabstop_positions)))

            # paragraph_contains_tabstops: bool = self.has_paragraph_tabstops(paragraph=paragraph)

            # if paragraph_contains_tabstops:
            #     tab_stops_in_current_paragraph = [
            #         tabstop.pos for tabstop in paragraph.paragraph_format.tab_stops._pPr.tabs
            #     ]

            #     for tabstop in tab_stops_in_current_paragraph:
            #         for indicator_tabstop_position, column_index in zip(
            #             self.indicator_tabstop_positions, column_indezes
            #         ):
            #             if tabstop == indicator_tabstop_position:
            #                 ahb_row_dataframe.iat[row_index, column_index] += splitted_text_at_tabs.pop(0)

            # elif not paragraph_contains_tabstops and splitted_text_at_tabs:
            #     # in splitted_text_at_tabs list must be an entry
            #     ahb_row_dataframe.at[row_index, "Beschreibung"] += splitted_text_at_tabs.pop(0)
            # elif not paragraph_contains_tabstops:
            #     pass
            # else:
            #     raise NotImplementedError(f"Could not parse paragraph in middle cell with {paragraph.text}")

            # # recognize that the first loop is over
            # is_first_iteration = False

        return ahb_row_dataframe

    def does_paragraph_contain_code(self, paragraph, left_indent_position) -> bool:
        return paragraph.paragraph_format.left_indent == left_indent_position and paragraph.runs[0].bold

    def does_paragraph_contain_qualifier(self, paragraph, left_indent_position):
        """
        Checks if the given paragraph contains a qualifier, e.g. `Dokumentennummer`
        Cause codes are always bold, we check if the text is not bold.
        """
        return paragraph.paragraph_format.left_indent == left_indent_position and paragraph.runs[0].bold is None

    def has_paragraph_tabstops(self, paragraph) -> bool:
        """
        Checks if the given paragraph contains tabstops
        """
        return paragraph.paragraph_format.tab_stops._pPr.tabs is not None
