import attrs
import pandas as pd
from docx.table import _Cell  # type:ignore[import]
from typing import List, Optional


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

            if self.does_paragraph_contain_qualifier_or_code(
                paragraph=paragraph, left_indent_position=self.left_indent_position
            ):

                if not is_first_iteration:
                    # a new code and it is not the first. So we add a new row in dataframe and increase the row_index
                    ahb_row_dataframe.loc[ahb_row_dataframe.index.max() + 1, :] = ""
                    row_index = row_index + 1

                ahb_row_dataframe["Codes und Qualifier"] += splitted_text_at_tabs.pop(0)
                column_indezes = list(range(4, 4 + len(self.indicator_tabstop_positions)))

            else:
                if splitted_text_at_tabs[0] == "":
                    del splitted_text_at_tabs[0]
                column_indezes = list(range(4, 4 + len(self.indicator_tabstop_positions)))

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

        return ahb_row_dataframe

    def does_paragraph_contain_qualifier_or_code(self, paragraph, left_indent_position) -> bool:
        return paragraph.paragraph_format.left_indent == left_indent_position

    def has_paragraph_tabstops(self, paragraph) -> bool:
        """
        Checks if the given paragraph contains tabstops
        """
        return paragraph.paragraph_format.tab_stops._pPr.tabs is not None
