from typing import List

import pandas as pd  # type:ignore[import]
from docx.text.paragraph import Paragraph  # type:ignore[import]


def parse_middle_cell(
    paragraph: Paragraph,
    dataframe: pd.DataFrame,
    row_index: int,
    left_indent_position: int,
    tabstop_positions: List[int],
) -> None:
    """Parses a paragraph in the middle column and puts the information into the appropriate columns

    Args:
        paragraph (Paragraph): Current paragraph in the edifact struktur cell
        dataframe (pd.DataFrame): Contains all infos
        row_index (int): Current index of the DataFrame
        left_indent_position (int): Position of the left indent from the indicator middle cell
        tabstop_positions (List[int]): All tabstop positions of the indicator middle cell
    """

    splitted_text_at_tabs = paragraph.text.split("\t")

    # Qualifier / Code
    # left_indent_position is characteristic for Datenelemente
    if paragraph.paragraph_format.left_indent == left_indent_position:
        dataframe.at[row_index, "Codes und Qualifier"] += splitted_text_at_tabs.pop(0)
        column_indezes = list(range(4, 4 + len(tabstop_positions)))

    else:
        if splitted_text_at_tabs[0] == "":
            tabstop_positions = tabstop_positions[1:]
            del splitted_text_at_tabs[0]

        column_indezes = list(range(5, 5 + len(tabstop_positions)))

    # pylint: disable=protected-access
    tab_stops = paragraph.paragraph_format.tab_stops._pPr.tabs

    if tab_stops is not None:
        for tabstop in tab_stops:
            for tabstop_position, column_index in zip(tabstop_positions, column_indezes):
                if tabstop.pos == tabstop_position:
                    dataframe.iat[row_index, column_index] += splitted_text_at_tabs.pop(0)
    elif tab_stops is None and splitted_text_at_tabs:
        # in splitted_text_at_tabs list must be an entry
        dataframe.at[row_index, "Beschreibung"] += splitted_text_at_tabs.pop(0)
    elif tab_stops is None:
        pass
    # Could not figure out a scenario where this error could be raised.
    # else:
    #     raise NotImplementedError(f"Could not parse paragraph in middle cell with {paragraph.text}")
